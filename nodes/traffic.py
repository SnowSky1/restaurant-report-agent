"""Traffic accessibility analysis."""

from __future__ import annotations

import asyncio
from typing import Any

from .state import AgentState, TrafficInfo


async def traffic_node(state: AgentState, amap_tools: Any) -> dict:
    errors = list(state.get("errors", []))
    location = state.get("location")
    if not location:
        errors.append("缺少位置信息，无法分析交通")
        return {"traffic": None, "errors": errors}

    radius = state.get("analysis_radius", 1000)
    specs = [
        ("地铁站", "150500"),
        ("公交站", "150700"),
        ("停车场", "150900"),
    ]
    results = await asyncio.gather(
        *[
            amap_tools.search_around(
                location=location.coordinates,
                keywords=keyword,
                types=typecode,
                radius=radius,
                page_size=15,
            )
            for keyword, typecode in specs
        ],
        return_exceptions=True,
    )

    groups: list[list[dict[str, Any]]] = []
    for (label, _), result in zip(specs, results):
        if isinstance(result, Exception):
            errors.append(f"{label}搜索失败：{result}")
            groups.append([])
        else:
            groups.append(list(result.get("pois") or [])[:10])

    subway, bus, parking = groups
    scores = _calculate_traffic_score(subway, bus, parking)
    return {
        "traffic": TrafficInfo(
            subway_stations=subway,
            bus_stations=bus,
            parking_lots=parking,
            traffic_score=scores,
            summary=_generate_traffic_summary(subway, bus, parking, scores),
        ),
        "errors": errors,
    }


def _distance(poi: dict[str, Any], default: int) -> int:
    try:
        return int(float(poi.get("distance") or default))
    except (TypeError, ValueError):
        return default


def _calculate_traffic_score(subway: list[dict], bus: list[dict], parking: list[dict]) -> dict[str, float]:
    nearest_subway = min((_distance(item, 2000) for item in subway), default=2000)
    nearest_bus = min((_distance(item, 1000) for item in bus), default=1000)

    subway_score = 10 if nearest_subway <= 200 else 8 if nearest_subway <= 500 else 6 if nearest_subway <= 800 else 4 if subway else 2
    bus_score = 10 if nearest_bus <= 100 and len(bus) >= 3 else 8 if nearest_bus <= 200 else 6 if nearest_bus <= 300 else 4 if bus else 2
    parking_score = 10 if len(parking) >= 5 else 8 if len(parking) >= 3 else 6 if parking else 2
    total = round(subway_score * 0.4 + bus_score * 0.3 + parking_score * 0.3, 1)
    return {"地铁": subway_score, "公交": bus_score, "停车": parking_score, "综合": total}


def _generate_traffic_summary(
    subway: list[dict], bus: list[dict], parking: list[dict], scores: dict[str, float]
) -> str:
    parts: list[str] = []
    if subway:
        nearest = min(subway, key=lambda item: _distance(item, 2000))
        parts.append(f"最近地铁站 {nearest.get('name', '未知')}，约 {_distance(nearest, 0)} 米")
    else:
        parts.append("分析半径内未检出地铁站")
    parts.append(f"公交站 {len(bus)} 个")
    parts.append(f"停车场 {len(parking)} 个")
    score = scores.get("综合", 0)
    level = "极佳" if score >= 8 else "良好" if score >= 6 else "一般" if score >= 4 else "较弱"
    parts.append(f"交通便利度{level}")
    return "；".join(parts)
