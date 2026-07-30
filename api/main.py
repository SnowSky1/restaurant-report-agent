"""FastAPI surface for the restaurant analysis workflow."""

from __future__ import annotations

import asyncio
from dataclasses import asdict, is_dataclass
from typing import Any, Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

from config.settings import settings
from main import run_analysis
from tools.amap_tools import AmapTools


app = FastAPI(
    title="Restaurant Report Agent API",
    version="0.1.0",
    description="LangGraph + Amap + CompeteAI-inspired restaurant analysis",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    store_name: str = Field(min_length=1, max_length=100)
    store_address: str = Field(min_length=2, max_length=300)
    store_type: str = Field(default="餐厅", min_length=1, max_length=50)
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
        if not value:
            return None
        try:
            longitude, latitude = (float(part.strip()) for part in value.split(",", 1))
        except (TypeError, ValueError):
            raise ValueError("location 必须是“经度,纬度”") from None
        if not -180 <= longitude <= 180 or not -90 <= latitude <= 90:
            raise ValueError("location 坐标超出有效范围")
        return f"{longitude:.6f},{latitude:.6f}"


class AnalyzeResponse(BaseModel):
    success: bool
    message: str
    report_markdown: str
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
    return {
        "status": "ok",
        "version": app.version,
        "data_mode": settings.data_mode,
        "amap_transport": settings.amap_transport,
        "amap_configured": bool(settings.amap_maps_api_key),
        "llm_provider": settings.llm_provider,
        "llm_model": llm_config.get("model"),
        "llm_configured": bool(llm_config.get("api_key")),
        "krill_fallback_enabled": settings.enable_krill_fallback,
    }


@app.get("/api/geocode")
async def geocode_address(address: str = Query(min_length=2, max_length=300)) -> dict[str, Any]:
    tools = AmapTools(
        settings.amap_mcp_url,
        settings.amap_maps_api_key,
        data_mode=settings.data_mode,
        transport=settings.amap_transport,
        timeout=settings.request_timeout_seconds,
    )
    try:
        result = await tools.geocode(address)
        geocodes = result.get("geocodes") or []
        if not geocodes:
            raise HTTPException(status_code=404, detail="未找到该地址")
        return {"success": True, "location": geocodes[0], "provenance": tools.provenance()}
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(status_code=502, detail=f"地址解析失败：{type(error).__name__}") from error
    finally:
        await tools.close()


@app.get("/api/reverse-geocode")
async def reverse_geocode(location: str = Query(pattern=r"^-?\d+(?:\.\d+)?,-?\d+(?:\.\d+)?$")) -> dict[str, Any]:
    tools = AmapTools(
        settings.amap_mcp_url,
        settings.amap_maps_api_key,
        data_mode=settings.data_mode,
        transport=settings.amap_transport,
        timeout=settings.request_timeout_seconds,
    )
    try:
        result = await tools.reverse_geocode(location)
        regeocode = result.get("regeocode") or {}
        if not regeocode:
            raise HTTPException(status_code=404, detail="未找到该坐标")
        return {"success": True, "location": regeocode, "provenance": tools.provenance()}
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(status_code=502, detail=f"逆地理编码失败：{type(error).__name__}") from error
    finally:
        await tools.close()


@app.post("/api/analyze", response_model=AnalyzeResponse)
async def create_analysis(request: AnalyzeRequest) -> AnalyzeResponse:
    try:
        report, state = await asyncio.wait_for(
            run_analysis(
                store_name=request.store_name,
                store_address=request.store_address,
                store_type=request.store_type,
                analysis_radius=request.analysis_radius,
                use_llm=request.use_llm,
                deep_analysis=request.deep_analysis,
                location=request.location,
                avg_ticket=request.avg_ticket,
                seat_count=request.seat_count,
                daily_fixed_cost=request.daily_fixed_cost,
                variable_cost_rate=request.variable_cost_rate,
                save_report=True,
                display_report=False,
            ),
            timeout=180,
        )
    except asyncio.TimeoutError as error:
        raise HTTPException(status_code=504, detail="分析超过 180 秒，请重试或暂时关闭 LLM 深度解释") from error
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"分析失败：{type(error).__name__}") from error

    if not report or not state:
        raise HTTPException(status_code=502, detail="工作流没有生成报告，请检查配置和后端日志")
    if not state.get("location"):
        raise HTTPException(status_code=502, detail="位置解析失败，无法生成可信分析；请检查地址或改用精确坐标")

    data = _build_response_data(state, report)
    provenance = data.get("provenance") or {}
    if provenance.get("used_mock_data"):
        message = "分析完成；部分数据因真实接口不可用而使用了明确标注的模拟回退"
    else:
        message = "分析完成；地图与周边数据来自真实接口"
    return AnalyzeResponse(success=True, message=message, report_markdown=report, data=data)


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
    traffic_label = "极佳" if traffic_value >= 8 else "良好" if traffic_value >= 6 else "一般" if traffic_value >= 4 else "较弱"
    counts = poi.get("poi_counts") or {}
    total = sum(counts.values()) if counts else 0
    main_type, main_count = max(counts.items(), key=lambda item: item[1]) if counts else ("暂无数据", 0)
    current_weather = weather.get("current") or {}
    scenarios = revenue.get("scenario_simulations") or []
    recommended_id = revenue.get("recommended_strategy")
    recommended = next((item for item in scenarios if item.get("id") == recommended_id), None)
    if recommended is None and scenarios:
        recommended = scenarios[0]

    line_data = []
    if recommended:
        line_data = [
            {"name": item.get("name"), "value": item.get("revenue", 0), "orders": item.get("orders", 0)}
            for item in recommended.get("daily_series", [])
        ]
    pie_data = [{"name": name, "value": value} for name, value in counts.items() if value > 0]

    return {
        "run_id": state.get("run_id"),
        "storeName": state.get("store_name"),
        "storeAddress": state.get("store_address"),
        "storeType": state.get("store_type"),
        "analysisRadius": state.get("analysis_radius"),
        "location": location,
        "competition_score": (competition.get("competition_intensity") or {}).get("score", min(10, round(len(competitors) / 2, 1))),
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


def _serialize(value: Any) -> Any:
    if is_dataclass(value):
        return {key: _serialize(item) for key, item in asdict(value).items()}
    if isinstance(value, dict):
        return {str(key): _serialize(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_serialize(item) for item in value]
    return value
