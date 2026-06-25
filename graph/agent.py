"""
LangGraph 工作流定义

定义餐饮店经营分析的完整工作流
"""

import asyncio
from typing import Any, Optional
from langgraph.graph import StateGraph, END

from nodes.state import AgentState
from nodes.location import location_node
from nodes.competitor import competitor_node
from nodes.traffic import traffic_node
from nodes.weather import weather_node
from nodes.poi import poi_node
from nodes.chart import chart_node
from nodes.report import report_node
from nodes.competition_analysis import competition_analysis_node


def create_agent_graph(
    amap_tools: Any,
    chart_tools: Any = None,
    llm: Any = None,
    enable_competition_analysis: bool = False
):
    """
    创建 LangGraph 工作流
    
    工作流结构:
    1. location - 位置解析
    2. parallel_data - 并行数据采集（竞争对手/交通/天气/POI）
    3. competition_analysis - 深度竞争分析（可选）
    4. report - 报告生成
    
    Args:
        amap_tools: 高德地图工具实例
        chart_tools: 图表工具实例（可选）
        llm: LLM 实例（用于智能总结和深度分析）
        enable_competition_analysis: 是否启用深度竞争分析
        
    Returns:
        CompiledGraph: 编译后的工作流
    """
    
    # 创建闭包节点函数
    async def _location_node(state: AgentState) -> dict:
        """位置解析节点包装"""
        return await location_node(state, amap_tools)
    
    async def _parallel_data_node(state: AgentState) -> dict:
        """
        并行数据采集节点
        
        同时执行竞争对手、交通、天气、POI 分析
        显著提升整体执行效率
        """
        print("⚡ 并行采集数据中...")
        
        # 并行执行所有数据采集任务
        results = await asyncio.gather(
            competitor_node(state, amap_tools),
            traffic_node(state, amap_tools),
            weather_node(state, amap_tools),
            poi_node(state, amap_tools),
            return_exceptions=True
        )
        
        # 合并结果
        merged = dict(state)
        errors = list(state.get("errors", []))
        
        for r in results:
            if isinstance(r, dict):
                # 合并非空结果
                for k, v in r.items():
                    if k == "errors" and isinstance(v, list):
                        errors.extend(v)
                    elif v is not None:
                        merged[k] = v
            elif isinstance(r, Exception):
                print(f"⚠️ 并行任务异常: {r}")
                errors.append(str(r))
        
        merged["errors"] = errors
        print("✓ 数据采集完成")
        
        return merged
    
    async def _chart_node(state: AgentState) -> dict:
        """图表生成节点包装"""
        return await chart_node(state, chart_tools)
    
    async def _competition_analysis_node(state: AgentState) -> dict:
        """深度竞争分析节点包装"""
        return await competition_analysis_node(state, llm)
    
    async def _report_node(state: AgentState) -> dict:
        """报告生成节点包装"""
        return await report_node(state, llm)
    
    # 创建工作流图
    workflow = StateGraph(AgentState)
    
    # 添加节点
    workflow.add_node("location", _location_node)
    workflow.add_node("parallel_data", _parallel_data_node)
    workflow.add_node("report", _report_node)
    
    # 设置入口点
    workflow.set_entry_point("location")
    
    # 位置解析 -> 并行数据采集
    workflow.add_edge("location", "parallel_data")
    
    # 根据是否启用深度分析，决定工作流路径
    if enable_competition_analysis:
        workflow.add_node("competition_analysis", _competition_analysis_node)
        # 并行数据采集 -> 深度竞争分析 -> 报告生成
        workflow.add_edge("parallel_data", "competition_analysis")
        workflow.add_edge("competition_analysis", "report")
    else:
        # 并行数据采集 -> 报告生成
        workflow.add_edge("parallel_data", "report")
    
    # 报告生成 -> 结束
    workflow.add_edge("report", END)
    
    # 编译工作流
    return workflow.compile()


def get_graph_structure(enable_competition_analysis: bool = False) -> str:
    """
    获取图结构的文本描述
    
    Args:
        enable_competition_analysis: 是否包含深度分析节点
        
    Returns:
        str: 图结构描述
    """
    if enable_competition_analysis:
        return """
LangGraph 工作流结构（含深度分析）:

    ┌─────────────────┐
    │     START       │
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │    location     │  位置解析
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │  parallel_data  │  并行数据采集
    │  ┌───────────┐  │  ├── competitor
    │  │ asyncio   │  │  ├── traffic
    │  │ .gather() │  │  ├── weather
    │  └───────────┘  │  └── poi
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │  competition    │  深度竞争分析
    │  _analysis      │  (CompeteAI)
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │     report      │  报告生成
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │      END        │
    └─────────────────┘
"""
    else:
        return """
LangGraph 工作流结构:

    ┌─────────────────┐
    │     START       │
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │    location     │  位置解析
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │  parallel_data  │  并行数据采集
    │  ┌───────────┐  │  ├── competitor
    │  │ asyncio   │  │  ├── traffic
    │  │ .gather() │  │  ├── weather
    │  └───────────┘  │  └── poi
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │     report      │  报告生成
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │      END        │
    └─────────────────┘
"""
