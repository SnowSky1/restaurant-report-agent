@echo off
chcp 936 >nul
setlocal
title Restaurant Report Agent 0.0.0
set "ROOT=%~dp0"

echo ============================================
echo   Restaurant Report Agent 0.0.0
echo ============================================

where python >nul 2>&1 || (echo [错误] 未找到 Python 3.10+ & pause & exit /b 1)
where node >nul 2>&1 || (echo [错误] 未找到 Node.js 20.9+ & pause & exit /b 1)
where npm >nul 2>&1 || (echo [错误] 未找到 npm & pause & exit /b 1)
if not exist "%ROOT%.env" (echo [错误] 缺少 .env，请先从 .env.example 复制并配置 & pause & exit /b 1)
if not exist "%ROOT%frontend\.env.local" (echo [错误] 缺少 frontend\.env.local，请先从 .env.example 复制并配置 & pause & exit /b 1)

netstat -ano | findstr /R /C:":8000 .*LISTENING" >nul && (echo [错误] 端口 8000 已被占用，请先确认对应进程 & pause & exit /b 1)
netstat -ano | findstr /R /C:":3000 .*LISTENING" >nul && (echo [错误] 端口 3000 已被占用，请先确认对应进程 & pause & exit /b 1)

echo [1/2] 启动 FastAPI...
start "Restaurant Agent Backend" /D "%ROOT%" cmd /k python -m uvicorn api.main:app --host 127.0.0.1 --port 8000
timeout /t 3 /nobreak >nul

echo [2/2] 启动 Next.js...
start "Restaurant Agent Frontend" /D "%ROOT%frontend" cmd /k npm run dev -- --hostname 127.0.0.1 --port 3000
timeout /t 4 /nobreak >nul

echo 前端: http://127.0.0.1:3000
echo API:  http://127.0.0.1:8000/docs
start "" http://127.0.0.1:3000
endlocal
