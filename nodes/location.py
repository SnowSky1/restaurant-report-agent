"""Resolve an address or user-selected coordinates into a location."""

from __future__ import annotations

from typing import Any

from .state import AgentState, LocationInfo


def _string_value(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return next((str(item) for item in value if item), "")
    return str(value) if value else ""


async def location_node(state: AgentState, amap_tools: Any) -> dict:
    errors = list(state.get("errors", []))
    address = state.get("store_address", "")
    coordinates = state.get("input_coordinates")

    try:
        source = "unknown"
        formatted_address = address
        city = district = business_area = adcode = ""

        if coordinates:
            regeo = await amap_tools.reverse_geocode(coordinates)
            source = regeo.get("_meta", {}).get("source", "unknown")
            regeocode = regeo.get("regeocode", {})
            component = regeocode.get("addressComponent", {})
            formatted_address = regeocode.get("formatted_address") or address
            city = _string_value(component.get("city") or component.get("province"))
            district = _string_value(component.get("district"))
            adcode = _string_value(component.get("adcode"))
            areas = component.get("businessAreas") or []
            if areas:
                business_area = areas[0].get("name", "")
        else:
            result = await amap_tools.geocode(address)
            source = result.get("_meta", {}).get("source", "unknown")
            geocodes = result.get("geocodes") or []
            if not geocodes:
                raise ValueError(f"无法解析地址：{address}")
            geocode = geocodes[0]
            coordinates = geocode.get("location", "")
            formatted_address = geocode.get("formatted_address") or address
            city = _string_value(geocode.get("city") or geocode.get("province"))
            district = _string_value(geocode.get("district"))
            business_area = _string_value(geocode.get("business_area"))
            adcode = _string_value(geocode.get("adcode"))

            if coordinates and (not business_area or not adcode):
                regeo = await amap_tools.reverse_geocode(coordinates)
                regeocode = regeo.get("regeocode", {})
                component = regeocode.get("addressComponent", {})
                city = city or _string_value(component.get("city") or component.get("province"))
                district = district or _string_value(component.get("district"))
                adcode = adcode or _string_value(component.get("adcode"))
                areas = component.get("businessAreas") or []
                if not business_area and areas:
                    business_area = areas[0].get("name", "")

        if not coordinates:
            raise ValueError("位置服务没有返回坐标")

        return {
            "location": LocationInfo(
                coordinates=coordinates,
                address=formatted_address,
                business_area=business_area,
                district=district,
                city=city,
                adcode=adcode,
                source=source,
            ),
            "errors": errors,
        }
    except Exception as error:
        errors.append(f"位置解析失败：{error}")
        return {"location": None, "errors": errors}
