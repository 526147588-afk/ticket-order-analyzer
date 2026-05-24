@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

title 出票订单数据分析工具 v1.0

echo =============================================
echo     出票订单数据分析工具 v1.0
echo =============================================
echo.

cd /d "%~dp0"

echo [1/3] 检查 Python 环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python，请先安装 Python 3.8+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [2/3] 安装依赖包...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo [错误] 依赖安装失败，请检查网络连接
    pause
    exit /b 1
)

echo [3/3] 启动应用...
echo ------------------------------------------------
echo 启动后浏览器将自动打开 http://localhost:8501
echo 按 Ctrl+C 可以停止服务
echo ------------------------------------------------
echo.

streamlit run main.py --server.port 8501 --server.headless true --browser.gatherUsageStats false

pause