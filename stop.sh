#!/bin/bash

echo "🛑 停止 SIRY AI Research API..."

pkill -f "uvicorn src.main:app" && echo "✅ 服务已停止" || echo "⚠️  未找到运行中的服务"
