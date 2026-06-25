from typing import Dict, Any, List
from mcp_client.client import MCPClient

class AmapTools:
    """高德地图工具封装"""
    
    def __init__(self, mcp_url: str, api_key: str):
        self.client = MCPClient(sse_url=mcp_url, api_key=api_key)
        
    async def initialize(self):
        await self.client.initialize()
        
    async def close(self):
        await self.client.close()
        
    async def geocode(self, address: str, city: str = None) -> Dict[str, Any]:
        """地理编码：地址转坐标"""
        args = {"address": address}
        if city:
            args["city"] = city
        return await self.client.call_tool("maps_geo", args)
        
    async def reverse_geocode(self, location: str, radius: int = 1000) -> Dict[str, Any]:
        """逆地理编码：坐标转地址/商圈"""
        args = {
            "location": location,
            "radius": str(radius),
            "extensions": "all"
        }
        return await self.client.call_tool("maps_regeo", args)
        
    async def search_around(self, location: str, keywords: str, types: str = "", radius: int = 1000) -> Dict[str, Any]:
        """周边搜索"""
        args = {
            "location": location,
            "keywords": keywords,
            "types": types,
            "radius": str(radius)
        }
        return await self.client.call_tool("maps_search_around", args)
        
    async def get_weather(self, city: str) -> Dict[str, Any]:
        """查询天气"""
        args = {
            "city": city,
            "extensions": "base"
        }
        return await self.client.call_tool("maps_weather", args)
