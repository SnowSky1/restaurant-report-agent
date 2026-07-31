"""FastAPI surface for the restaurant analysis workflow."""

from __future__ import annotations

import asyncio
import logging
import re
import secrets
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from dataclasses import asdict, is_dataclass
from time import monotonic
from typing import Any, Literal
from uuid import uuid4

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator, model_validator

from config.settings import settings
from main import run_analysis
from nodes.revenue_simulation import SUPPORTED_STORE_TYPES
from services.llm import krill_fallback_configured
from services.site_comparison import (
    DEFAULT_WEIGHTS,
    assess_evidence_quality,
    compare_candidate_sites,
)
from tools.amap_tools import AmapTools

logger = logging.getLogger(__name__)
logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
# httpx logs full query strings at INFO; Amap puts its credential in the query.
# Keep transport logs above INFO so application logs never disclose API keys.
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
_analysis_semaphore = asyncio.Semaphore(max(1, settings.max_concurrent_analyses))
_rate_events: dict[str, deque[float]] = defaultdict(deque)
_rate_lock = asyncio.Lock()


@asynccontextmanager
async def lifespan(application: FastAPI):
    application.state.amap_http = httpx.AsyncClient(
        base_url="https://restapi.amap.com",
        timeout=settings.request_timeout_seconds,
        limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
    )
    application.state.last_analysis = None
    try:
        yield
    finally:
        await application.state.amap_http.aclose()


app = FastAPI(
    title="Restaurant Report Agent API",
    version="0.0.0",
    description="LangGraph + Amap + CompeteAI-inspired restaurant analysis",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    supplied_request_id = request.headers.get("X-Request-ID", "")
    request_id = (
        supplied_request_id
        if re.fullmatch(r"[A-Za-z0-9._-]{1,64}", supplied_request_id)
        else uuid4().hex
    )
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    return response


StoreType = Literal[
    "餐厅",
    "咖啡店",
    "奶茶店",
    "火锅店",
    "烧烤店",
    "快餐店",
    "面馆",
    "西餐厅",
    "日料店",
    "韩餐厅",
    "川菜馆",
    "粤菜馆",
    "甜品店",
    "面包店",
]


def _normalize_location(value: str | None) -> str | None:
    if not value:
        return None
    try:
        longitude, latitude = (float(part.strip()) for part in value.split(",", 1))
    except (TypeError, ValueError):
        raise ValueError("location 必须是“经度,纬度”") from None
    if not -180 <= longitude <= 180 or not -90 <= latitude <= 90:
        raise ValueError("location 坐标超出有效范围")
    return f"{longitude:.6f},{latitude:.6f}"


class AnalyzeRequest(BaseModel):
    store_name: str = Field(min_length=1, max_length=100)
    store_address: str = Field(min_length=2, max_length=300)
    store_type: StoreType = "餐厅"
    analysis_radius: int = Field(default=1000, ge=100, le=5000)
    location: str | None = None
    deep_analysis: bool = True
    use_llm: bool = True
    avg_ticket: float | None = Field(default=None, gt=0, le=5000)
    seat_count: int | None = Field(default=None, gt=0, le=2000)
    daily_fixed_cost: float | None = Field(default=None, gt=0, le=1_000_000)
    variable_cost_rate: float | None = Field(default=None, gt=0, lt=1)

    @field_validator("location")
    @classmethod
    def validate_location(cls, value: str | None) -> str | None:
        return _normalize_location(value)


class AnalyzeResponse(BaseModel):
    success: bool
    status: Literal["complete", "degraded"]
    message: str
    report_markdown: str
    data: dict[str, Any]


class CandidateSite(BaseModel):
    candidate_id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,32}$")
    name: str = Field(min_length=1, max_length=100)
    address: str = Field(min_length=2, max_length=300)
    location: str | None = None

    @field_validator("location")
    @classmethod
    def validate_location(cls, value: str | None) -> str | None:
        return _normalize_location(value)


class ComparisonWeights(BaseModel):
    demand_potential: float = Field(default=DEFAULT_WEIGHTS["demand_potential"], ge=0, le=1)
    accessibility: float = Field(default=DEFAULT_WEIGHTS["accessibility"], ge=0, le=1)
    competitive_headroom: float = Field(default=DEFAULT_WEIGHTS["competitive_headroom"], ge=0, le=1)
    profitability: float = Field(default=DEFAULT_WEIGHTS["profitability"], ge=0, le=1)
    evidence_quality: float = Field(default=DEFAULT_WEIGHTS["evidence_quality"], ge=0, le=1)

    @model_validator(mode="after")
    def require_positive_total(self) -> ComparisonWeights:
        if sum(self.model_dump().values()) <= 0:
            raise ValueError("至少一个比较权重必须大于 0")
        return self


class CompareRequest(BaseModel):
    candidates: list[CandidateSite] = Field(min_length=2, max_length=5)
    store_type: StoreType = "餐厅"
    analysis_radius: int = Field(default=1000, ge=100, le=5000)
    avg_ticket: float | None = Field(default=None, gt=0, le=5000)
    seat_count: int | None = Field(default=None, gt=0, le=2000)
    daily_fixed_cost: float | None = Field(default=None, gt=0, le=1_000_000)
    variable_cost_rate: float | None = Field(default=None, gt=0, lt=1)
    weights: ComparisonWeights = Field(default_factory=ComparisonWeights)
    require_viable: bool = True
    minimum_evidence_score: float = Field(default=50, ge=0, le=100)

    @model_validator(mode="after")
    def require_unique_candidates(self) -> CompareRequest:
        ids = [candidate.candidate_id for candidate in self.candidates]
        if len(ids) != len(set(ids)):
            raise ValueError("candidate_id 必须唯一")
        return self


class CompareResponse(BaseModel):
    success: bool
    status: Literal["complete", "degraded"]
    message: str
    data: dict[str, Any]


@app.get("/")
def root() -> dict[str, Any]:
    return {
        "name": "Restaurant Report Agent API",
        "version": app.version,
        "docs": "/docs",
        "health": "/api/health",
    }


@app.get("/api/health")
def health_check() -> dict[str, Any]:
    llm_config = settings.get_llm_config()
    krill_ready = settings.enable_krill_fallback and krill_fallback_configured()
    return {
        "status": "ok",
        "version": app.version,
        "data_mode": settings.data_mode,
        "amap_transport": settings.amap_transport,
        "amap_configured": bool(settings.amap_maps_api_key),
        "llm_provider": settings.llm_provider,
        "llm_model": llm_config.get("model"),
        "llm_configured": bool(llm_config.get("api_key")) or krill_ready,
        "llm_primary_configured": bool(llm_config.get("api_key")),
        "krill_fallback_enabled": settings.enable_krill_fallback,
        "krill_fallback_configured": krill_ready,
        "supported_store_types": list(SUPPORTED_STORE_TYPES),
        "authentication_required": bool(settings.api_access_token),
        "last_analysis": getattr(app.state, "last_analysis", None),
    }


async def require_access_token(
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None),
) -> None:
    expected = settings.api_access_token
    if not expected:
        return
    bearer = authorization.removeprefix("Bearer ").strip() if authorization else ""
    supplied = x_api_key or bearer
    if not supplied or not secrets.compare_digest(supplied, expected):
        raise HTTPException(status_code=401, detail="缺少或无效的 API 访问令牌")


async def _enforce_rate_limit(request: Request, *, cost: int = 1) -> None:
    limit = max(1, settings.api_rate_limit_per_minute)
    key = request.client.host if request.client else "unknown"
    now = monotonic()
    async with _rate_lock:
        events = _rate_events[key]
        while events and events[0] <= now - 60:
            events.popleft()
        if len(events) + cost > limit:
            raise HTTPException(status_code=429, detail="分析请求过于频繁，请稍后重试")
        events.extend([now] * cost)


def _amap_tools(request: Request) -> AmapTools:
    return AmapTools(
        settings.amap_mcp_url,
        settings.amap_maps_api_key,
        data_mode=settings.data_mode,
        transport=settings.amap_transport,
        timeout=settings.request_timeout_seconds,
        http_client=getattr(request.app.state, "amap_http", None),
        cache_ttl_seconds=settings.amap_cache_ttl_seconds,
        max_retries=settings.amap_max_retries,
        max_parallel_requests=settings.amap_max_parallel_requests,
    )


def _analysis_is_degraded(data: dict[str, Any], state: dict[str, Any]) -> bool:
    provenance = data.get("provenance") or {}
    return (
        bool(data.get("errors"))
        or bool(provenance.get("used_mock_data"))
        or any(
            not state.get(key)
            for key in ("traffic", "weather", "poi_analysis", "revenue_simulation")
        )
    )


@app.get("/api/ready")
async def readiness_check(
    request: Request,
    probe: bool = Query(default=False, description="执行一次真实地图探测；会消耗少量上游配额"),
    _auth: None = Depends(require_access_token),
) -> dict[str, Any]:
    configured = settings.data_mode == "mock" or bool(settings.amap_maps_api_key)
    result: dict[str, Any] = {
        "status": "ready" if configured else "not_ready",
        "configuration_ready": configured,
        "probe_executed": False,
        "last_analysis": getattr(request.app.state, "last_analysis", None),
    }
    if not probe or not configured:
        return result

    tools = _amap_tools(request)
    try:
        response = await tools.geocode("北京市东城区天安门")
        has_location = bool(response.get("geocodes"))
        provenance = tools.provenance()
        real_reachable = has_location and (
            settings.data_mode == "mock" or bool(provenance.get("used_real_data"))
        )
        result.update(
            {
                "status": "ready" if real_reachable else "degraded",
                "probe_executed": True,
                "amap_reachable": real_reachable,
                "provenance": provenance,
            }
        )
        return result
    except Exception as error:
        logger.warning("readiness_probe_failed error=%s", type(error).__name__)
        result.update({"status": "not_ready", "probe_executed": True, "amap_reachable": False})
        return result
    finally:
        await tools.close()


@app.get("/api/geocode")
async def geocode_address(
    request: Request,
    address: str = Query(min_length=2, max_length=300),
    _auth: None = Depends(require_access_token),
) -> dict[str, Any]:
    tools = _amap_tools(request)
    try:
        result = await tools.geocode(address)
        geocodes = result.get("geocodes") or []
        if not geocodes:
            raise HTTPException(status_code=404, detail="未找到该地址")
        return {
            "success": True,
            "location": geocodes[0],
            "provenance": tools.provenance(),
        }
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(
            status_code=502, detail=f"地址解析失败：{type(error).__name__}"
        ) from error
    finally:
        await tools.close()


@app.get("/api/reverse-geocode")
async def reverse_geocode(
    request: Request,
    location: str = Query(pattern=r"^-?\d+(?:\.\d+)?,-?\d+(?:\.\d+)?$"),
    _auth: None = Depends(require_access_token),
) -> dict[str, Any]:
    tools = _amap_tools(request)
    try:
        result = await tools.reverse_geocode(location)
        regeocode = result.get("regeocode") or {}
        if not regeocode:
            raise HTTPException(status_code=404, detail="未找到该坐标")
        return {
            "success": True,
            "location": regeocode,
            "provenance": tools.provenance(),
        }
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(
            status_code=502, detail=f"逆地理编码失败：{type(error).__name__}"
        ) from error
    finally:
        await tools.close()


@app.post("/api/analyze", response_model=AnalyzeResponse)
async def create_analysis(
    payload: AnalyzeRequest,
    request: Request,
    _auth: None = Depends(require_access_token),
) -> AnalyzeResponse:
    await _enforce_rate_limit(request)
    tools = _amap_tools(request)
    try:
        async with _analysis_semaphore:
            report, state = await asyncio.wait_for(
                run_analysis(
                    store_name=payload.store_name,
                    store_address=payload.store_address,
                    store_type=payload.store_type,
                    analysis_radius=payload.analysis_radius,
                    use_llm=payload.use_llm,
                    deep_analysis=payload.deep_analysis,
                    location=payload.location,
                    avg_ticket=payload.avg_ticket,
                    seat_count=payload.seat_count,
                    daily_fixed_cost=payload.daily_fixed_cost,
                    variable_cost_rate=payload.variable_cost_rate,
                    save_report=settings.save_api_reports,
                    display_report=False,
                    amap_tools=tools,
                ),
                timeout=settings.analysis_timeout_seconds,
            )
    except asyncio.TimeoutError as error:
        raise HTTPException(
            status_code=504,
            detail=f"分析超过 {settings.analysis_timeout_seconds:g} 秒，请重试或暂时关闭 LLM 深度解释",
        ) from error
    except Exception as error:
        logger.exception(
            "api_analysis_failed request_id=%s store_type=%s",
            request.state.request_id,
            payload.store_type,
        )
        raise HTTPException(status_code=500, detail=f"分析失败：{type(error).__name__}") from error
    finally:
        await tools.close()

    if not report or not state:
        raise HTTPException(status_code=502, detail="工作流没有生成报告，请检查配置和后端日志")
    if not state.get("location"):
        raise HTTPException(
            status_code=502,
            detail="位置解析失败，无法生成可信分析；请检查地址或改用精确坐标",
        )

    data = _build_response_data(state, report)
    data["request_id"] = request.state.request_id
    provenance = data.get("provenance") or {}
    degraded = _analysis_is_degraded(data, state)
    status: Literal["complete", "degraded"] = "degraded" if degraded else "complete"
    data["status"] = status
    provenance["status"] = status
    message = (
        "分析完成，但存在缺失、错误或模拟回退；请查看数据状态后再使用结论"
        if degraded
        else "分析完成；所需地图与周边数据均来自真实接口"
    )
    request.app.state.last_analysis = {
        "request_id": request.state.request_id,
        "run_id": data.get("run_id"),
        "status": status,
        "used_mock_data": bool(provenance.get("used_mock_data")),
        "error_count": len(data.get("errors") or []),
    }
    return AnalyzeResponse(
        success=True, status=status, message=message, report_markdown=report, data=data
    )


@app.post("/api/compare", response_model=CompareResponse)
async def compare_sites(
    payload: CompareRequest,
    request: Request,
    _auth: None = Depends(require_access_token),
) -> CompareResponse:
    """Screen 2-5 sites with one evidence model and no LLM ranking."""

    await _enforce_rate_limit(request, cost=len(payload.candidates))
    candidate_semaphore = asyncio.Semaphore(
        min(len(payload.candidates), max(1, settings.compare_max_parallel_candidates))
    )

    async def analyze_candidate(candidate: CandidateSite) -> dict[str, Any]:
        tools = _amap_tools(request)
        try:
            async with candidate_semaphore:
                report, state = await asyncio.wait_for(
                    run_analysis(
                        store_name=candidate.name,
                        store_address=candidate.address,
                        store_type=payload.store_type,
                        analysis_radius=payload.analysis_radius,
                        use_llm=False,
                        deep_analysis=False,
                        location=candidate.location,
                        avg_ticket=payload.avg_ticket,
                        seat_count=payload.seat_count,
                        daily_fixed_cost=payload.daily_fixed_cost,
                        variable_cost_rate=payload.variable_cost_rate,
                        save_report=False,
                        display_report=False,
                        amap_tools=tools,
                    ),
                    timeout=settings.analysis_timeout_seconds,
                )
            if not report or not state or not state.get("location"):
                raise ValueError("位置解析失败或工作流没有生成完整结果")
            data = _build_response_data(state, report)
            status = "degraded" if _analysis_is_degraded(data, state) else "complete"
            data["status"] = status
            (data.get("provenance") or {})["status"] = status
            # Screening responses intentionally omit long reports and raw chart payloads.
            data.pop("report_markdown", None)
            data.pop("charts", None)
            data.pop("competitors", None)
            return {
                "candidate_id": candidate.candidate_id,
                "candidate_name": candidate.name,
                "candidate_address": candidate.address,
                "data": data,
            }
        except Exception as error:
            logger.warning(
                "candidate_analysis_failed request_id=%s candidate_id=%s error=%s",
                request.state.request_id,
                candidate.candidate_id,
                type(error).__name__,
            )
            return {
                "candidate_id": candidate.candidate_id,
                "candidate_name": candidate.name,
                "candidate_address": candidate.address,
                "error": f"候选点分析失败：{type(error).__name__}",
            }
        finally:
            await tools.close()

    async with _analysis_semaphore:
        analyzed = await asyncio.gather(
            *(analyze_candidate(candidate) for candidate in payload.candidates)
        )

    successful = [item for item in analyzed if item.get("data")]
    failures = [
        {
            "candidate_id": item["candidate_id"],
            "candidate_name": item["candidate_name"],
            "candidate_address": item["candidate_address"],
            "error": item.get("error", "未知错误"),
        }
        for item in analyzed
        if not item.get("data")
    ]
    if len(successful) < 2:
        raise HTTPException(status_code=502, detail="成功分析的候选点不足两个，无法形成可信比较")

    comparison = compare_candidate_sites(
        successful,
        weights=payload.weights.model_dump(),
        require_viable=payload.require_viable,
        minimum_evidence_score=payload.minimum_evidence_score,
    )
    degraded = bool(failures) or any(
        item["data"].get("status") == "degraded" for item in successful
    )
    status: Literal["complete", "degraded"] = "degraded" if degraded else "complete"
    message = comparison["message"]
    if failures:
        message += f" 另有 {len(failures)} 个候选点分析失败，未参与排名。"
    response_data = {
        "request_id": request.state.request_id,
        "status": status,
        "store_type": payload.store_type,
        "analysis_radius": payload.analysis_radius,
        "screening_mode": "deterministic_no_llm",
        "successful_candidate_count": len(successful),
        "failed_candidates": failures,
        **comparison,
    }
    request.app.state.last_analysis = {
        "request_id": request.state.request_id,
        "operation": "compare",
        "status": status,
        "candidate_count": len(payload.candidates),
        "failed_candidate_count": len(failures),
        "recommended_candidate_id": comparison.get("recommended_candidate_id"),
    }
    return CompareResponse(success=True, status=status, message=message, data=response_data)


def _build_response_data(state: dict[str, Any], report: str) -> dict[str, Any]:
    location = _serialize(state.get("location")) or {}
    competitors = _serialize(state.get("competitors")) or []
    traffic = _serialize(state.get("traffic")) or {}
    weather = _serialize(state.get("weather")) or {}
    poi = _serialize(state.get("poi_analysis")) or {}
    charts = _serialize(state.get("charts")) or {}
    competition = _serialize(state.get("competition_analysis")) or {}
    revenue = _serialize(state.get("revenue_simulation")) or {}
    provenance = _serialize(state.get("provenance")) or {}

    traffic_value = (traffic.get("traffic_score") or {}).get("综合", 0)
    traffic_label = (
        "极佳"
        if traffic_value >= 8
        else "良好"
        if traffic_value >= 6
        else "一般"
        if traffic_value >= 4
        else "较弱"
    )
    counts = poi.get("poi_counts") or {}
    total = sum(counts.values()) if counts else 0
    main_type, main_count = (
        max(counts.items(), key=lambda item: item[1]) if counts else ("暂无数据", 0)
    )
    current_weather = weather.get("current") or {}
    scenarios = revenue.get("scenario_simulations") or []
    recommended_id = revenue.get("recommended_strategy") or revenue.get("best_available_strategy")
    recommended = next((item for item in scenarios if item.get("id") == recommended_id), None)
    if recommended is None and scenarios:
        recommended = scenarios[0]

    line_data = []
    if recommended:
        line_data = [
            {
                "name": item.get("name"),
                "value": item.get("revenue", 0),
                "orders": item.get("orders", 0),
            }
            for item in recommended.get("daily_series", [])
        ]
    pie_data = [{"name": name, "value": value} for name, value in counts.items() if value > 0]

    result = {
        "run_id": state.get("run_id"),
        "status": state.get("workflow_status")
        if state.get("workflow_status") in {"complete", "degraded"}
        else "degraded",
        "storeName": state.get("store_name"),
        "storeAddress": state.get("store_address"),
        "storeType": state.get("store_type"),
        "analysisRadius": state.get("analysis_radius"),
        "location": location,
        "competition_score": (competition.get("competition_intensity") or {}).get(
            "score", min(10, round(len(competitors) / 2, 1))
        ),
        "competitor_count": len(competitors),
        "traffic_score": traffic_label,
        "traffic_score_value": traffic_value,
        "traffic_desc": traffic.get("summary") or "暂无交通说明",
        "poi_main_type": main_type,
        "poi_desc": f"采样 {main_count} 个，占本次样本 {round(main_count / total * 100) if total else 0}%",
        "weather_main": current_weather.get("weather") or "未知",
        "weather_desc": f"温度 {current_weather.get('temperature') or '-'}°C",
        "lineChartData": line_data,
        "pieChartData": pie_data,
        "competitors": competitors,
        "traffic": traffic,
        "weather": weather,
        "poi_analysis": poi,
        "charts": charts,
        "competition_analysis": competition,
        "revenue_simulation": revenue,
        "provenance": provenance,
        "errors": list(dict.fromkeys(state.get("errors") or [])),
        "report_markdown": report,
    }
    calibrated_input_count = sum(
        state.get(key) is not None
        for key in ("avg_ticket", "seat_count", "daily_fixed_cost", "variable_cost_rate")
    )
    result["evidence_quality"] = assess_evidence_quality(
        result, calibrated_input_count=calibrated_input_count
    )
    return result


def _serialize(value: Any) -> Any:
    if is_dataclass(value):
        return {key: _serialize(item) for key, item in asdict(value).items()}
    if isinstance(value, dict):
        return {str(key): _serialize(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_serialize(item) for item in value]
    return value
