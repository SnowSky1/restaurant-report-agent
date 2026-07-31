"""
图表生成节点

生成可视化图表数据
"""

from .state import AgentState, ChartData


async def chart_node(state: AgentState) -> dict:
    """
    图表生成节点

    根据分析数据生成图表

    Args:
        state: 当前状态
    Returns:
        dict: 包含图表数据的状态更新
    """
    print("📊 正在生成图表数据...")

    errors = list(state.get("errors", []))

    # 竞争对手分布图数据
    competitor_chart = _build_competitor_chart(state.get("competitors", []))

    # POI 分布饼图数据
    poi_chart = _build_poi_chart(state.get("poi_analysis"))

    # 交通评分雷达图数据
    traffic_chart = _build_traffic_chart(state.get("traffic"))

    # 营收情景对比
    revenue_chart = _build_revenue_chart(state.get("revenue_simulation"))

    chart_data = ChartData(
        competitor_chart=competitor_chart,
        poi_chart=poi_chart,
        traffic_chart=traffic_chart,
        revenue_chart=revenue_chart,
    )

    print("✓ 图表数据生成完成")

    return {"charts": chart_data, "errors": errors}


def _build_competitor_chart(competitors: list) -> dict:
    """构建竞争对手分布图数据"""
    if not competitors:
        return {"type": "bar", "data": [], "title": "竞争对手距离分布"}

    # 按距离分组
    distance_groups = {"0-200m": 0, "200-500m": 0, "500-800m": 0, "800m+": 0}

    for comp in competitors:
        try:
            dist = (
                int(comp.distance) if hasattr(comp, "distance") else int(comp.get("distance", 1000))
            )
            if dist <= 200:
                distance_groups["0-200m"] += 1
            elif dist <= 500:
                distance_groups["200-500m"] += 1
            elif dist <= 800:
                distance_groups["500-800m"] += 1
            else:
                distance_groups["800m+"] += 1
        except (ValueError, TypeError):
            distance_groups["800m+"] += 1

    return {
        "type": "bar",
        "title": "竞争对手距离分布",
        "data": [{"name": k, "value": v} for k, v in distance_groups.items()],
    }


def _build_poi_chart(poi_analysis) -> dict:
    """构建 POI 分布饼图数据"""
    if not poi_analysis:
        return {"type": "pie", "data": [], "title": "周边POI分布"}

    poi_counts = {}
    if hasattr(poi_analysis, "poi_counts"):
        poi_counts = poi_analysis.poi_counts
    elif isinstance(poi_analysis, dict):
        poi_counts = poi_analysis.get("poi_counts", {})

    return {
        "type": "pie",
        "title": "周边POI分布",
        "data": [{"name": k, "value": v} for k, v in poi_counts.items() if v > 0],
    }


def _build_traffic_chart(traffic) -> dict:
    """构建交通评分雷达图数据"""
    if not traffic:
        return {"type": "radar", "data": [], "title": "交通便利性评分"}

    traffic_score = {}
    if hasattr(traffic, "traffic_score"):
        traffic_score = traffic.traffic_score
    elif isinstance(traffic, dict):
        traffic_score = traffic.get("traffic_score", {})

    # 雷达图数据格式
    radar_data = []
    for key in ["地铁", "公交", "停车"]:
        if key in traffic_score:
            radar_data.append({"name": key, "value": traffic_score[key]})

    return {"type": "radar", "title": "交通便利性评分", "data": radar_data, "max": 10}


def _build_revenue_chart(simulation) -> dict:
    """Build a scenario revenue/profit comparison chart."""
    if not simulation:
        return {"type": "bar", "data": [], "title": "营收情景模拟"}
    data = []
    for scenario in simulation.get("scenario_simulations", []):
        data.append(
            {
                "name": scenario.get("name", scenario.get("id", "情景")),
                "revenue": scenario.get("monthly_revenue", 0),
                "profit": scenario.get("monthly_profit", 0),
            }
        )
    return {"type": "bar", "data": data, "title": "月度营收与利润情景模拟"}
