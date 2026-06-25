"""
竞争对手分析节点

搜索周边同类型店铺，分析竞争态势
"""

from typing import Any, List
from .state import AgentState, CompetitorInfo


# 店铺类型到搜索关键词的映射
STORE_TYPE_KEYWORDS = {
    "餐厅": "餐饮|中餐|餐厅",
    "咖啡店": "咖啡|咖啡厅|咖啡馆",
    "奶茶店": "奶茶|茶饮|饮品",
    "火锅店": "火锅",
    "烧烤店": "烧烤|烤肉",
    "快餐店": "快餐|简餐",
    "面馆": "面馆|面食|拉面",
    "西餐厅": "西餐|牛排|意大利",
    "日料店": "日料|日本料理|寿司",
    "韩餐厅": "韩餐|韩国料理|烤肉",
    "川菜馆": "川菜",
    "粤菜馆": "粤菜|广东菜",
    "甜品店": "甜品|蛋糕|甜点",
    "面包店": "面包|烘焙|蛋糕",
}


async def competitor_node(state: AgentState, amap_tools: Any) -> dict:
    """
    竞争对手分析节点
    
    搜索周边同类型店铺，提取竞争对手信息
    
    Args:
        state: 当前状态
        amap_tools: 高德地图工具实例
        
    Returns:
        dict: 包含竞争对手列表的状态更新
    """
    print(f"🏪 正在分析竞争对手...")
    
    errors = list(state.get("errors", []))
    competitors: List[CompetitorInfo] = []
    
    location = state.get("location")
    if not location or not location.coordinates:
        errors.append("缺少位置信息，无法分析竞争对手")
        return {"competitors": competitors, "errors": errors}
    
    try:
        # 获取搜索关键词
        store_type = state.get("store_type", "餐厅")
        keywords = STORE_TYPE_KEYWORDS.get(store_type, "餐饮")
        radius = state.get("analysis_radius", 1000)
        
        # 搜索周边同类店铺
        search_result = await amap_tools.search_around(
            location=location.coordinates,
            keywords=keywords,
            radius=radius
        )
        
        pois = search_result.get("pois", [])
        
        for poi in pois[:20]:  # 最多取前 20 个
            # 提取评分
            biz_ext = poi.get("biz_ext", {})
            rating = ""
            if isinstance(biz_ext, dict):
                rating = biz_ext.get("rating", "")
            
            competitor = CompetitorInfo(
                name=poi.get("name", ""),
                distance=poi.get("distance", ""),
                address=poi.get("address", ""),
                rating=rating,
                type=poi.get("type", "")
            )
            competitors.append(competitor)
        
        print(f"✓ 发现 {len(competitors)} 家竞争对手")
        
        return {
            "competitors": competitors,
            "errors": errors
        }
        
    except Exception as e:
        errors.append(f"竞争对手分析异常: {str(e)}")
        print(f"❌ 竞争对手分析失败: {e}")
        return {"competitors": competitors, "errors": errors}
