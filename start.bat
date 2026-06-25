@echo off
chcp 65001 >nul 2>&1
title Restaurant Report Agent - Launcher

echo ============================================
echo   餐饮店经营分析报告系统 - 一键启动
echo ============================================
echo.

:: 项目根目录
set "ROOT=%~dp0"

:: 检查端口占用并清理
echo [1/4] 检查端口占用...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000.*LISTENING" 2^>nul') do (
    echo   关闭占用 8000 端口的进程 PID=%%a
    taskkill /PID %%a /F >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3000.*LISTENING" 2^>nul') do (
    echo   关闭占用 3000 端口的进程 PID=%%a
    taskkill /PID %%a /F >nul 2>&1
)
timeout /t 2 /nobreak >nul

:: 检查 Python
echo [2/4] 检查运行环境...
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo   [错误] 未找到 Python，请先安装 Python 3.10+
    pause
    exit /b 1
)

:: 检查 Node.js
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo   [错误] 未找到 Node.js，请先安装 Node.js 18+
    pause
    exit /b 1
)
echo   Python 和 Node.js 已就绪

:: 启动后端
echo [3/4] 启动后端服务 (FastAPI :8000)...
start "Backend - FastAPI :8000" cmd /k "cd /d %ROOT% && python -m uvicorn api.main:app --host 127.0.0.1 --port 8000"
timeout /t 3 /nobreak >nul

:: 启动前端
echo [4/4] 启动前端服务 (Next.js :3000)...
start "Frontend - Next.js :3000" cmd /k "cd /d %ROOT%frontend && npm run dev"
timeout /t 5 /nobreak >nul

:: 验证
echo.
echo ============================================
echo   启动完成！
echo.
echo   前端地址: http://localhost:3000
echo   后端地址: http://localhost:8000
echo.
echo   使用方法:
echo   1. 浏览器打开 http://localhost:3000
echo   2. 填写店铺信息，点击「开始分析」
echo   3. 左侧导航查看各维度报告
echo.
echo   关闭方法: 关闭弹出的两个终端窗口即可
echo ============================================
echo.

:: 自动打开浏览器
start http://localhost:3000

pause
