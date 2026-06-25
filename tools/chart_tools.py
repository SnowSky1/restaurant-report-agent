from typing import Dict, Any
from mcp_client.client import MCPClient

class ChartTools:
    """可视化图表工具封装"""
    
    def __init__(self, mcp_url: str):
        self.client = MCPClient(sse_url=mcp_url)
        
    async def initialize(self):
        await self.client.initialize()
        
    async def close(self):
        await self.client.close()
        
    async def create_bar_chart(self, data: list, title: str) -> Dict[str, Any]:
        # 实际开发中调用 @antvis/mcp-server-chart 的相应工具
        return await self.client.call_tool("chart_bar", {"data": data, "title": title})
        
    async def create_pie_chart(self, data: list, title: str) -> Dict[str, Any]:
        return await self.client.call_tool("chart_pie", {"data": data, "title": title})
