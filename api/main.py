from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sys
import os
from pathlib import Path

# 添加项目根目录到 sys.path，以便能够导入项目模块
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import run_analysis

app = FastAPI(title="Restaurant Report Agent API")

# 配置 CORS，允许前端应用访问。
# 安全：allow_origins=["*"] 搭配 allow_credentials=True 是非法组合（浏览器会拒绝，且不安全），
# 改为显式 allowlist；可用环境变量 ALLOWED_ORIGINS（逗号分隔）覆盖，生产填真实域名。
ALLOWED_ORIGINS = [
    o.strip()
    for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
    if o.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from typing import Optional

class AnalyzeRequest(BaseModel):
    store_name: str
    store_address: str
    store_type: str = "餐厅"
    analysis_radius: int = 1000
    location: Optional[str] = None  # 可选传入经纬度，格式: "116.481488,39.990464"
    deep_analysis: bool = False

class AnalyzeResponse(BaseModel):
    success: bool
    message: str
    report_markdown: str = ""
    # 这里我们预留了结构化数据的字段供前端后续图表使用
    data: dict = {}

@app.post("/api/analyze", response_model=AnalyzeResponse)
async def create_analysis(request: AnalyzeRequest):
    # 暂时使用 mock 数据快速测试前端
    USE_MOCK = True  # 设为 False 使用真实 LLM
    
    if USE_MOCK:
        return AnalyzeResponse(
            success=True,
            message="分析成功 (Mock 数据)",
            report_markdown="# 店铺分析报告\n\n这是一份测试报告。",
            data={
                "competition_score": 6.5,
                "competitor_count": 13,
                "traffic_score": "良好",
                "traffic_desc": "周边有 2 个地铁站, 5 个公交站",
                "poi_main_type": "写字楼为主",
                "poi_desc": "占比约 65%",
                "weather_main": "晴",
                "weather_desc": "温度: 22°C",
                "lineChartData": [
                    {"name": "周一", "value": 400},
                    {"name": "周二", "value": 300},
                    {"name": "周三", "value": 550},
                    {"name": "周四", "value": 450},
                    {"name": "周五", "value": 700},
                    {"name": "周六", "value": 900},
                    {"name": "周日", "value": 850},
                ],
                "pieChartData": [
                    {"name": "写字楼", "value": 65},
                    {"name": "住宅", "value": 20},
                    {"name": "商场", "value": 15},
                ]
            }
        )
    
    try:
        # 我们对 main.py 的 run_analysis 进行了封装调用
        report_text, final_state = await run_analysis(
            store_name=request.store_name,
            store_address=request.store_address,
            store_type=request.store_type,
            analysis_radius=request.analysis_radius,
            use_llm=True, # 使用真实的LLM调用
            deep_analysis=request.deep_analysis,
            location=request.location
        )
        
        # 从 final_state 提取真实的分析数据给前端
        # final_state 结构可能是 dict 或 Pydantic model
        
        def safe_get(obj, key, default=None):
            """安全地从 dict 或对象中获取属性"""
            if obj is None:
                return default
            if isinstance(obj, dict):
                return obj.get(key, default)
            return getattr(obj, key, default)
        
        # 计算竞争强度分数
        competitors = safe_get(final_state, "competitors", [])
        if competitors is None:
            competitors = []
        competitor_count = len(competitors) if hasattr(competitors, '__len__') else 0
        competition_score = min(10, round(competitor_count / 2, 1)) if competitor_count > 0 else 0
        
        # 提取交通信息
        traffic = safe_get(final_state, "traffic", {})
        traffic_score_val = safe_get(traffic, "score", 0) or 0
        traffic_score = "一般"
        if traffic_score_val > 80:
            traffic_score = "极佳"
        elif traffic_score_val > 60:
            traffic_score = "良好"
        
        subway_stations = safe_get(traffic, "subway_stations", []) or []
        bus_stations = safe_get(traffic, "bus_stations", []) or []
        traffic_desc = f"周边有 {len(subway_stations)} 个地铁站, {len(bus_stations)} 个公交站"
        
        # 提取 POI 商圈分析
        poi_analysis = safe_get(final_state, "poi_analysis", {})
        counts = safe_get(poi_analysis, "counts", {})
        if counts is None:
            counts = {}
        if hasattr(counts, 'dict'):
            counts = counts.dict()
        total_poi = sum(counts.values()) if counts else 1
        
        poi_main_type = "写字楼为主"
        poi_desc = "周边商务气息浓厚"
        if counts:
            main_type = max(counts.items(), key=lambda x: x[1])
            poi_main_type = f"{main_type[0]}为主"
            poi_desc = f"占比约 {int(main_type[1]/total_poi*100)}%"
            
        # 构造饼图数据
        pieChartData = []
        for k, v in counts.items():
            pieChartData.append({"name": k, "value": v})
        if not pieChartData:
            pieChartData = [
                {"name": "写字楼", "value": 65},
                {"name": "住宅", "value": 20},
                {"name": "商场", "value": 15},
            ]
            
        # 提取天气信息
        weather = safe_get(final_state, "weather", {})
        weather_main = safe_get(weather, "weather", "未知") or "未知"
        weather_temp = safe_get(weather, "temperature", "-") or "-"
        weather_desc = f"温度: {weather_temp}°C"

        mock_data = {
            "competition_score": competition_score,
            "competitor_count": competitor_count,
            "traffic_score": traffic_score,
            "traffic_desc": traffic_desc,
            "poi_main_type": poi_main_type,
            "poi_desc": poi_desc,
            "weather_main": weather_main,
            "weather_desc": weather_desc,
            "lineChartData": [
                {"name": "周一", "value": 400},
                {"name": "周二", "value": 300},
                {"name": "周三", "value": 550},
                {"name": "周四", "value": 450},
                {"name": "周五", "value": 700},
                {"name": "周六", "value": 900},
                {"name": "周日", "value": 850},
            ],
            "pieChartData": pieChartData
        }
        
        return AnalyzeResponse(
            success=True,
            message="分析成功",
            report_markdown=report_text,
            data=mock_data
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def root():
    return {
        "message": "Restaurant Report Agent API",
        "frontend": "请访问 http://localhost:3000 使用前端界面",
        "endpoints": {
            "health": "/api/health",
            "analyze": "POST /api/analyze"
        }
    }

@app.get("/api/health")
def health_check():
    return {"status": "ok"}
