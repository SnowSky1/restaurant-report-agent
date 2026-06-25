# 🏪 餐饮店经营分析智能体

基于 **LangGraph** 框架开发的智能体，集成魔搭社区的 **高德地图 MCP** 和 **可视化图表 MCP** 服务，自动生成包含竞争对手分析、交通便利性、天气影响、商业环境等多维度的餐饮店经营报告。

## ✨ 功能特点

- 🗺️ **位置分析** - 自动解析店铺地址，获取经纬度和商圈信息
- 🏪 **竞争对手分析** - 搜索周边同类餐饮店，分析竞争态势
- 🚌 **交通便利性** - 分析周边公交站、地铁站、停车场分布
- ⛅ **天气影响** - 获取天气预报，分析天气对经营的影响
- 🏢 **商业环境** - 分析周边客源结构（写字楼、住宅、学校等）
- 📊 **数据可视化** - 自动生成各类分析图表
- 📝 **智能报告** - 汇总分析结果，生成完整经营报告
- 🖼️ **Pyppeteer 渲染** - 支持将图表渲染为高清图片
- 📓 **Jupyter 支持** - IPython/Plotly 交互式可视化
- 🔬 **深度竞争分析** - 借鉴 [CompeteAI](https://github.com/microsoft/competeai) 理论框架 (ICML 2024 Oral)

---

## 🔬 CompeteAI 集成

本项目集成了微软研究院 **CompeteAI** 的竞争动态分析理论，提供更深入的竞争态势分析。

### 什么是 CompeteAI?

[CompeteAI](https://github.com/microsoft/competeai) 是微软研究院发表于 **ICML 2024 (Oral)** 的研究项目，研究基于大型语言模型的智能体之间的竞争行为。

### 启用深度竞争分析

```bash
# 使用 --deep-analysis 或 -d 参数启用
python main.py --name "星巴克咖啡" --address "北京市朝阳区建国路88号" --type "咖啡店" --deep-analysis
```

### 深度分析内容

启用后，报告将额外包含：

| 分析维度 | 说明 |
|---------|------|
| **竞争强度评分** | 1-10分量化评估 |
| **市场定位分析** | 当前定位 + 建议定位 |
| **差异化机会** | 可发掘的竞争优势 |
| **定价策略建议** | 基于市场的价格建议 |
| **场景化分析** | 早/午/晚/周末各时段分析 |
| **未来预测** | 新竞争者风险、市场趋势 |
| **行动计划** | 优先级排序的具体建议 |

### 理论基础

CompeteAI 的核心发现：
- LLM 智能体能展现复杂的竞争行为
- 竞争动态与真实市场理论高度一致
- 可观察到纳什均衡、马太效应等经济学现象

---

## 🏗️ 框架设计详解

### 整体架构

本项目采用 **分层架构** 设计，将系统划分为四个核心层次：

```
┌─────────────────────────────────────────────────────────────────┐
│                        用户接口层 (Interface)                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │   CLI 命令行  │  │ Jupyter NB  │  │      Python API        │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                      智能体层 (Agent Layer)                      │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                  LangGraph 工作流引擎                    │    │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐       │     │
│  │  │位置分析 │→│竞争分析 │→│交通分析 │→│天气分析 │→...       │     │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘       │     │
│  └─────────────────────────────────────────────────────────┘    │
├─────────────────────────────────────────────────────────────────┤
│                       工具层 (Tools Layer)                      │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐  │
│  │   AmapTools      │  │   ChartTools     │  │  Visualizer  │  │
│  │   高德地图工具     │  │   图表生成工具    │  │   可视化器    │  │
│  └──────────────────┘  └──────────────────┘  └──────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                      基础设施层 (Infrastructure)                 │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐   │
│  │   MCP Client     │  │   LLM Client     │  │  Pyppeteer   │   │
│  │   SSE 协议客户端  │  │  OpenAI/DeepSeek │  │  浏览器渲染   │    │
│  └──────────────────┘  └──────────────────┘  └──────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                       外部服务 (External Services)               │
│  ┌──────────────────────────┐  ┌──────────────────────────┐     │
│  │   魔搭社区 MCP 服务        │  │      LLM API 服务        │     │
│  │  • 高德地图 MCP           │  │  • OpenAI GPT            │     │
│  │  • 可视化图表 MCP         │  │  • DeepSeek              │     │
│  └──────────────────────────┘  └──────────────────────────┘     │
└─────────────────────────────────────────────────────────────────┘
```

### LangGraph 工作流设计

智能体的核心是基于 **LangGraph** 构建的有向图工作流：

```
                          ┌─────────────┐
                          │   START     │
                          └──────┬──────┘
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │    位置分析节点         │
                    │  (Location Node)       │
                    │  • 地理编码            │
                    │  • 逆地理编码          │
                    │  • 获取商圈信息        │
                    └───────────┬────────────┘
                                │
                    ┌───────────┴───────────┐
                    │  位置解析成功?         │
                    └───────────┬───────────┘
                         Yes    │    No
                    ┌───────────┴───────────┐
                    │                       │
                    ▼                       ▼
        ┌────────────────────┐         ┌────────┐
        │   竞争对手分析节点   │         │  END   │
        │  (Competitor Node) │         └────────┘
        │  • 周边搜索同类店   │
        │  • 距离/评分分析   │
        └─────────┬──────────┘
                  │
                  ▼
        ┌────────────────────┐
        │   交通便利性节点    │
        │  (Traffic Node)    │
        │  • 公交站搜索      │
        │  • 地铁站搜索      │
        │  • 停车场搜索      │
        │  • 便利性评分      │
        └─────────┬──────────┘
                  │
                  ▼
        ┌────────────────────┐
        │   天气分析节点      │
        │  (Weather Node)    │
        │  • 获取天气预报    │
        │  • 分析天气影响    │
        └─────────┬──────────┘
                  │
                  ▼
        ┌────────────────────┐
        │   商业环境分析节点   │
        │  (POI Node)        │
        │  • 写字楼搜索      │
        │  • 住宅区搜索      │
        │  • 学校搜索        │
        │  • 客源结构分析    │
        └─────────┬──────────┘
                  │
                  ▼
        ┌────────────────────┐
        │   图表生成节点      │
        │  (Chart Node)      │
        │  • 竞争对手图表    │
        │  • 客源分布饼图    │
        │  • 天气趋势图      │
        │  • 交通评分雷达图  │
        └─────────┬──────────┘
                  │
                  ▼
        ┌────────────────────┐
        │   报告汇总节点      │
        │  (Report Node)     │
        │  • 汇总所有分析    │
        │  • 生成建议        │
        │  • 输出 Markdown   │
        └─────────┬──────────┘
                  │
                  ▼
              ┌────────┐
              │  END   │
              └────────┘
```

### 状态管理 (AgentState)

工作流中的数据通过 **AgentState** 统一管理：

```python
class AgentState(TypedDict):
    # 输入数据
    store_name: str          # 店铺名称
    store_address: str       # 店铺地址
    store_type: str          # 店铺类型
    analysis_radius: int     # 分析半径
    
    # 分析结果
    location: LocationInfo           # 位置信息
    competitors: list[CompetitorInfo] # 竞争对手
    traffic: TrafficInfo             # 交通信息
    weather: WeatherData             # 天气数据
    poi_analysis: POIAnalysis        # 商业环境
    charts: ChartData                # 图表数据
    
    # 输出
    final_report: str        # 最终报告
    errors: list[str]        # 错误信息
```

### MCP 客户端设计

采用 **SSE (Server-Sent Events)** 协议与魔搭社区 MCP 服务通信：

```
┌─────────────────┐      SSE Request       ┌─────────────────────┐
│                 │ ──────────────────────▶│                     │
│   MCP Client    │                        │   MCP Server        │
│  (本地客户端)    │◀────────────────────── │  (魔搭社区托管)      │
│                 │      SSE Response      │                     │
└─────────────────┘                        └─────────────────────┘
        │
        │ 支持的操作:
        │ • initialize    - 初始化连接
        │ • tools/list    - 列出可用工具
        │ • tools/call    - 调用工具
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│                     MCP 工具封装                             │
│  ┌─────────────────────────┐  ┌─────────────────────────┐  │
│  │      AmapTools          │  │      ChartTools         │  │
│  │  • geocode()           │  │  • create_bar_chart()   │  │
│  │  • reverse_geocode()   │  │  • create_pie_chart()   │  │
│  │  • search_around()     │  │  • create_line_chart()  │  │
│  │  • get_weather()       │  │  • create_radar_chart() │  │
│  │  • get_transit_route() │  │                         │  │
│  └─────────────────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 可视化系统设计

支持多种可视化方式：

```
┌─────────────────────────────────────────────────────────────────┐
│                      可视化系统 (Visualization)                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────┐     ┌─────────────────────────────┐   │
│  │   ChartRenderer     │     │   NotebookVisualizer        │   │
│  │   (Pyppeteer)       │     │   (IPython + Plotly)        │   │
│  │                     │     │                             │   │
│  │  • HTML → PNG/JPEG  │     │  • display_report()        │   │
│  │  • SVG → PNG        │     │  • plot_competitors()      │   │
│  │  • ECharts 渲染     │     │  • plot_poi_distribution() │   │
│  │                     │     │  • plot_traffic_radar()    │   │
│  └──────────┬──────────┘     │  • plot_weather_trend()    │   │
│             │                │  • display_dashboard()      │   │
│             ▼                └─────────────┬───────────────┘   │
│  ┌─────────────────────┐                   │                   │
│  │   Headless Chrome   │                   ▼                   │
│  │   (无头浏览器)       │     ┌─────────────────────────────┐   │
│  └─────────────────────┘     │   Plotly 交互式图表          │   │
│                              │   (支持缩放、悬停、导出)      │   │
│                              └─────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### 数据流转过程

```
用户输入                    MCP 服务调用                    数据处理
─────────                  ─────────────                  ─────────
                                                         
店铺名称 ─┐                                              ┌─→ 位置信息
店铺地址 ─┼─→ 位置分析节点 ─→ maps_geo ─────────────────┤
店铺类型 ─┘                   maps_regeo                 └─→ 商圈信息
                                    
位置坐标 ─────→ 竞争分析节点 ─→ maps_search_around ─────→ 竞争对手列表
                                    
位置坐标 ─────→ 交通分析节点 ─→ maps_search_around ─────→ 交通设施 + 评分
                              (公交/地铁/停车场)
                                    
城市名称 ─────→ 天气分析节点 ─→ maps_weather ───────────→ 天气预报 + 影响
                                    
位置坐标 ─────→ POI分析节点 ──→ maps_search_around ─────→ 客源结构分析
                              (写字楼/住宅/学校)
                                    
分析数据 ─────→ 图表生成节点 ─→ chart_bindbindbindbar ─→ 可视化图表
                              chart_bindpie
                              chart_bindline
                                    
全部数据 ─────→ 报告汇总节点 ─→ LLM (可选) ─────────────→ Markdown 报告
```

---

## 🛠️ 技术栈

| 组件 | 技术选型 | 说明 |
|------|----------|------|
| 智能体框架 | LangGraph | 构建有向图工作流 |
| LLM | OpenAI / DeepSeek / SiliconFlow | 可切换的 LLM 后端 |
| MCP 客户端 | 自研 SSE 客户端 | 基于 httpx-sse |
| 地图服务 | 高德地图 MCP | 魔搭社区托管 |
| 图表生成 | AntV 图表 MCP | 魔搭社区托管 |
| 图片渲染 | Pyppeteer | Headless Chrome |
| 交互可视化 | Plotly | Jupyter 环境 |
| 配置管理 | Pydantic Settings | 类型安全配置 |

---

## 📦 安装

### 1. 克隆项目

```bash
cd restaurant-report-agent
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

复制 `env_example.txt` 为 `.env` 并填入配置：

```bash
cp env_example.txt .env
```

编辑 `.env` 文件：

```env
# LLM 配置 - 选择 openai、deepseek 或 siliconflow
LLM_PROVIDER=siliconflow

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o-mini

# DeepSeek Configuration
# LLM_PROVIDER=deepseek
# DEEPSEEK_API_KEY=your_deepseek_api_key

# SiliconFlow Configuration (国内高性价比选择)
SILICONFLOW_API_KEY=your_siliconflow_api_key
SILICONFLOW_BASE_URL=https://api.siliconflow.cn/v1
SILICONFLOW_MODEL=Qwen/Qwen2.5-7B-Instruct

# 高德地图 API Key (必填)
# 申请地址: https://lbs.amap.com/
AMAP_MAPS_API_KEY=your_amap_api_key
```

**推荐 LLM 选择**：
- **OpenAI GPT** - 效果最好，但需要国际网络
- **DeepSeek** - 国产优秀模型，性价比高
- **SiliconFlow** - 国内访问快，提供多种开源模型（推荐）

---

## 🚀 使用方法

### 命令行运行

```bash
# 基本用法
python main.py --name "店铺名称" --address "店铺地址"

# 完整参数
python main.py \
  --name "星巴克咖啡" \
  --address "北京市朝阳区建国路88号SOHO现代城" \
  --type "咖啡店" \
  --radius 1000 \
  --output "./my_report.md"
```

### 参数说明

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `--name` | `-n` | 店铺名称 | (必填) |
| `--address` | `-a` | 店铺地址 | (必填) |
| `--type` | `-t` | 店铺类型 | 餐厅 |
| `--radius` | `-r` | 分析半径(米) | 1000 |
| `--output` | `-o` | 输出文件路径 | ./reports/店铺名_时间戳.md |
| `--no-llm` | - | 不使用 LLM 增强 | - |

### 支持的店铺类型

- 餐厅、咖啡店、奶茶店、火锅店、烧烤店
- 快餐店、面馆、西餐厅、日料店、韩餐厅
- 川菜馆、粤菜馆、甜品店、面包店

### Jupyter Notebook 使用

```bash
jupyter notebook notebook_demo.ipynb
```

### 代码调用

```python
import asyncio
from main import run_analysis

async def main():
    report = await run_analysis(
        store_name="我的咖啡店",
        store_address="上海市浦东新区陆家嘴环路1000号",
        store_type="咖啡店",
        analysis_radius=800
    )
    print(report)

asyncio.run(main())
```

### 使用可视化器

```python
from visualization.notebook import NotebookVisualizer

viz = NotebookVisualizer()

# 显示竞争对手分析图表
viz.plot_competitors(competitors_data, "我的店铺")

# 显示客源分布饼图
viz.plot_poi_distribution(poi_counts)

# 显示交通评分雷达图
viz.plot_traffic_radar(traffic_scores)

# 显示完整仪表板
viz.display_analysis_dashboard(final_state)
```

### 使用 Pyppeteer 渲染图表

```python
from visualization.renderer import ChartRenderer

renderer = ChartRenderer(width=800, height=600)
await renderer.initialize()

# 渲染 HTML 为图片
result = await renderer.render_html(
    html_content="<div>...</div>",
    output_path="chart.png"
)

# 渲染 SVG 为图片
result = await renderer.render_svg(
    svg_content="<svg>...</svg>",
    output_path="chart.png"
)

await renderer.close()
```

---

## 📊 报告内容

生成的报告包含以下部分：

1. **店铺基础信息** - 地址、坐标、所属商圈
2. **竞争对手分析** - 周边同类店铺数量、距离、评分
3. **交通便利性** - 公交/地铁/停车场分布及评分
4. **天气影响分析** - 天气预报及对客流的影响
5. **商业环境分析** - 客源结构及建议
6. **数据可视化** - 各类分析图表
7. **总结与建议** - 综合经营建议

---

## 📁 项目结构

```
restaurant-report-agent/
├── config/
│   ├── __init__.py
│   └── settings.py           # 配置管理
├── mcp_client/
│   ├── __init__.py
│   └── client.py             # MCP SSE 客户端
├── tools/
│   ├── __init__.py
│   ├── amap_tools.py         # 高德地图工具
│   └── chart_tools.py        # 图表生成工具
├── nodes/
│   ├── __init__.py
│   ├── state.py              # 状态定义
│   ├── location.py           # 位置分析节点
│   ├── competitor.py         # 竞争对手分析
│   ├── traffic.py            # 交通分析
│   ├── weather.py            # 天气分析
│   ├── poi.py                # 商业环境分析
│   ├── chart.py              # 图表生成
│   └── report.py             # 报告汇总
├── graph/
│   ├── __init__.py
│   └── agent.py              # LangGraph 工作流
├── visualization/
│   ├── __init__.py
│   ├── renderer.py           # Pyppeteer 图表渲染
│   └── notebook.py           # Jupyter 可视化
├── main.py                   # 命令行入口
├── notebook_demo.ipynb       # Jupyter 演示
├── requirements.txt          # 依赖配置
├── env_example.txt           # 环境变量模板
└── README.md                 # 使用说明
```

---

## 🔧 MCP 服务说明

本项目使用魔搭社区提供的 MCP 服务：

### 高德地图 MCP

- **URL**: `https://mcp.modelscope.cn/sse/@amap/amap-maps`
- **功能**: 
  - `maps_geo` - 地理编码
  - `maps_regeo` - 逆地理编码
  - `maps_search_text` - 关键词搜索
  - `maps_search_around` - 周边搜索
  - `maps_search_detail` - POI 详情
  - `maps_weather` - 天气查询
  - `maps_direction_transit` - 公交路径规划
  - `maps_direction_driving` - 驾车路径规划
- **需要**: 高德开放平台 API Key

### 可视化图表 MCP

- **URL**: `https://mcp.modelscope.cn/sse/@antvis/mcp-server-chart`
- **功能**: 生成柱状图、饼图、折线图、雷达图等 25+ 种图表

---

## ⚠️ 注意事项

1. **API Key 必填**: 高德地图 API Key 是必需的，请在 [高德开放平台](https://lbs.amap.com/) 申请
2. **网络要求**: 需要能够访问魔搭社区 MCP 服务
3. **LLM 可选**: 即使不配置 LLM，也可以生成基础报告
4. **Pyppeteer**: 首次使用会自动下载 Chromium 浏览器

---

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

*本项目基于 LangGraph 框架和魔搭社区 MCP 服务开发*
