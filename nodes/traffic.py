"""
交通便利性分析节点

分析周边地铁、公交、停车场等交通设施，计算交通评分
"""

from typing import Any, List
from .state import AgentState, TrafficInfo


async def traffic_node(state: AgentState, amap_tools: Any) -> dict:
    """
    交通便利性分析节点
    
    搜索周边交通设施，计算综合交通评分
    
    Args:
        state: 当前状态
        amap_tools: 高德地图工具实例
        
    Returns:
        dict: 包含交通信息的状态更新
    """
    print(f"🚇 正在分析交通便利性...")
    
    errors = list(state.get("errors", []))
    
    location = state.get("location")
    if not location or not location.coordinates:
        errors.append("缺少位置信息，无法分析交通")
        return {"traffic": None, "errors": errors}
    
    subway_stations: List[dict] = []
    bus_stations: List[dict] = []
    parking_lots: List[dict] = []
    
    coordinates = location.coordinates
    radius = state.get("analysis_radius", 1000)
    
    # 并行搜索各类交通设施（使用 try-except 保证健壮性）
    try:
        subway_result = await amap_tools.search_around(
            location=coordinates,
            keywords="地铁站",
            radius=radius
        )
        subway_stations = subway_result.get("pois", [])[:10]
    except Exception as e:
        print(f"⚠️ 地铁站搜索失败: {e}")
    
    try:
        bus_result = await amap_tools.search_around(
            location=coordinates,
            keywords="公交站",
            radius=radius
        )
        bus_stations = bus_result.get("pois", [])[:10]
    except Exception as e:
        print(f"⚠️ 公交站搜索失败: {e}")
    
    try:
        parking_result = await amap_tools.search_around(
            location=coordinates,
            keywords="停车场",
            radius=radius
        )
        parking_lots = parking_result.get("pois", [])[:10]
    except Exception as e:
        print(f"⚠️ 停车场搜索失败: {e}")
    
    # 计算交通评分
    traffic_score = _calculate_traffic_score(subway_stations, bus_stations, parking_lots)
    
    # 生成交通总结
    summary = _generate_traffic_summary(subway_stations, bus_stations, parking_lots, traffic_score)
    
    traffic_info = TrafficInfo(
        subway_stations=subway_stations,
        bus_stations=bus_stations,
        parking_lots=parking_lots,
        traffic_score=traffic_score,
        summary=summary
    )
    
    print(f"✓ 交通分析完成: 综合评分 {traffic_score.get('综合', 'N/A')}")
    
    return {
        "traffic": traffic_info,
        "errors": errors
    }


def _calculate_traffic_score(subway: List[dict], bus: List[dict], parking: List[dict]) -> dict:
    """计算交通评分"""
    scores = {}
    
    # 地铁评分 (0-10)
    if subway:
        nearest_subway = int(subway[0].get("distance", 1000)) if subway else 1000
        if nearest_subway <= 200:
            scores["地铁"] = 10
        elif nearest_subway <= 500:
            scores["地铁"] = 8
        elif nearest_subway <= 800:
            scores["地铁"] = 6
        else:
            scores["地铁"] = 4
    else:
        scores["地铁"] = 2
    
    # 公交评分 (0-10)
    if bus:
        nearest_bus = int(bus[0].get("distance", 500)) if bus else 500
        bus_count = len(bus)
        if nearest_bus <= 100 and bus_count >= 3:
            scores["公交"] = 10
        elif nearest_bus <= 200:
            scores["公交"] = 8
        elif nearest_bus <= 300:
            scores["公交"] = 6
        else:
            scores["公交"] = 4
    else:
        scores["公交"] = 2
    
    # 停车评分 (0-10)
    if parking:
        parking_count = len(parking)
        if parking_count >= 5:
            scores["停车"] = 10
        elif parking_count >= 3:
            scores["停车"] = 8
        elif parking_count >= 1:
            scores["停车"] = 6
        else:
            scores["停车"] = 4
    else:
        scores["停车"] = 2
    
    # 综合评分
    scores["综合"] = round(
        scores["地铁"] * 0.4 + scores["公交"] * 0.3 + scores["停车"] * 0.3,
        1
    )
    
    return scores


def _generate_traffic_summary(subway: List[dict], bus: List[dict], parking: List[dict], scores: dict) -> str:
    """生成交通总结"""
    parts = []
    
    if subway:
        nearest = subway[0]
        parts.append(f"最近地铁站: {nearest.get('name', '未知')} ({nearest.get('distance', '?')}米)")
    else:
        parts.append("周边无地铁站")
    
    if bus:
        parts.append(f"公交站: {len(bus)} 个")
    
    if parking:
        parts.append(f"停车场: {len(parking)} 个")
    
    score = scores.get("综合", 0)
    if score >= 8:
        level = "极佳"
    elif score >= 6:
        level = "良好"
    elif score >= 4:
        level = "一般"
    else:
        level = "较差"
    
    parts.append(f"交通便利程度: {level}")
    
    return "；".join(parts)
