"""
报告生成节点

汇总所有分析数据，生成完整的 Markdown 格式报告
"""

from typing import Any, Optional
from datetime import datetime
from .state import AgentState


async def report_node(state: AgentState, llm: Any = None) -> dict:
    """
    报告生成节点
    
    汇总所有分析结果，生成 Markdown 报告
    支持 LLM 增强生成更智能的总结和建议
    
    Args:
        state: 当前状态
        llm: LLM 实例（可选，用于生成智能总结）
        
    Returns:
        dict: 包含最终报告的状态更新
    """
    print(f"📝 正在生成分析报告...")
    
    errors = list(state.get("errors", []))
    
    # 基础报告结构
    report_sections = []
    
    # 标题
    store_name = state.get("store_name", "未知店铺")
    report_sections.append(f"# {store_name} 经营分析报告\n")
    report_sections.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # 一、基本信息
    report_sections.append(_build_basic_info_section(state))
    
    # 二、位置分析
    report_sections.append(_build_location_section(state))
    
    # 三、竞争对手分析
    report_sections.append(_build_competitor_section(state))
    
    # 四、交通便利性分析
    report_sections.append(_build_traffic_section(state))
    
    # 五、天气影响分析
    report_sections.append(_build_weather_section(state))
    
    # 六、商业环境分析
    report_sections.append(_build_poi_section(state))
    
    # 七、深度竞争分析（如果有）
    if state.get("competition_analysis"):
        report_sections.append(_build_competition_analysis_section(state))
    
    # 八、综合建议
    if llm:
        try:
            summary = await _generate_llm_summary(state, llm)
            report_sections.append(summary)
        except Exception as e:
            print(f"⚠️ LLM 总结生成失败: {e}")
            report_sections.append(_build_basic_summary(state))
    else:
        report_sections.append(_build_basic_summary(state))
    
    final_report = "\n".join(report_sections)
    
    print(f"✓ 报告生成完成，共 {len(final_report)} 字符")
    
    return {
        "final_report": final_report,
        "errors": errors
    }


def _build_basic_info_section(state: AgentState) -> str:
    """构建基本信息部分"""
    return f"""
## 一、基本信息

| 项目 | 内容 |
|------|------|
| 店铺名称 | {state.get('store_name', '-')} |
| 店铺地址 | {state.get('store_address', '-')} |
| 店铺类型 | {state.get('store_type', '-')} |
| 分析半径 | {state.get('analysis_radius', 1000)} 米 |
"""


def _build_location_section(state: AgentState) -> str:
    """构建位置分析部分"""
    location = state.get("location")
    if not location:
        return "\n## 二、位置分析\n\n暂无位置信息\n"
    
    return f"""
## 二、位置分析

- **坐标**: {location.coordinates}
- **格式化地址**: {location.address}
- **所属商圈**: {location.business_area or '未知'}
- **所在区域**: {location.district or location.city or '未知'}
"""


def _build_competitor_section(state: AgentState) -> str:
    """构建竞争对手分析部分"""
    competitors = state.get("competitors", [])
    if not competitors:
        return "\n## 三、竞争对手分析\n\n周边未发现同类竞争对手\n"
    
    section = f"\n## 三、竞争对手分析\n\n共发现 **{len(competitors)}** 家同类店铺\n\n"
    section += "| 店铺名称 | 距离 | 评分 |\n|----------|------|------|\n"
    
    for comp in competitors[:10]:
        name = comp.name if hasattr(comp, 'name') else comp.get('name', '-')
        distance = comp.distance if hasattr(comp, 'distance') else comp.get('distance', '-')
        rating = comp.rating if hasattr(comp, 'rating') else comp.get('rating', '-')
        section += f"| {name} | {distance}米 | {rating or '-'} |\n"
    
    if len(competitors) > 10:
        section += f"\n*（仅显示前 10 家，共 {len(competitors)} 家）*\n"
    
    return section


def _build_traffic_section(state: AgentState) -> str:
    """构建交通分析部分"""
    traffic = state.get("traffic")
    if not traffic:
        return "\n## 四、交通便利性分析\n\n暂无交通信息\n"
    
    scores = traffic.traffic_score if hasattr(traffic, 'traffic_score') else {}
    subway = traffic.subway_stations if hasattr(traffic, 'subway_stations') else []
    bus = traffic.bus_stations if hasattr(traffic, 'bus_stations') else []
    parking = traffic.parking_lots if hasattr(traffic, 'parking_lots') else []
    summary = traffic.summary if hasattr(traffic, 'summary') else ""
    
    section = f"""
## 四、交通便利性分析

### 交通评分

| 类型 | 评分 |
|------|------|
| 地铁 | {scores.get('地铁', '-')}/10 |
| 公交 | {scores.get('公交', '-')}/10 |
| 停车 | {scores.get('停车', '-')}/10 |
| **综合** | **{scores.get('综合', '-')}/10** |

### 交通设施

- 地铁站: {len(subway)} 个
- 公交站: {len(bus)} 个
- 停车场: {len(parking)} 个

### 总结

{summary}
"""
    return section


def _build_weather_section(state: AgentState) -> str:
    """构建天气分析部分"""
    weather = state.get("weather")
    if not weather:
        return "\n## 五、天气影响分析\n\n暂无天气信息\n"
    
    current = weather.current if hasattr(weather, 'current') else {}
    impact = weather.business_impact if hasattr(weather, 'business_impact') else ""
    
    return f"""
## 五、天气影响分析

### 当前天气

- **天气**: {current.get('weather', '-')}
- **温度**: {current.get('temperature', '-')}°C
- **风向**: {current.get('wind_direction', '-')}
- **风力**: {current.get('wind_power', '-')}级
- **湿度**: {current.get('humidity', '-')}%

### 经营影响

{impact}
"""


def _build_poi_section(state: AgentState) -> str:
    """构建商业环境分析部分"""
    poi_analysis = state.get("poi_analysis")
    if not poi_analysis:
        return "\n## 六、商业环境分析\n\n暂无 POI 信息\n"
    
    poi_counts = poi_analysis.poi_counts if hasattr(poi_analysis, 'poi_counts') else {}
    poi_summary = poi_analysis.poi_summary if hasattr(poi_analysis, 'poi_summary') else ""
    
    section = "\n## 六、商业环境分析\n\n### POI 分布\n\n"
    section += "| 类型 | 数量 |\n|------|------|\n"
    
    for poi_type, count in poi_counts.items():
        section += f"| {poi_type} | {count} |\n"
    
    section += f"\n### 分析总结\n\n{poi_summary}\n"
    
    return section


def _build_competition_analysis_section(state: AgentState) -> str:
    """构建深度竞争分析部分"""
    analysis = state.get("competition_analysis", {})
    if not analysis:
        return ""
    
    section = "\n## 七、深度竞争分析（CompeteAI）\n\n"
    
    # 竞争强度
    intensity = analysis.get("competition_intensity", {})
    if intensity:
        section += f"### 竞争强度\n\n"
        section += f"- **整体评级**: {intensity.get('level', '-')}\n"
        section += f"- **评分**: {intensity.get('score', '-')}/10\n"
        section += f"- **说明**: {intensity.get('description', '-')}\n\n"
    
    # 市场定位
    position = analysis.get("market_position", {})
    if position:
        section += f"### 市场定位\n\n"
        section += f"- **建议定位**: {position.get('recommended', '-')}\n"
        section += f"- **差异化方向**: {position.get('differentiation', '-')}\n\n"
    
    # 竞争威胁
    threats = analysis.get("competitive_threats", [])
    if threats:
        section += "### 竞争威胁\n\n"
        for threat in threats[:5]:
            if isinstance(threat, dict):
                section += f"- **{threat.get('threat', '-')}** ({threat.get('severity', '-')}): {threat.get('source', '-')}\n"
            else:
                section += f"- {threat}\n"
        section += "\n"
    
    # 差异化机会
    opportunities = analysis.get("differentiation_opportunities", [])
    if opportunities:
        section += "### 差异化机会\n\n"
        for opp in opportunities[:5]:
            if isinstance(opp, dict):
                section += f"- **{opp.get('opportunity', '-')}**: {opp.get('implementation', '-')}\n"
            else:
                section += f"- {opp}\n"
        section += "\n"
    
    # 定价策略
    pricing = analysis.get("pricing_strategy", {})
    if pricing:
        section += f"### 定价策略建议\n\n"
        section += f"- **当前评估**: {pricing.get('current_assessment', '-')}\n"
        section += f"- **建议**: {pricing.get('recommendation', '-')}\n\n"
    
    # 行动计划
    action_plan = analysis.get("action_plan", [])
    if action_plan:
        section += "### 行动计划\n\n"
        section += "| 优先级 | 行动 | 时间线 | 预期ROI |\n|--------|------|--------|--------|\n"
        for action in action_plan[:5]:
            if isinstance(action, dict):
                section += f"| {action.get('priority', '-')} | {action.get('action', '-')} | {action.get('timeline', '-')} | {action.get('expected_roi', '-')} |\n"
        section += "\n"
    
    return section


def _build_basic_summary(state: AgentState) -> str:
    """构建基础总结"""
    return """
## 八、综合建议

基于以上分析，建议关注以下方面：

1. **竞争策略**: 根据周边竞争对手情况，制定差异化经营策略
2. **营销重点**: 结合商业环境特点，针对主要客群进行精准营销
3. **运营优化**: 根据交通和天气情况，优化营业时间和服务方式
4. **长期规划**: 持续关注区域发展动态，把握市场机会

---
*报告由餐饮店经营分析智能体自动生成*
"""


async def _generate_llm_summary(state: AgentState, llm) -> str:
    """使用 LLM 生成智能总结"""
    # 构建上下文
    context_parts = []
    
    context_parts.append(f"店铺: {state.get('store_name')} ({state.get('store_type')})")
    context_parts.append(f"地址: {state.get('store_address')}")
    
    competitors = state.get("competitors", [])
    context_parts.append(f"竞争对手: {len(competitors)} 家")
    
    traffic = state.get("traffic")
    if traffic and hasattr(traffic, 'traffic_score'):
        score = traffic.traffic_score.get('综合', 'N/A')
        context_parts.append(f"交通评分: {score}/10")
    
    poi = state.get("poi_analysis")
    if poi and hasattr(poi, 'poi_summary'):
        context_parts.append(f"商业环境: {poi.poi_summary}")
    
    weather = state.get("weather")
    if weather and hasattr(weather, 'current'):
        w = weather.current.get('weather', '')
        context_parts.append(f"天气: {w}")
    
    context = "\n".join(context_parts)
    
    prompt = f"""基于以下餐饮店铺分析数据，请生成一份专业的经营建议总结（200-300字）：

{context}

请从以下角度给出具体、可操作的建议：
1. 市场定位与差异化策略
2. 目标客群与营销建议
3. 运营优化方向
4. 风险提示与应对措施

使用 Markdown 格式输出，以"## 八、综合建议"作为标题。"""

    try:
        response = await llm.ainvoke(prompt)
        content = response.content if hasattr(response, 'content') else str(response)
        return f"\n{content}\n"
    except Exception as e:
        print(f"⚠️ LLM 调用失败: {e}")
        return _build_basic_summary(state)
