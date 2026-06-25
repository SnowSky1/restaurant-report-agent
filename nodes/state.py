"""
状态定义模块

定义 LangGraph 工作流使用的 AgentState 和各类数据结构
"""

from typing import TypedDict, Optional, List, Any
from dataclasses import dataclass, field


@dataclass
class LocationInfo:
    """位置信息"""
    coordinates: str  # 经纬度，格式: "116.481488,39.990464"
    address: str  # 格式化地址
    business_area: str  # 所属商圈
    district: str = ""  # 区县
    city: str = ""  # 城市


@dataclass
class CompetitorInfo:
    """竞争对手信息"""
    name: str  # 店铺名称
    distance: str  # 距离（米）
    address: str  # 地址
    rating: str = ""  # 评分
    type: str = ""  # 类型


@dataclass
class TrafficInfo:
    """交通信息"""
    subway_stations: List[dict] = field(default_factory=list)  # 地铁站
    bus_stations: List[dict] = field(default_factory=list)  # 公交站
    parking_lots: List[dict] = field(default_factory=list)  # 停车场
    traffic_score: dict = field(default_factory=dict)  # 交通评分 {"综合": 8.5, "地铁": 9, ...}
    summary: str = ""  # 交通总结


@dataclass
class WeatherData:
    """天气数据"""
    current: dict = field(default_factory=dict)  # 当前天气
    forecast: List[dict] = field(default_factory=list)  # 天气预报
    business_impact: str = ""  # 对经营的影响分析


@dataclass
class POIAnalysis:
    """POI 分析结果"""
    poi_counts: dict = field(default_factory=dict)  # 各类型 POI 数量
    poi_details: List[dict] = field(default_factory=list)  # POI 详情
    poi_summary: str = ""  # POI 分析总结


@dataclass
class ChartData:
    """图表数据"""
    competitor_chart: dict = field(default_factory=dict)
    poi_chart: dict = field(default_factory=dict)
    traffic_chart: dict = field(default_factory=dict)


class AgentState(TypedDict, total=False):
    """
    LangGraph Agent 状态定义
    
    包含店铺分析所需的所有状态字段
    """
    # 输入参数
    store_name: str  # 店铺名称
    store_address: str  # 店铺地址
    store_type: str  # 店铺类型
    analysis_radius: int  # 分析半径（米）
    
    # 分析结果
    location: Optional[LocationInfo]  # 位置信息
    competitors: Optional[List[CompetitorInfo]]  # 竞争对手列表
    traffic: Optional[TrafficInfo]  # 交通信息
    weather: Optional[WeatherData]  # 天气数据
    poi_analysis: Optional[POIAnalysis]  # POI 分析
    charts: Optional[ChartData]  # 图表数据
    
    # 深度分析结果 (CompeteAI 理论框架)
    competition_analysis: Optional[dict]  # 深度竞争分析结果
    
    # 输出
    final_report: Optional[str]  # 最终报告（Markdown 格式）
    
    # 错误追踪
    errors: List[str]


def create_initial_state(
    store_name: str,
    store_address: str,
    store_type: str = "餐厅",
    analysis_radius: int = 1000
) -> AgentState:
    """
    创建初始状态
    
    Args:
        store_name: 店铺名称
        store_address: 店铺地址
        store_type: 店铺类型
        analysis_radius: 分析半径（米）
        
    Returns:
        AgentState: 初始化的状态字典
    """
    return AgentState(
        store_name=store_name,
        store_address=store_address,
        store_type=store_type,
        analysis_radius=analysis_radius,
        location=None,
        competitors=None,
        traffic=None,
        weather=None,
        poi_analysis=None,
        charts=None,
        competition_analysis=None,
        final_report=None,
        errors=[]
    )
