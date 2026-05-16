#!/bin/bash

# 扣子技能爬取管理系统启动脚本
# Linux/macOS 版本

echo "========================================"
echo "  扣子技能爬取管理系统"
echo "========================================"
echo ""

# 检查 Python 是否安装
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 python3，请先安装 Python 3.8+"
    exit 1
fi

# 检查是否已安装依赖
if [ ! -d "venv" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
echo "📦 检查并安装依赖..."
pip install -q -r requirements.txt

# 检查依赖安装结果
if [ $? -ne 0 ]; then
    echo "❌ 依赖安装失败，请检查网络连接"
    exit 1
fi

# 创建数据目录
mkdir -p data

echo ""
echo "✅ 环境准备完成"
echo "🚀 启动服务..."
echo ""
echo "访问地址: http://localhost:8000"
echo "默认账号: northyoutang"
echo "默认密码: northyoutang@gmail"
echo ""
echo "按 Ctrl+C 停止服务"
echo "========================================"
echo ""

# 启动服务
python3 main.py
