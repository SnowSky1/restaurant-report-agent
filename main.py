"""
餐饮店经营分析智能体 - 主入口

使用 LangGraph 框架，集成高德地图 MCP 和可视化图表 MCP 服务，
自动生成包含竞争对手分析、交通便利性、天气影响、商业环境等多维度的经营报告。

使用方法:
    python main.py --name "店铺名称" --address "店铺地址" --type "餐厅" --radius 1000

环境变量:
    - LLM_PROVIDER: 选择 LLM 提供商 (openai/deepseek)
    - OPENAI_API_KEY: OpenAI API Key
    - DEEPSEEK_API_KEY: DeepSeek API Key
    - AMAP_MAPS_API_KEY: 高德地图 API Key
"""

import os
import sys
import asyncio
import argparse
from datetime import datetime
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.markdown import Markdown

from config.settings import settings
from tools.amap_tools import AmapTools
from tools.chart_tools import ChartTools
from graph.agent import create_agent_graph
from nodes.state import create_initial_state


# 加载环境变量
load_dotenv()

console = Console()


def get_llm():
    """获取 LLM 实例"""
    llm_config = settings.get_llm_config()
    
    if llm_config["provider"] == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            api_key=llm_config["api_key"],
            model=llm_config["model"],
        )
    else:  # deepseek 或 siliconflow (兼容 OpenAI API)
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            api_key=llm_config["api_key"],
            base_url=llm_config["base_url"],
            model=llm_config["model"],
        )


async def run_analysis(
    store_name: str,
    store_address: str,
    store_type: str = "餐厅",
    analysis_radius: int = 1000,
    output_file: str = None,
    use_llm: bool = True,
    deep_analysis: bool = False,
    location: str = None
) -> tuple[str, dict]:
    """
    运行店铺经营分析
    
    Args:
        store_name: 店铺名称
        store_address: 店铺地址
        store_type: 店铺类型
        analysis_radius: 分析半径（米）
        output_file: 输出文件路径
        use_llm: 是否使用 LLM 增强
        deep_analysis: 是否启用深度竞争分析 (借鉴 CompeteAI 理论)
        
    Returns:
        str: 生成的报告内容
    """
    deep_analysis_text = "\n深度分析: ✓ 已启用 (自研 CompeteAI)" if deep_analysis else ""
    console.print(Panel.fit(
        f"[bold blue]🏪 餐饮店经营分析智能体[/bold blue]\n\n"
        f"店铺名称: {store_name}\n"
        f"店铺地址: {store_address}\n"
        f"店铺类型: {store_type}\n"
        f"分析半径: {analysis_radius}米{deep_analysis_text}",
        title="分析任务"
    ))
    
    # 验证配置
    errors = settings.validate_config()
    if errors:
        for error in errors:
            console.print(f"[red]❌ 配置错误: {error}[/red]")
        console.print("\n[yellow]请检查 .env 文件中的配置[/yellow]")
        return "", {}
    
    # 初始化工具
    amap_tools = AmapTools(
        mcp_url=settings.amap_mcp_url,
        api_key=settings.amap_maps_api_key
    )
    
    chart_tools = ChartTools(
        mcp_url=settings.chart_mcp_url
    )
    
    # 初始化 LLM（可选）
    llm = None
    if use_llm:
        try:
            llm = get_llm()
            console.print(f"[green]✓ LLM 已加载 ({settings.llm_provider})[/green]")
        except Exception as e:
            console.print(f"[yellow]⚠ LLM 加载失败: {e}[/yellow]")
    
    # 创建工作流
    graph = create_agent_graph(
        amap_tools=amap_tools,
        chart_tools=chart_tools,
        llm=llm,
        enable_competition_analysis=deep_analysis
    )
    
    # 创建初始状态
    initial_state = create_initial_state(
        store_name=store_name,
        store_address=store_address,
        store_type=store_type,
        analysis_radius=analysis_radius
    )
    
    # 增加对传入 location 的处理支持
    # (修改 create_initial_state 或者在创建后直接更新)
    
    # 运行分析
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]正在分析...", total=None)
        
        # 如果用户直接传入了 location (经纬度)
        if location:
            initial_state["location"] = {"coordinates": location, "address": store_address, "business_area": ""}
            
        try:
            # 执行工作流
            progress.update(task, description="[cyan]📍 解析店铺位置...")
            final_state = await graph.ainvoke(initial_state)
            
            progress.update(task, description="[green]✓ 分析完成!")
            
        except Exception as e:
            console.print(f"[red]❌ 分析失败: {e}[/red]")
            return "", {}
        finally:
            # 清理资源
            await amap_tools.close()
            await chart_tools.close()
    
    # 获取报告
    report = final_state.get("final_report", "")
    
    if not report:
        console.print("[red]❌ 报告生成失败[/red]")
        if errors:
            for error in final_state["errors"]:
                console.print(f"  - {error}")
        return "", final_state
    
    # 保存报告
    if output_file:
        output_path = Path(output_file)
    else:
        # 默认保存到 reports 目录
        output_dir = Path(settings.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # 使用安全的文件名（避免中文编码问题）
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in store_name)
        if not safe_name or safe_name == "_" * len(safe_name):
            safe_name = "report"
        output_path = output_dir / f"{safe_name}_{timestamp}.md"
    
    # 增加确保 output_dir 存在的方法，因为如果是命令行运行可能路径不存在
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
    console.print(f"\n[green]✓ 报告已保存到: {output_path}[/green]")
    
    # 显示报告预览
    console.print("\n")
    console.print(Panel(
        Markdown(report[:2000] + "\n\n..." if len(report) > 2000 else report),
        title="[bold]报告预览[/bold]",
        border_style="blue"
    ))
    
    # 将 final_state 一并返回给 API 使用
    return report, final_state


def main():
    """命令行入口"""
    parser = argparse.ArgumentParser(
        description="餐饮店经营分析智能体",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py --name "星巴克咖啡" --address "北京市朝阳区建国路88号" --type "咖啡店"
  python main.py --name "海底捞火锅" --address "上海市浦东新区陆家嘴" --type "火锅店" --radius 1500
        """
    )
    
    parser.add_argument(
        "--name", "-n",
        required=True,
        help="店铺名称"
    )
    
    parser.add_argument(
        "--address", "-a",
        required=True,
        help="店铺地址"
    )
    
    parser.add_argument(
        "--type", "-t",
        default="餐厅",
        choices=["餐厅", "咖啡店", "奶茶店", "火锅店", "烧烤店", "快餐店", "面馆", "西餐厅", "日料店", "韩餐厅", "川菜馆", "粤菜馆", "甜品店", "面包店"],
        help="店铺类型 (默认: 餐厅)"
    )
    
    parser.add_argument(
        "--radius", "-r",
        type=int,
        default=1000,
        help="分析半径，单位米 (默认: 1000)"
    )
    
    parser.add_argument(
        "--output", "-o",
        help="输出文件路径 (默认: ./reports/店铺名_时间戳.md)"
    )
    
    parser.add_argument(
        "--no-llm",
        action="store_true",
        help="不使用 LLM 增强总结"
    )
    
    parser.add_argument(
        "--deep-analysis", "-d",
        action="store_true",
        help="启用深度竞争分析 (自研 CompeteAI 理论框架)"
    )
    
    args = parser.parse_args()
    
    # 运行分析
    report, _ = asyncio.run(run_analysis(
        store_name=args.name,
        store_address=args.address,
        store_type=args.type,
        analysis_radius=args.radius,
        output_file=args.output,
        use_llm=not args.no_llm,
        deep_analysis=args.deep_analysis
    ))


if __name__ == "__main__":
    main()
