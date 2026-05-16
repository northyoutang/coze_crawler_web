@echo off
chcp 65001 > nul
echo ========================================
echo   扣子技能爬取管理系统
echo ========================================
echo.

REM 检查 Python 是否安装
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 错误: 未找到 python，请先安装 Python 3.8+
    pause
    exit /b 1
)

REM 检查是否已安装依赖
if not exist venv (
    echo 📦 创建虚拟环境...
    python -m venv venv
)

REM 激活虚拟环境
call venv\Scripts\activate.bat

REM 安装依赖
echo 📦 检查并安装依赖...
pip install -q -r requirements.txt

REM 检查依赖安装结果
if %errorlevel% neq 0 (
    echo ❌ 依赖安装失败，请检查网络连接
    pause
    exit /b 1
)

REM 创建数据目录
if not exist data mkdir data

echo.
echo ✅ 环境准备完成
echo 🚀 启动服务...
echo.
echo 访问地址: http://localhost:8000
echo 默认账号: northyoutang
echo 默认密码: northyoutang@gmail
echo.
echo 按 Ctrl+C 停止服务
echo ========================================
echo.

REM 启动服务
python main.py

pause
