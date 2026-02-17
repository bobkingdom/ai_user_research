"""
AI User Research - FastAPI 主应用
演示如何使用三种Agent框架实现用户研究场景
"""

import os
import logging
from datetime import datetime
from typing import Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# 配置日志
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 创建 FastAPI 应用实例
app = FastAPI(
    title="AI User Research API",
    description="使用Claude Agent SDK、Agno、SmolaAgents演示AI用户研究场景",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该配置具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 启动时检查必需的环境变量
@app.on_event("startup")
async def startup_event():
    """应用启动时的初始化"""
    logger.info("🚀 AI User Research API 启动中...")

    # 检查必需的 API Key
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if not anthropic_key:
        logger.warning("⚠️ ANTHROPIC_API_KEY 未配置 - 某些功能可能不可用")
    else:
        logger.info("✅ ANTHROPIC_API_KEY 已配置")

    # 记录可选配置
    if os.getenv("OPENAI_API_KEY"):
        logger.info("✅ OPENAI_API_KEY 已配置")
    if os.getenv("OPENROUTER_API_KEY"):
        logger.info("✅ OPENROUTER_API_KEY 已配置")

    # 记录并发配置
    survey_concurrency = os.getenv("SURVEY_MAX_CONCURRENCY", "100")
    focus_group_concurrency = os.getenv("FOCUS_GROUP_MAX_CONCURRENCY", "50")
    logger.info(f"📊 问卷最大并发: {survey_concurrency}")
    logger.info(f"👥 焦点小组最大并发: {focus_group_concurrency}")

    logger.info("✅ AI User Research API 启动完成")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时的清理"""
    logger.info("🛑 AI User Research API 正在关闭...")


@app.get("/", response_model=Dict[str, Any])
async def root():
    """
    根路径 - 返回项目基本信息
    """
    return {
        "name": "AI User Research API",
        "description": "使用三种Agent框架演示AI用户研究",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
        "frameworks": {
            "claude_agent_sdk": "1对1受众访谈（Agentic Loop + MCP）",
            "agno": "问卷批量投放（Teams）+ 焦点小组批量（Workflows）",
            "smolagents": "受众生成流水线（Manager模式）"
        },
        "documentation": {
            "swagger_ui": "/docs",
            "redoc": "/redoc"
        }
    }


@app.get("/health")
async def health_check():
    """
    健康检查端点 - 用于 Render.com 和其他监控服务
    """
    try:
        # 检查必需的环境变量
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {}
        }

        # 检查 Anthropic API Key
        if os.getenv("ANTHROPIC_API_KEY"):
            health_status["checks"]["anthropic_api"] = "configured"
        else:
            health_status["checks"]["anthropic_api"] = "missing"
            health_status["status"] = "degraded"

        # 检查可选配置
        health_status["checks"]["openai_api"] = (
            "configured" if os.getenv("OPENAI_API_KEY") else "not_configured"
        )
        health_status["checks"]["openrouter_api"] = (
            "configured" if os.getenv("OPENROUTER_API_KEY") else "not_configured"
        )

        return health_status

    except Exception as e:
        logger.error(f"健康检查失败: {str(e)}")
        raise HTTPException(status_code=503, detail="Service unavailable")


@app.get("/config")
async def get_config():
    """
    获取当前配置信息（不包含敏感数据）
    """
    return {
        "log_level": os.getenv("LOG_LEVEL", "INFO"),
        "survey_max_concurrency": int(os.getenv("SURVEY_MAX_CONCURRENCY", "100")),
        "focus_group_max_concurrency": int(os.getenv("FOCUS_GROUP_MAX_CONCURRENCY", "50")),
        "python_version": os.getenv("PYTHON_VERSION", "3.11.0"),
        "api_keys_configured": {
            "anthropic": bool(os.getenv("ANTHROPIC_API_KEY")),
            "openai": bool(os.getenv("OPENAI_API_KEY")),
            "openrouter": bool(os.getenv("OPENROUTER_API_KEY"))
        }
    }


# 未来可在此添加更多路由
# 例如: /api/surveys, /api/focus-groups, /api/audiences 等

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level=LOG_LEVEL.lower()
    )
