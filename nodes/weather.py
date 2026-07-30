"""Weather and weather-to-operations impact analysis."""

from __future__ import annotations

from typing import Any

from .state import AgentState, WeatherData


async def weather_node(state: AgentState, amap_tools: Any) -> dict:
    errors = list(state.get("errors", []))
    location = state.get("location")
    if not location:
        errors.append("缺少位置信息，无法获取天气")
        return {"weather": None, "errors": errors}

    try:
        city_key = location.adcode or location.city or location.district
        result = await amap_tools.get_weather(city_key)
        lives = result.get("lives") or []
        forecasts = result.get("forecasts") or []
        current = _normalize_live(lives[0]) if lives else {}
        casts = forecasts[0].get("casts", []) if forecasts else []
        if not current and casts:
            first = casts[0]
            current = {
                "weather": first.get("dayweather", ""),
                "temperature": first.get("daytemp", ""),
                "wind_direction": first.get("daywind", ""),
                "wind_power": first.get("daypower", ""),
                "humidity": "",
                "report_time": forecasts[0].get("reporttime", ""),
            }
        return {
            "weather": WeatherData(
                current=current,
                forecast=casts,
                business_impact=_analyze_weather_impact(current),
            ),
            "errors": errors,
        }
    except Exception as error:
        errors.append(f"天气查询失败：{error}")
        return {"weather": None, "errors": errors}


def _normalize_live(live: dict[str, Any]) -> dict[str, Any]:
    return {
        "weather": live.get("weather", ""),
        "temperature": live.get("temperature", ""),
        "wind_direction": live.get("winddirection", ""),
        "wind_power": live.get("windpower", ""),
        "humidity": live.get("humidity", ""),
        "report_time": live.get("reporttime", ""),
    }


def _analyze_weather_impact(weather: dict[str, Any]) -> str:
    if not weather:
        return "天气信息不足，建议按常规客流计划经营"
    weather_type = str(weather.get("weather") or "")
    impacts: list[str] = []
    if any(word in weather_type for word in ("雨", "雪", "暴")):
        impacts.extend(["堂食自然客流可能下降", "建议提升外卖运力并准备恶劣天气优惠"])
    elif any(word in weather_type for word in ("晴", "多云")):
        impacts.append("天气适合出行，有利于到店客流")
    try:
        temperature = float(weather.get("temperature"))
        if temperature >= 32:
            impacts.append("高温时冷饮、遮阳和室内舒适度更关键")
        elif temperature <= 8:
            impacts.append("低温时热饮、热食和保温配送需求增加")
    except (TypeError, ValueError):
        pass
    return "；".join(impacts) if impacts else "天气影响相对中性"
