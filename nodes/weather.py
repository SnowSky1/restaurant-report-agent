"""
天气分析节点

获取天气信息，分析对店铺经营的影响
"""

from typing import Any
from .state import AgentState, WeatherData


async def weather_node(state: AgentState, amap_tools: Any) -> dict:
    """
    天气分析节点
    
    获取当前天气和预报，分析对经营的影响
    
    Args:
        state: 当前状态
        amap_tools: 高德地图工具实例
        
    Returns:
        dict: 包含天气数据的状态更新
    """
    print(f"🌤️ 正在获取天气信息...")
    
    errors = list(state.get("errors", []))
    
    location = state.get("location")
    if not location:
        errors.append("缺少位置信息，无法获取天气")
        return {"weather": None, "errors": errors}
    
    try:
        # 获取城市信息
        city = location.city or location.district or "北京"
        
        # 查询天气
        weather_result = await amap_tools.get_weather(city)
        
        current_weather = {}
        if weather_result.get("lives"):
            live = weather_result["lives"][0]
            current_weather = {
                "weather": live.get("weather", ""),
                "temperature": live.get("temperature", ""),
                "wind_direction": live.get("winddirection", ""),
                "wind_power": live.get("windpower", ""),
                "humidity": live.get("humidity", ""),
                "report_time": live.get("reporttime", "")
            }
        
        # 分析天气对经营的影响
        business_impact = _analyze_weather_impact(current_weather)
        
        weather_data = WeatherData(
            current=current_weather,
            forecast=[],  # 可扩展为多日预报
            business_impact=business_impact
        )
        
        weather_desc = current_weather.get("weather", "未知")
        temp = current_weather.get("temperature", "?")
        print(f"✓ 天气信息获取完成: {weather_desc} {temp}°C")
        
        return {
            "weather": weather_data,
            "errors": errors
        }
        
    except Exception as e:
        errors.append(f"天气查询异常: {str(e)}")
        print(f"❌ 天气查询失败: {e}")
        return {"weather": None, "errors": errors}


def _analyze_weather_impact(weather: dict) -> str:
    """分析天气对经营的影响"""
    if not weather:
        return "无法获取天气信息"
    
    weather_type = weather.get("weather", "")
    temperature = weather.get("temperature", "")
    
    impacts = []
    
    # 根据天气类型分析
    if "雨" in weather_type:
        impacts.append("雨天可能减少街头人流，但增加外卖订单")
        impacts.append("建议加强外卖配送能力，可考虑雨天优惠活动")
    elif "雪" in weather_type:
        impacts.append("雪天出行不便，堂食客流可能下降")
        impacts.append("建议提前备货，关注配送安全")
    elif "晴" in weather_type or "多云" in weather_type:
        impacts.append("天气适宜出行，有利于堂食客流")
    elif "阴" in weather_type:
        impacts.append("阴天对客流影响不大")
    
    # 根据温度分析
    try:
        temp = int(temperature) if temperature else None
        if temp is not None:
            if temp >= 35:
                impacts.append("高温天气，冷饮/空调是吸引顾客的关键")
            elif temp <= 5:
                impacts.append("低温天气，热饮/暖气是顾客关注点")
            elif 20 <= temp <= 28:
                impacts.append("温度舒适，适合户外用餐")
    except (ValueError, TypeError):
        pass
    
    return "；".join(impacts) if impacts else "天气条件一般，正常经营"
