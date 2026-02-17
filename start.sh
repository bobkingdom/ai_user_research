#!/bin/bash

# SIRY AI Research - 快速启动脚本

echo "🚀 启动 SIRY AI Research API..."

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "🔧 激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo "📥 安装依赖..."
pip install -r requirements.txt

# 检查 .env 文件
if [ ! -f ".env" ]; then
    echo "⚠️  警告: .env 文件不存在"
    echo "请复制 .env.example 为 .env 并配置 API Keys"
    echo ""
    echo "cp .env.example .env"
    echo ""
    read -p "是否现在创建 .env 文件? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cp .env.example .env
        echo "✅ 已创建 .env 文件，请编辑并填入你的 API Keys"
        exit 0
    fi
fi

# 启动服务
echo "🌐 启动 FastAPI 服务..."
echo "📍 访问 http://localhost:8000/docs 查看 API 文档"
echo ""
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
