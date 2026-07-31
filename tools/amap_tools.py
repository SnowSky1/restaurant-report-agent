"""High-level Amap tools with explicit real/mock provenance.

The reliable path uses the Amap Web Service REST API.  ``DATA_MODE=auto``
falls back to deterministic sample data only when a real call fails or returns
no usable rows.  Every result contains ``_meta`` so the UI can disclose that
fallback instead of presenting sample data as live data.
"""

from __future__ import annotations

import asyncio
import hashlib
import re
from contextvars import ContextVar
from copy import deepcopy
from datetime import datetime
from time import monotonic, perf_counter
from typing import Any

import httpx

from mcp_client.client import MCPClient

AMAP_REST_BASE_URL = "https://restapi.amap.com"
_REST_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}
_OPERATION_METRICS: ContextVar[dict[str, int] | None] = ContextVar(
    "amap_operation_metrics", default=None
)


class AmapAPIError(RuntimeError):
    pass


class AmapTools:
    """Amap geocoding, POI and weather tools."""

    def __init__(
        self,
        mcp_url: str,
        api_key: str,
        *,
        data_mode: str = "auto",
        transport: str = "rest",
        timeout: float = 30.0,
        http_client: httpx.AsyncClient | None = None,
        cache_ttl_seconds: float = 300.0,
        max_retries: int = 2,
        max_parallel_requests: int = 4,
    ):
        self.api_key = api_key
        self.data_mode = data_mode
        self.transport = transport
        self.timeout = timeout
        self.cache_ttl_seconds = max(0.0, cache_ttl_seconds)
        self.max_retries = max(0, max_retries)
        self._request_semaphore = asyncio.Semaphore(max(1, max_parallel_requests))
        self.mcp_client = MCPClient(mcp_url, api_key, timeout) if transport == "mcp" else None
        self._owns_http = http_client is None
        self.http = http_client
        if self.http is None and data_mode != "mock" and api_key:
            self.http = httpx.AsyncClient(base_url=AMAP_REST_BASE_URL, timeout=timeout)
        self.events: list[dict[str, Any]] = []
        self.http_call_count = 0
        self.cache_hits = 0
        self.upstream_latency_ms = 0

    @property
    def used_mock_data(self) -> bool:
        return any(event["source"] == "mock" for event in self.events)

    @property
    def used_real_data(self) -> bool:
        return any(event["source"] in {"amap_rest", "amap_mcp"} for event in self.events)

    def provenance(self) -> dict[str, Any]:
        sources = sorted({event["source"] for event in self.events})
        warnings = [event["message"] for event in self.events if event["source"] == "mock"]
        return {
            "mode": self.data_mode,
            "transport": self.transport,
            "sources": sources,
            "used_real_data": self.used_real_data,
            "used_mock_data": self.used_mock_data,
            "warnings": warnings,
            "api_calls": self.http_call_count,
            "cache_hits": self.cache_hits,
            "upstream_latency_ms": self.upstream_latency_ms,
            "operations": [dict(event) for event in self.events],
            "sample_scope": "高德周边搜索每类最多返回单页 25 条，属于样本而非完整市场普查",
        }

    async def initialize(self) -> None:
        if self.transport == "mcp" and self.data_mode != "mock" and self.mcp_client:
            await self.mcp_client.initialize()

    async def close(self) -> None:
        if self._owns_http and self.http is not None:
            await self.http.aclose()
        if self.mcp_client:
            await self.mcp_client.close()

    def _metric_start(self) -> dict[str, int]:
        metrics = {"api_calls": 0, "cache_hits": 0, "latency_ms": 0}
        _OPERATION_METRICS.set(metrics)
        return metrics

    def _record(
        self,
        tool: str,
        source: str,
        message: str = "",
        started: dict[str, int] | None = None,
    ) -> None:
        metrics = started or {"api_calls": 0, "cache_hits": 0, "latency_ms": 0}
        self.events.append(
            {
                "tool": tool,
                "source": source,
                "message": message,
                "api_calls": metrics["api_calls"],
                "cache_hits": metrics["cache_hits"],
                "latency_ms": metrics["latency_ms"],
            }
        )

    @staticmethod
    def _with_meta(
        payload: dict[str, Any], source: str, fallback_reason: str = ""
    ) -> dict[str, Any]:
        result = dict(payload)
        result["_meta"] = {
            "source": source,
            "is_mock": source == "mock",
            "fallback_reason": fallback_reason,
        }
        return result

    async def _rest_get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        if not self.api_key:
            raise AmapAPIError("Amap API key is not configured")
        if self.http is None:
            self.http = httpx.AsyncClient(base_url=AMAP_REST_BASE_URL, timeout=self.timeout)
        request_params = {**params, "key": self.api_key, "output": "json"}
        cache_key = self._cache_key(path, request_params)
        cached = _REST_CACHE.get(cache_key)
        if cached and cached[0] > monotonic():
            self.cache_hits += 1
            metrics = _OPERATION_METRICS.get()
            if metrics is not None:
                metrics["cache_hits"] += 1
            return deepcopy(cached[1])
        if cached:
            _REST_CACHE.pop(cache_key, None)

        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            started = perf_counter()
            latency_recorded = False
            self.http_call_count += 1
            metrics = _OPERATION_METRICS.get()
            if metrics is not None:
                metrics["api_calls"] += 1
            try:
                async with self._request_semaphore:
                    response = await self.http.get(path, params=request_params)
                elapsed_ms = round((perf_counter() - started) * 1000)
                self.upstream_latency_ms += elapsed_ms
                if metrics is not None:
                    metrics["latency_ms"] += elapsed_ms
                latency_recorded = True
                if response.status_code == 429 or response.status_code >= 500:
                    raise httpx.HTTPStatusError(
                        f"retryable Amap HTTP {response.status_code}",
                        request=response.request,
                        response=response,
                    )
                response.raise_for_status()
                data = response.json()
                if str(data.get("status")) != "1":
                    info = data.get("info") or "unknown Amap error"
                    infocode = data.get("infocode") or "unknown"
                    raise AmapAPIError(f"{info} ({infocode})")
                if self.cache_ttl_seconds:
                    if len(_REST_CACHE) >= 1024:
                        expired = [
                            key
                            for key, (expires, _) in _REST_CACHE.items()
                            if expires <= monotonic()
                        ]
                        for key in expired:
                            _REST_CACHE.pop(key, None)
                        if len(_REST_CACHE) >= 1024:
                            _REST_CACHE.pop(next(iter(_REST_CACHE)))
                    _REST_CACHE[cache_key] = (
                        monotonic() + self.cache_ttl_seconds,
                        deepcopy(data),
                    )
                return data
            except (httpx.RequestError, httpx.HTTPStatusError) as error:
                if not latency_recorded:
                    elapsed_ms = round((perf_counter() - started) * 1000)
                    self.upstream_latency_ms += elapsed_ms
                    if metrics is not None:
                        metrics["latency_ms"] += elapsed_ms
                last_error = error
                if attempt >= self.max_retries:
                    status = (
                        error.response.status_code
                        if isinstance(error, httpx.HTTPStatusError)
                        else None
                    )
                    detail = f"HTTP {status}" if status else type(error).__name__
                    raise AmapAPIError(
                        f"Amap request failed after {attempt + 1} attempt(s): {detail}"
                    ) from error
                await asyncio.sleep(min(0.25 * (2**attempt), 1.0))
        raise AmapAPIError(str(last_error or "Amap request failed"))

    def _cache_key(self, path: str, params: dict[str, Any]) -> str:
        safe_params = {key: value for key, value in params.items() if key != "key"}
        key_fingerprint = hashlib.sha256(self.api_key.encode("utf-8")).hexdigest()[:12]
        payload = repr((path, sorted(safe_params.items()), key_fingerprint)).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    async def _mcp_call(self, tool: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if not self.mcp_client:
            raise AmapAPIError("MCP transport is not initialized")
        started = perf_counter()
        self.http_call_count += 1
        metrics = _OPERATION_METRICS.get()
        if metrics is not None:
            metrics["api_calls"] += 1
        try:
            result = await self.mcp_client.call_tool(tool, arguments)
        finally:
            elapsed_ms = round((perf_counter() - started) * 1000)
            self.upstream_latency_ms += elapsed_ms
            if metrics is not None:
                metrics["latency_ms"] += elapsed_ms
        if not result:
            raise AmapAPIError(f"MCP tool {tool} returned no data")
        return result

    async def geocode(self, address: str, city: str | None = None) -> dict[str, Any]:
        metric_start = self._metric_start()
        if self.data_mode == "mock":
            return self._mock_geocode(address, "DATA_MODE=mock", metric_start)

        try:
            if self.transport == "mcp":
                data = await self._mcp_call("maps_geo", {"address": address, "city": city or ""})
            else:
                data = await self._rest_get(
                    "/v3/geocode/geo",
                    {"address": address, **({"city": city} if city else {})},
                )
            if data.get("geocodes"):
                self._record(
                    "geocode",
                    "amap_mcp" if self.transport == "mcp" else "amap_rest",
                    started=metric_start,
                )
                return self._with_meta(data, "amap_mcp" if self.transport == "mcp" else "amap_rest")
            raise AmapAPIError("geocoding returned no candidate")
        except Exception as primary_error:
            # Some Amap keys allow place search/reverse geocoding but not the
            # dedicated geocoding product.  Place-text is still real Amap data.
            if self.transport == "rest":
                try:
                    candidate = await self._place_text_geocode(address, city)
                    self._record("geocode", "amap_rest", "used place-text fallback", metric_start)
                    return candidate
                except Exception as place_error:
                    primary_error = AmapAPIError(f"{primary_error}; place search: {place_error}")
            if self.data_mode == "real":
                raise primary_error
            return self._mock_geocode(address, str(primary_error), metric_start)

    async def _place_text_geocode(self, address: str, city: str | None) -> dict[str, Any]:
        inferred_city = city or self._extract_city(address)
        last_error = "no place candidate"
        for query in self._landmark_queries(address):
            params: dict[str, Any] = {
                "keywords": query,
                "offset": 20,
                "extensions": "all",
            }
            if inferred_city:
                params.update({"city": inferred_city, "citylimit": "true"})
            data = await self._rest_get("/v3/place/text", params)
            pois = data.get("pois") or []
            if not pois:
                continue
            poi = pois[0]
            location = poi.get("location")
            if not location:
                last_error = "place candidate has no coordinates"
                continue
            regeo = await self._rest_get(
                "/v3/geocode/regeo",
                {"location": location, "extensions": "all", "radius": 1000},
            )
            component = regeo.get("regeocode", {}).get("addressComponent", {})
            business_areas = component.get("businessAreas") or []
            geocode = {
                "formatted_address": regeo.get("regeocode", {}).get("formatted_address")
                or poi.get("address")
                or address,
                "location": location,
                "province": component.get("province") or "",
                "city": component.get("city") or component.get("province") or inferred_city or "",
                "district": component.get("district") or "",
                "adcode": component.get("adcode") or poi.get("adcode") or "",
                "business_area": business_areas[0].get("name", "") if business_areas else "",
                "matched_poi": poi.get("name", ""),
            }
            return self._with_meta({"status": "1", "geocodes": [geocode]}, "amap_rest")
        raise AmapAPIError(last_error)

    @staticmethod
    def _extract_city(address: str) -> str:
        match = re.search(r"([^省市区县]{2,12}市)", address)
        return match.group(1) if match else ""

    @staticmethod
    def _landmark_queries(address: str) -> list[str]:
        candidates: list[str] = []
        after_number = re.split(r"\d+号", address, maxsplit=1)
        if len(after_number) == 2 and after_number[1].strip():
            candidates.append(after_number[1].strip(" ，,.-"))
        for marker in ("区", "县", "市"):
            if marker in address:
                tail = address.rsplit(marker, 1)[-1].strip()
                if tail:
                    candidates.append(tail)
                    break
        candidates.append(address)
        result: list[str] = []
        for candidate in candidates:
            if candidate and candidate not in result:
                result.append(candidate)
        return result

    async def reverse_geocode(self, location: str, radius: int = 1000) -> dict[str, Any]:
        metric_start = self._metric_start()
        if self.data_mode == "mock":
            return self._mock_reverse_geocode(location, "DATA_MODE=mock", metric_start)
        try:
            if self.transport == "mcp":
                data = await self._mcp_call(
                    "maps_regeo",
                    {"location": location, "radius": str(radius), "extensions": "all"},
                )
                source = "amap_mcp"
            else:
                data = await self._rest_get(
                    "/v3/geocode/regeo",
                    {"location": location, "radius": radius, "extensions": "all"},
                )
                source = "amap_rest"
            if not data.get("regeocode"):
                raise AmapAPIError("reverse geocoding returned no result")
            self._record("reverse_geocode", source, started=metric_start)
            return self._with_meta(data, source)
        except Exception as error:
            if self.data_mode == "real":
                raise
            return self._mock_reverse_geocode(location, str(error), metric_start)

    async def search_around(
        self,
        location: str,
        keywords: str = "",
        types: str = "",
        radius: int = 1000,
        page_size: int = 25,
    ) -> dict[str, Any]:
        metric_start = self._metric_start()
        if self.data_mode == "mock":
            return self._mock_search(
                location, keywords, types, radius, "DATA_MODE=mock", metric_start
            )
        try:
            if self.transport == "mcp":
                data = await self._mcp_call(
                    "maps_search_around",
                    {
                        "location": location,
                        "keywords": keywords,
                        "types": types,
                        "radius": str(radius),
                    },
                )
                source = "amap_mcp"
            else:
                inferred_types = types or self._infer_types(keywords)
                params: dict[str, Any] = {
                    "location": location,
                    "radius": max(100, min(int(radius), 50000)),
                    "offset": max(1, min(int(page_size), 25)),
                    "extensions": "all",
                    "sortrule": "distance",
                }
                if inferred_types:
                    params["types"] = inferred_types
                # Amap does not interpret pipe-delimited natural-language
                # keywords as OR; type codes provide much better coverage.
                if keywords and "|" not in keywords and not inferred_types:
                    params["keywords"] = keywords
                data = await self._rest_get("/v3/place/around", params)
                source = "amap_rest"
            pois = data.get("pois") or []
            if not pois:
                raise AmapAPIError("nearby search returned no POIs")
            self._record("search_around", source, started=metric_start)
            return self._with_meta(data, source)
        except Exception as error:
            if self.data_mode == "real":
                raise
            return self._mock_search(location, keywords, types, radius, str(error), metric_start)

    @staticmethod
    def _infer_types(keywords: str) -> str:
        mappings = [
            (("地铁",), "150500"),
            (("公交",), "150700"),
            (("停车",), "150900"),
            (("写字楼", "办公楼"), "120201"),
            (("住宅", "小区", "公寓"), "120300"),
            (("商场", "购物中心", "百货"), "060100"),
            (("学校", "大学", "中学", "小学"), "141200|141201|141202|141203"),
            (("医院", "诊所"), "090100|090200"),
            (("餐饮", "咖啡", "奶茶", "火锅", "烧烤", "快餐", "面馆"), "050000"),
        ]
        for words, code in mappings:
            if any(word in keywords for word in words):
                return code
        return ""

    async def get_weather(self, city: str) -> dict[str, Any]:
        metric_start = self._metric_start()
        if self.data_mode == "mock":
            return self._mock_weather(city, "DATA_MODE=mock", metric_start)
        try:
            if self.transport == "mcp":
                data = await self._mcp_call("maps_weather", {"city": city, "extensions": "all"})
                source = "amap_mcp"
            else:
                live, forecast = await asyncio.gather(
                    self._rest_get("/v3/weather/weatherInfo", {"city": city, "extensions": "base"}),
                    self._rest_get("/v3/weather/weatherInfo", {"city": city, "extensions": "all"}),
                )
                data = {
                    "status": "1",
                    "lives": live.get("lives") or [],
                    "forecasts": forecast.get("forecasts") or [],
                }
                source = "amap_rest"
            if not data.get("lives") and not data.get("forecasts"):
                raise AmapAPIError("weather returned no data")
            self._record("weather", source, started=metric_start)
            return self._with_meta(data, source)
        except Exception as error:
            if self.data_mode == "real":
                raise
            return self._mock_weather(city, str(error), metric_start)

    def _mock_geocode(
        self, address: str, reason: str, metric_start: dict[str, int] | None = None
    ) -> dict[str, Any]:
        reason = self._friendly_reason(reason)
        known = [
            (
                ("钱江世纪城",),
                ("120.254158,30.231242", "杭州市", "萧山区", "钱江世纪城", "330109"),
            ),
            (
                ("柏林春天", "泊林春天"),
                ("120.290182,30.237687", "杭州市", "萧山区", "钱江世纪城", "330109"),
            ),
            (
                ("SOHO现代城", "建国路88号"),
                ("116.475831,39.906540", "北京市", "朝阳区", "大望路", "110105"),
            ),
        ]
        selected = None
        for words, value in known:
            if any(word in address for word in words):
                selected = value
                break
        if selected is None:
            seed = int(hashlib.sha256(address.encode("utf-8")).hexdigest()[:8], 16)
            selected = (
                f"{116.35 + (seed % 2000) / 10000:.6f},{39.85 + (seed % 1200) / 10000:.6f}",
                "北京市",
                "朝阳区",
                "示例商圈",
                "110105",
            )
        location, city, district, business_area, adcode = selected
        self._record("geocode", "mock", f"地理编码使用模拟数据：{reason}", metric_start)
        return self._with_meta(
            {
                "status": "1",
                "geocodes": [
                    {
                        "formatted_address": address,
                        "location": location,
                        "city": city,
                        "district": district,
                        "business_area": business_area,
                        "adcode": adcode,
                    }
                ],
            },
            "mock",
            reason,
        )

    def _mock_reverse_geocode(
        self, location: str, reason: str, metric_start: dict[str, int] | None = None
    ) -> dict[str, Any]:
        reason = self._friendly_reason(reason)
        self._record("reverse_geocode", "mock", f"逆地理编码使用模拟数据：{reason}", metric_start)
        return self._with_meta(
            {
                "status": "1",
                "regeocode": {
                    "formatted_address": "模拟位置（请核对坐标）",
                    "addressComponent": {
                        "province": "北京市",
                        "city": "北京市",
                        "district": "朝阳区",
                        "adcode": "110105",
                        "businessAreas": [{"name": "示例商圈"}],
                    },
                },
            },
            "mock",
            reason,
        )

    def _mock_search(
        self,
        location: str,
        keywords: str,
        types: str,
        radius: int,
        reason: str,
        metric_start: dict[str, int] | None = None,
    ) -> dict[str, Any]:
        reason = self._friendly_reason(reason)
        is_commercial_bundle = (
            sum(code in types for code in ("120201", "120300", "060100", "141200", "090100")) >= 3
        )
        label = (
            "商业环境 POI"
            if is_commercial_bundle
            else (keywords or self._type_label(types) or "周边设施")
        )
        if is_commercial_bundle:
            specs = [
                ("国际中心A座", "商务住宅;楼宇;商务写字楼", "120201"),
                ("创智大厦", "商务住宅;楼宇;商务写字楼", "120201"),
                ("金融中心", "商务住宅;楼宇;商务写字楼", "120201"),
                ("城市花园", "商务住宅;住宅区", "120300"),
                ("滨江公寓", "商务住宅;住宅区", "120300"),
                ("中央社区", "商务住宅;住宅区", "120300"),
                ("城市广场", "购物服务;商场", "060100"),
                ("生活中心", "购物服务;购物中心", "060101"),
                ("实验小学", "科教文化服务;学校", "141203"),
                ("城市中学", "科教文化服务;学校", "141202"),
                ("社区医院", "医疗保健服务;医院", "090100"),
                ("综合门诊部", "医疗保健服务;诊所", "090200"),
            ]
            pois = [
                {
                    "id": f"MOCK{index:03d}",
                    "name": name,
                    "type": poi_type,
                    "typecode": typecode,
                    "address": f"模拟地址 {index} 号",
                    "location": location,
                    "distance": str(min(radius, 120 + index * 62)),
                    "biz_ext": {},
                }
                for index, (name, poi_type, typecode) in enumerate(specs, 1)
            ]
            self._record("search_around", "mock", f"{label}使用模拟数据：{reason}", metric_start)
            return self._with_meta(
                {"status": "1", "count": str(len(pois)), "pois": pois}, "mock", reason
            )

        if "地铁" in label or "150500" in types:
            names = ["中心广场地铁站", "商务区地铁站"]
            poi_type = "交通设施服务;地铁站"
        elif "公交" in label or "150700" in types:
            names = ["中心广场公交站", "商务区东公交站", "城市花园公交站"]
            poi_type = "交通设施服务;公交车站"
        elif "停车" in label or "150900" in types:
            names = ["商业中心停车场", "城市广场地下停车场", "写字楼停车场"]
            poi_type = "交通设施服务;停车场"
        elif "写字楼" in label or "120201" in types:
            names = ["国际中心A座", "创智大厦", "金融中心"]
            poi_type = "商务住宅;楼宇;商务写字楼"
        elif "住宅" in label or "120300" in types:
            names = ["城市花园", "滨江公寓", "中央社区"]
            poi_type = "商务住宅;住宅区"
        elif "商场" in label or "060100" in types:
            names = ["城市广场", "生活中心"]
            poi_type = "购物服务;商场"
        elif "学校" in label or "1412" in types:
            names = ["实验小学", "城市中学"]
            poi_type = "科教文化服务;学校"
        elif "医院" in label or "090" in types:
            names = ["社区医院", "综合门诊部"]
            poi_type = "医疗保健服务;医院"
        else:
            names = ["示例咖啡一店", "示例咖啡二店", "示例茶饮店", "示例简餐店"]
            poi_type = "餐饮服务;咖啡厅"
        pois = []
        for index, name in enumerate(names, 1):
            pois.append(
                {
                    "id": f"MOCK{index:03d}",
                    "name": name,
                    "type": poi_type,
                    "typecode": types.split("|")[0] if types else "050000",
                    "address": f"模拟地址 {index} 号",
                    "location": location,
                    "distance": str(80 + index * 115),
                    "biz_ext": {
                        "rating": f"{4.0 + index / 10:.1f}",
                        "cost": str(25 + index * 5),
                    },
                }
            )
        self._record("search_around", "mock", f"{label}使用模拟数据：{reason}", metric_start)
        return self._with_meta(
            {"status": "1", "count": str(len(pois)), "pois": pois}, "mock", reason
        )

    def _mock_weather(
        self, city: str, reason: str, metric_start: dict[str, int] | None = None
    ) -> dict[str, Any]:
        reason = self._friendly_reason(reason)
        now = datetime.now()
        live = {
            "province": "模拟",
            "city": city or "模拟城市",
            "adcode": "000000",
            "weather": "多云",
            "temperature": "24",
            "winddirection": "东南",
            "windpower": "1-3",
            "humidity": "58",
            "reporttime": now.strftime("%Y-%m-%d %H:%M:%S"),
        }
        casts = [
            {
                "date": now.strftime("%Y-%m-%d"),
                "week": str(now.isoweekday()),
                "dayweather": "多云",
                "nightweather": "晴",
                "daytemp": "28",
                "nighttemp": "20",
                "daywind": "东南",
                "daypower": "1-3",
            }
        ]
        self._record("weather", "mock", f"天气使用模拟数据：{reason}", metric_start)
        return self._with_meta(
            {
                "status": "1",
                "lives": [live],
                "forecasts": [{"city": city, "casts": casts}],
            },
            "mock",
            reason,
        )

    @staticmethod
    def _type_label(types: str) -> str:
        labels = {
            "150500": "地铁站",
            "150700": "公交站",
            "150900": "停车场",
            "120201": "写字楼",
            "120300": "住宅",
            "060100": "商场",
            "141200": "学校",
            "090100": "医院",
            "050000": "餐饮竞品",
        }
        return next((label for code, label in labels.items() if code in types), "")

    @staticmethod
    def _friendly_reason(reason: str) -> str:
        if reason == "DATA_MODE=mock":
            return "已启用显式模拟模式"
        if "10021" in reason or "CUQPS_HAS_EXCEEDED_THE_LIMIT" in reason:
            return "高德调用量已达到当前配额（10021）"
        if "key is not configured" in reason.lower():
            return "未配置高德 Web 服务 Key"
        return reason
