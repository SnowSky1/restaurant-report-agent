"""
LangGraph 工作流定义

定义餐饮店经营分析的完整工作流
"""

import asyncio
from typing import Any

from langgraph.graph import END, StateGraph

from nodes.chart import chart_node
from nodes.competition_analysis import competition_analysis_node
from nodes.competitor import competitor_node
from nodes.location import location_node
from nodes.poi import poi_node
from nodes.report import report_node
from nodes.revenue_simulation import revenue_simulation_node
from nodes.state import AgentState
from nodes.traffic import traffic_node
from nodes.weather import weather_node


def create_agent_graph(amap_tools: Any, llm: Any = None, enable_competition_analysis: bool = False):
    """
    创建 LangGraph 工作流

    工作流结构:
    1. location - 位置解析
    2. parallel_data - 并行数据采集（竞争对手/交通/天气/POI）
    3. competition_analysis - 深度竞争分析（可选）
    4. revenue_simulation - 多智能体定价/营收情景模拟
    5. chart - 图表数据生成
    6. report - 报告生成

    Args:
        amap_tools: 高德地图工具实例
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
            return_exceptions=True,
        )

        # 合并结果
        merged = dict(state)
        initial_errors = list(state.get("errors", []))
        errors = list(initial_errors)

        for r in results:
            if isinstance(r, dict):
                # 合并非空结果
                for k, v in r.items():
                    if k == "errors" and isinstance(v, list):
                        for error in v:
                            if error not in initial_errors and error not in errors:
                                errors.append(error)
                    elif v is not None:
                        merged[k] = v
            elif isinstance(r, Exception):
                print(f"⚠️ 并行任务异常: {r}")
                errors.append(str(r))

        merged["errors"] = errors
        merged["workflow_status"] = "degraded" if errors else "running"
        if hasattr(amap_tools, "provenance"):
            merged["provenance"] = amap_tools.provenance()
        print("✓ 数据采集完成")

        return merged

    async def _chart_node(state: AgentState) -> dict:
        """图表生成节点包装"""
        return await chart_node(state)

    def _route_after_location(state: AgentState) -> str:
        return "continue" if state.get("location") else "failed"

    async def _competition_analysis_node(state: AgentState) -> dict:
        """深度竞争分析节点包装"""
        return await competition_analysis_node(state, llm)

    async def _revenue_simulation_node(state: AgentState) -> dict:
        """CompeteAI-inspired multi-agent market simulation."""
        return await revenue_simulation_node(state)

    async def _report_node(state: AgentState) -> dict:
        """报告生成节点包装；一次工作流至多进行一次 LLM 调用。"""
        # 深度分析已经让 LLM 解释过竞争证据，报告阶段复用结构化
        # 结果并采用确定性总结，避免重复调用将接口时延放大一倍。
        report_llm = None if enable_competition_analysis else llm
        return await report_node(state, report_llm)

    # 创建工作流图
    workflow = StateGraph(AgentState)

    # 添加节点
    workflow.add_node("location", _location_node)
    workflow.add_node("parallel_data", _parallel_data_node)
    workflow.add_node("revenue_simulation", _revenue_simulation_node)
    workflow.add_node("chart", _chart_node)
    workflow.add_node("report", _report_node)

    # 设置入口点
    workflow.set_entry_point("location")

    # 位置是其余节点的可信前置条件；失败时立即停止，避免浪费外部配额。
    workflow.add_conditional_edges(
        "location",
        _route_after_location,
        {"continue": "parallel_data", "failed": END},
    )

    # 根据是否启用深度分析，决定工作流路径
    if enable_competition_analysis:
        workflow.add_node("competition_analysis", _competition_analysis_node)
        # 并行数据采集 -> 深度竞争分析 -> 营收模拟
        workflow.add_edge("parallel_data", "competition_analysis")
        workflow.add_edge("competition_analysis", "revenue_simulation")
    else:
        workflow.add_edge("parallel_data", "revenue_simulation")

    # 恢复历史确认过但后来丢失的 chart -> report 路径
    workflow.add_edge("revenue_simulation", "chart")
    workflow.add_edge("chart", "report")
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
    │ revenue_simulat.│  定价/营收多智能体模拟
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │      chart      │  图表数据生成
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
    │ revenue_simulat.│  定价/营收情景模拟
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │      chart      │  图表数据生成
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
