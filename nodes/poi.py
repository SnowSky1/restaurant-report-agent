"""Nearby commercial-environment analysis."""

from __future__ import annotations

from typing import Any

from .state import AgentState, POIAnalysis

POI_CATEGORIES = {
    "写字楼": {"keywords": "写字楼|办公楼", "types": "120201"},
    "住宅": {"keywords": "住宅|小区|公寓", "types": "120300"},
    "商场": {"keywords": "商场|购物中心|百货", "types": "060100"},
    "学校": {"keywords": "学校|大学|中学|小学", "types": "141200|141201|141202|141203"},
    "医院": {"keywords": "医院|诊所", "types": "090100|090200"},
}


async def poi_node(state: AgentState, amap_tools: Any) -> dict:
    errors = list(state.get("errors", []))
    location = state.get("location")
    if not location:
        errors.append("缺少位置信息，无法分析商业环境")
        return {"poi_analysis": None, "errors": errors}

    radius = state.get("analysis_radius", 1000)
    combined_types = "|".join(config["types"] for config in POI_CATEGORIES.values())
    try:
        result = await amap_tools.search_around(
            location=location.coordinates,
            types=combined_types,
            radius=radius,
            page_size=25,
        )
        rows = list(result.get("pois") or [])
        source = result.get("_meta", {}).get("source", "unknown")
    except Exception as error:
        errors.append(f"商业环境 POI 搜索失败：{error}")
        rows = []
        source = "unknown"

    counts: dict[str, int] = {category: 0 for category in POI_CATEGORIES}
    details: list[dict[str, Any]] = []
    for poi in rows:
        category = _poi_category(str(poi.get("typecode") or ""), str(poi.get("type") or ""))
        if not category:
            continue
        counts[category] += 1
        if sum(1 for item in details if item["category"] == category) < 5:
            details.append(
                {
                    "category": category,
                    "name": poi.get("name", ""),
                    "distance": str(poi.get("distance") or ""),
                    "type": poi.get("type", ""),
                    "location": poi.get("location", ""),
                    "source": source,
                }
            )

    return {
        "poi_analysis": POIAnalysis(
            poi_counts=counts,
            poi_details=details,
            poi_summary=_generate_poi_summary(counts),
        ),
        "errors": errors,
    }


def _poi_category(typecode: str, type_name: str) -> str | None:
    if "120201" in typecode or "写字楼" in type_name:
        return "写字楼"
    if typecode.startswith("1203") or "住宅区" in type_name:
        return "住宅"
    if typecode.startswith("0601") or "商场" in type_name or "购物中心" in type_name:
        return "商场"
    if typecode.startswith("1412") or "学校" in type_name:
        return "学校"
    if typecode.startswith("090") or "医院" in type_name or "诊所" in type_name:
        return "医院"
    return None


def _generate_poi_summary(counts: dict[str, int]) -> str:
    total = sum(counts.values())
    if total == 0:
        return "当前数据源没有检出周边配套，请结合现场踏勘复核"
    main_type, main_count = max(counts.items(), key=lambda item: item[1])
    suggestions = {
        "写字楼": "工作日午餐与下午茶需求更突出，可设计高周转商务套餐",
        "住宅": "家庭与晚间消费潜力较高，应加强外卖和家庭套餐",
        "商场": "休闲和周末客流更集中，适合联名活动与到店体验",
        "学校": "学生客群更重视性价比、出餐速度与社交属性",
        "医院": "陪护与医务客群偏好稳定、清淡和便捷的供给",
    }
    return f"本次采样共 {total} 个周边设施，以{main_type}最多（{main_count}个）；{suggestions.get(main_type, '建议继续现场验证客群结构')}"
