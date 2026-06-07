@echo off
chcp 65001 >nul
title Quant Dashboard - 本地启动

echo ============================================
echo   Quant Dashboard 本地开发环境
echo ============================================
echo.

:: 检查 Python
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [错误] 未找到 Python，请先安装 Python 3.10+
    pause
    exit /b 1
)

:: 检查 Node
where node >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [错误] 未找到 Node.js，请先安装 Node.js 18+
    pause
    exit /b 1
)

echo [1/3] 安装后端依赖...
cd /d "%~dp0backend"
pip install -r requirements.txt -q
if %ERRORLEVEL% neq 0 (
    echo [警告] pip install 有错误，继续尝试...
)

echo [2/3] 安装前端依赖...
cd /d "%~dp0frontend"
call npm install --silent
if %ERRORLEVEL% neq 0 (
    echo [警告] npm install 有错误，继续尝试...
)

echo [3/3] 启动服务...
echo.
echo   后端: http://localhost:8000
echo   前端: http://localhost:5173
echo   API文档: http://localhost:8000/docs
echo.

:: 启动后端（新窗口）
cd /d "%~dp0backend"
start "Quant Backend" cmd /c "uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

:: 等待后端启动
timeout /t 3 /nobreak >nul

:: 启动前端（新窗口）
cd /d "%~dp0frontend"
start "Quant Frontend" cmd /c "npx vite --host 0.0.0.0 --port 5173"

echo.
echo 服务已在新窗口中启动！
echo 关闭窗口即可停止服务。
echo.
pause
