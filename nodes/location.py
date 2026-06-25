"""
位置解析节点

负责将店铺地址转换为经纬度坐标，并获取商圈信息
"""

from typing import Any
from .state import AgentState, LocationInfo


async def location_node(state: AgentState, amap_tools: Any) -> dict:
    """
    位置解析节点
    
    1. 地理编码：地址 -> 坐标
    2. 逆地理编码：获取商圈等详细信息
    
    Args:
        state: 当前状态
        amap_tools: 高德地图工具实例
        
    Returns:
        dict: 更新后的状态字段
    """
    print(f"📍 正在解析位置: {state['store_address']}")
    
    errors = list(state.get("errors", []))
    
    try:
        # 1. 地理编码
        geo_result = await amap_tools.geocode(state["store_address"])
        
        if geo_result.get("status") != "1" or not geo_result.get("geocodes"):
            errors.append(f"地理编码失败: {state['store_address']}")
            return {"errors": errors}
        
        geocode = geo_result["geocodes"][0]
        coordinates = geocode.get("location", "")
        city = geocode.get("city", "")
        district = geocode.get("district", "")
        formatted_address = geocode.get("formatted_address", state["store_address"])
        
        # 2. 逆地理编码获取商圈信息
        business_area = ""
        if coordinates:
            try:
                regeo_result = await amap_tools.reverse_geocode(coordinates)
                if regeo_result.get("status") == "1":
                    regeocode = regeo_result.get("regeocode", {})
                    address_component = regeocode.get("addressComponent", {})
                    business_areas = address_component.get("businessAreas", [])
                    if business_areas:
                        business_area = business_areas[0].get("name", "")
            except Exception as e:
                print(f"⚠️ 逆地理编码失败: {e}")
        
        location_info = LocationInfo(
            coordinates=coordinates,
            address=formatted_address,
            business_area=business_area,
            district=district,
            city=city if isinstance(city, str) else ""
        )
        
        print(f"✓ 位置解析完成: {coordinates} ({business_area or district})")
        
        return {
            "location": location_info,
            "errors": errors
        }
        
    except Exception as e:
        errors.append(f"位置解析异常: {str(e)}")
        print(f"❌ 位置解析失败: {e}")
        return {"errors": errors}
