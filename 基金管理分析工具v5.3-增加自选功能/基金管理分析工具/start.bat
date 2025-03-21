@echo off
chcp 65001
setlocal enabledelayedexpansion

echo 正在检查Python环境...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到Python环境，请先安装Python 3.x
    pause
    exit /b 1
)

echo 正在检查pip...
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到pip，请确保Python安装正确
    pause
    exit /b 1
)

echo 正在安装依赖包...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [错误] 安装依赖包失败
    pause
    exit /b 1
)

echo 正在启动应用程序...
streamlit run app/main.py

pause