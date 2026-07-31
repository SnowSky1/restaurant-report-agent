@echo off
chcp 65001 >nul 2>&1
setlocal
set "ROOT=%~dp0"
cd /d "%ROOT%"

echo [1/6] 后端静态检查
ruff check api config graph main.py mcp_client nodes services tests tools || goto :failed
ruff format --check api config graph main.py mcp_client nodes services tests tools || goto :failed

echo [2/6] 后端单元与集成测试
python -m unittest discover -s tests -v || goto :failed

echo [3/6] 前端逻辑测试
pushd frontend
call npm test || (popd & goto :failed)

echo [4/6] 前端 ESLint
call npm run lint -- --no-cache || (popd & goto :failed)

echo [5/6] Next.js 生产构建
call npm run build || (popd & goto :failed)

echo [6/6] 生产依赖安全审计
call npm audit --omit=dev || (popd & goto :failed)
popd

echo.
echo 全部检查通过。
pause
exit /b 0

:failed
echo.
echo 检查失败，请查看上方日志。
pause
exit /b 1
