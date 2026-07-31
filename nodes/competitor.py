"""Nearby competitor discovery."""

from __future__ import annotations

from typing import Any

from .state import AgentState, CompetitorInfo

STORE_SEARCH = {
    "餐厅": ("餐饮", "050000"),
    "咖啡店": ("咖啡", "050500"),
    "奶茶店": ("奶茶|茶饮|饮品", "050700"),
    "火锅店": ("火锅", "050000"),
    "烧烤店": ("烧烤|烤肉", "050000"),
    "快餐店": ("快餐|简餐", "050300"),
    "面馆": ("面馆|面食|拉面", "050000"),
    "西餐厅": ("西餐|牛排|意大利", "050200"),
    "日料店": ("日料|日本料理|寿司", "050200"),
    "韩餐厅": ("韩餐|韩国料理|烤肉", "050200"),
    "川菜馆": ("川菜", "050000"),
    "粤菜馆": ("粤菜|广东菜", "050000"),
    "甜品店": ("甜品|蛋糕|甜点", "050900"),
    "面包店": ("面包|烘焙|蛋糕", "050800"),
}


async def competitor_node(state: AgentState, amap_tools: Any) -> dict:
    errors = list(state.get("errors", []))
    location = state.get("location")
    if not location:
        errors.append("缺少位置信息，无法分析竞争对手")
        return {"competitors": [], "errors": errors}

    try:
        store_type = state.get("store_type", "餐厅")
        keywords, typecode = STORE_SEARCH.get(store_type, STORE_SEARCH["餐厅"])
        result = await amap_tools.search_around(
            location=location.coordinates,
            keywords=keywords,
            types=typecode,
            radius=state.get("analysis_radius", 1000),
            page_size=25,
        )
        source = result.get("_meta", {}).get("source", "unknown")
        store_name = state.get("store_name", "").replace(" ", "").lower()
        competitors: list[CompetitorInfo] = []
        for poi in result.get("pois") or []:
            name = str(poi.get("name") or "")
            if not name:
                continue
            normalized_name = name.replace(" ", "").lower()
            if store_name and (normalized_name == store_name or store_name in normalized_name):
                continue
            biz_ext = poi.get("biz_ext") if isinstance(poi.get("biz_ext"), dict) else {}
            competitors.append(
                CompetitorInfo(
                    name=name,
                    distance=str(poi.get("distance") or ""),
                    address=str(poi.get("address") or ""),
                    rating=str(biz_ext.get("rating") or ""),
                    type=str(poi.get("type") or ""),
                    typecode=str(poi.get("typecode") or ""),
                    location=str(poi.get("location") or ""),
                    average_cost=str(biz_ext.get("cost") or ""),
                    source=source,
                )
            )
        return {"competitors": competitors[:20], "errors": errors}
    except Exception as error:
        errors.append(f"竞争对手分析失败：{error}")
        return {"competitors": [], "errors": errors}
