@echo off
chcp 65001 >nul
echo ========================================
echo    餐饮店经营分析智能体 - 快速测试
echo ========================================
echo.

REM 检查 .env 文件是否存在
if not exist .env (
    echo [创建配置文件]
    echo 正在创建 .env 文件...
    (
        echo LLM_PROVIDER=siliconflow
        echo SILICONFLOW_API_KEY=your_siliconflow_api_key_here
        echo SILICONFLOW_BASE_URL=https://api.siliconflow.cn/v1
        echo SILICONFLOW_MODEL=Qwen/Qwen2.5-7B-Instruct
        echo AMAP_MAPS_API_KEY=your_amap_api_key_here
        echo AMAP_MCP_URL=https://mcp.modelscope.cn/sse/@amap/amap-maps
        echo CHART_MCP_URL=https://mcp.modelscope.cn/sse/@antvis/mcp-server-chart
        echo OUTPUT_DIR=./reports
    ) > .env
    echo ✓ .env 文件创建成功
    echo.
) else (
    echo ✓ .env 文件已存在
    echo.
)

REM 检查 Python 是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未找到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)

echo [Python 版本]
python --version
echo.

REM 检查依赖是否安装
echo [检查依赖]
python -c "import langgraph" >nul 2>&1
if errorlevel 1 (
    echo 正在安装依赖...
    pip install -r requirements.txt
    echo.
) else (
    echo ✓ 依赖已安装
    echo.
)

REM 运行测试
echo [开始测试分析]
echo 分析店铺: 星巴克咖啡(SOHO现代城店)
echo 地址: 北京市朝阳区建国路88号SOHO现代城
echo.

python main.py ^
  --name "星巴克咖啡(SOHO现代城店)" ^
  --address "北京市朝阳区建国路88号SOHO现代城" ^
  --type "咖啡店" ^
  --radius 800

echo.
echo ========================================
echo 测试完成！
echo.
echo 报告已保存在 reports/ 目录下
echo.
echo 查看高德 API 使用情况:
echo https://console.amap.com/
echo ========================================
pause

