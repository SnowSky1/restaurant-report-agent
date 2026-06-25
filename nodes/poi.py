"""
POI 分析节点

分析周边商业环境：写字楼、住宅、学校、商场等
"""

from typing import Any, Dict, List
from .state import AgentState, POIAnalysis


# POI 类型配置
POI_CATEGORIES = {
    "写字楼": {"keywords": "写字楼|办公楼", "weight": 0.3},
    "住宅": {"keywords": "住宅|小区|公寓", "weight": 0.25},
    "商场": {"keywords": "商场|购物中心|百货", "weight": 0.2},
    "学校": {"keywords": "学校|大学|中学|小学", "weight": 0.15},
    "医院": {"keywords": "医院|诊所", "weight": 0.1},
}


async def poi_node(state: AgentState, amap_tools: Any) -> dict:
    """
    POI 分析节点
    
    搜索周边各类 POI，分析商业环境
    
    Args:
        state: 当前状态
        amap_tools: 高德地图工具实例
        
    Returns:
        dict: 包含 POI 分析结果的状态更新
    """
    print(f"🏢 正在分析周边商业环境...")
    
    errors = list(state.get("errors", []))
    
    location = state.get("location")
    if not location or not location.coordinates:
        errors.append("缺少位置信息，无法分析 POI")
        return {"poi_analysis": None, "errors": errors}
    
    coordinates = location.coordinates
    radius = state.get("analysis_radius", 1000)
    
    poi_counts: Dict[str, int] = {}
    poi_details: List[dict] = []
    
    # 搜索各类 POI
    for category, config in POI_CATEGORIES.items():
        try:
            result = await amap_tools.search_around(
                location=coordinates,
                keywords=config["keywords"],
                radius=radius
            )
            pois = result.get("pois", [])
            poi_counts[category] = len(pois)
            
            # 保存前 5 个详情
            for poi in pois[:5]:
                poi_details.append({
                    "category": category,
                    "name": poi.get("name", ""),
                    "distance": poi.get("distance", ""),
                    "type": poi.get("type", "")
                })
                
        except Exception as e:
            print(f"⚠️ {category} POI 搜索失败: {e}")
            poi_counts[category] = 0
    
    # 生成分析总结
    poi_summary = _generate_poi_summary(poi_counts, state.get("store_type", "餐厅"))
    
    poi_analysis = POIAnalysis(
        poi_counts=poi_counts,
        poi_details=poi_details,
        poi_summary=poi_summary
    )
    
    total_pois = sum(poi_counts.values())
    print(f"✓ POI 分析完成: 共发现 {total_pois} 个相关 POI")
    
    return {
        "poi_analysis": poi_analysis,
        "errors": errors
    }


def _generate_poi_summary(poi_counts: Dict[str, int], store_type: str) -> str:
    """生成 POI 分析总结"""
    if not poi_counts:
        return "周边 POI 信息不足"
    
    total = sum(poi_counts.values())
    if total == 0:
        return "周边商业设施较少"
    
    # 找出主要 POI 类型
    sorted_pois = sorted(poi_counts.items(), key=lambda x: x[1], reverse=True)
    main_type = sorted_pois[0][0] if sorted_pois else "综合"
    main_count = sorted_pois[0][1] if sorted_pois else 0
    
    parts = []
    
    # 主要类型分析
    if main_type == "写字楼" and main_count > 0:
        parts.append(f"周边以写字楼为主（{main_count}栋），工作日午餐/下午茶需求大")
        parts.append("建议关注商务套餐和工作日促销")
    elif main_type == "住宅" and main_count > 0:
        parts.append(f"周边住宅区密集（{main_count}个小区），家庭消费潜力大")
        parts.append("建议关注家庭套餐和外卖服务")
    elif main_type == "商场" and main_count > 0:
        parts.append(f"周边商场较多（{main_count}个），周末客流量大")
        parts.append("建议关注周末活动和休闲消费")
    elif main_type == "学校" and main_count > 0:
        parts.append(f"周边学校较多（{main_count}所），学生群体消费活跃")
        parts.append("建议关注性价比和学生优惠")
    
    # 综合评价
    if total >= 20:
        parts.append("商业环境成熟，客流量有保障")
    elif total >= 10:
        parts.append("商业环境一般，需要特色经营")
    else:
        parts.append("商业环境待发展，需重点拓展外卖")
    
    return "；".join(parts)
