"""
API 路由模块 - 1对1访谈相关 API
使用 Claude Agent SDK + MCP Tools 实现深度访谈
"""
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from src.routers.deps import verify_api_key
from src.core.models import AudienceProfile

router = APIRouter(
    prefix="/api/interviews",
    tags=["1对1访谈 (Claude Agent SDK)"],
    dependencies=[Depends(verify_api_key)]
)


# ===== Request Models =====

class InterviewCreateRequest(BaseModel):
    audience_id: str = Field(..., description="受众ID")
    audience_profile: Optional[AudienceProfile] = Field(None, description="受众画像（无状态模式直接传入）")
    topic: str = Field(..., description="访谈主题")
    research_objectives: List[str] = Field(default=[], description="研究目标")
    message_histories: List[Dict[str, Any]] = Field(default=[], description="历史消息（无状态上下文传递）")
    mcp_tools: List[str] = Field(
        default=["personality", "chat_history", "web_search"],
        description="启用的MCP工具"
    )


class InterviewMessageRequest(BaseModel):
    interview_id: str = Field(..., description="访谈会话ID")
    message: str = Field(..., description="访谈者消息")
    audience_profile: Optional[AudienceProfile] = Field(None, description="受众画像")
    message_histories: List[Dict[str, Any]] = Field(default=[], description="历史消息")


class EndInterviewRequest(BaseModel):
    interview_id: str = Field(..., description="访谈会话ID")
    message_histories: List[Dict[str, Any]] = Field(default=[], description="完整对话历史")


class GetInterviewRequest(BaseModel):
    interview_id: str = Field(..., description="访谈会话ID")


class GetInterviewMessagesRequest(BaseModel):
    interview_id: str = Field(..., description="访谈会话ID")


# ===== Response Models =====

class InterviewSession(BaseModel):
    interview_id: str
    audience_id: str
    topic: str
    status: str
    opening_message: str
    created_at: datetime


class InterviewMessage(BaseModel):
    message_id: str
    role: str
    content: str
    tools_used: List[str] = []
    created_at: datetime


class InterviewSummary(BaseModel):
    interview_id: str
    status: str
    total_rounds: int
    duration_seconds: int
    summary: str
    insights: List[Dict[str, Any]]
    emotion_timeline: List[Dict[str, Any]]
    ended_at: datetime


# ===== API Endpoints =====

@router.post("/create", response_model=InterviewSession, status_code=201)
async def create_interview(request: InterviewCreateRequest):
    """
    创建1对1访谈会话

    使用 Claude Agent SDK + SKILLS:
    - realistic-persona-chat SKILL
    - MCP Tools: personality, chat_history, web_search
    - 三阶段Loop: Gather → Action → Verify

    **注意**: 此端点暂未实现，返回示例数据
    """
    interview_id = f"itv-{uuid.uuid4().hex[:12]}"

    return InterviewSession(
        interview_id=interview_id,
        audience_id=request.audience_id,
        topic=request.topic,
        status="active",
        opening_message="您好，很高兴能和您聊聊。作为研究者，您的观点对我们非常重要...",
        created_at=datetime.utcnow()
    )


@router.post("/messages/send", response_model=InterviewMessage)
async def send_interview_message(request: InterviewMessageRequest):
    """
    向访谈会话发送消息

    Agent 会基于人格画像和访谈历史，使用 MCP Tools 生成真实回答

    **注意**: 此端点暂未实现，返回示例回答
    """
    return InterviewMessage(
        message_id=f"msg-{uuid.uuid4().hex[:8]}",
        role="audience",
        content="我平时主要用 Notion 做项目管理，Obsidian 做知识管理。这两个工具各有优势，但在它们之间切换还是有点麻烦...",
        tools_used=["chat_history", "personality"],
        created_at=datetime.utcnow()
    )


@router.post("/end", response_model=InterviewSummary)
async def end_interview(request: EndInterviewRequest):
    """
    结束访谈会话，获取摘要和洞察

    **注意**: 此端点暂未实现
    """
    return InterviewSummary(
        interview_id=request.interview_id,
        status="completed",
        total_rounds=8,
        duration_seconds=1200,
        summary="访谈对象是一位经验丰富的产品经理，核心痛点在于工具间的数据同步和切换成本...",
        insights=[
            {
                "type": "pain_point",
                "content": "多工具切换导致的效率损失",
                "confidence_score": 0.89
            }
        ],
        emotion_timeline=[
            {"round": 1, "emotion": "neutral"},
            {"round": 3, "emotion": "frustrated"}
        ],
        ended_at=datetime.utcnow()
    )


@router.post("/detail", response_model=InterviewSession)
async def get_interview(request: GetInterviewRequest):
    """
    获取访谈会话详情

    **注意**: 此端点暂未实现
    """
    raise HTTPException(status_code=501, detail="端点尚未实现")


@router.post("/messages/list", response_model=List[InterviewMessage])
async def get_interview_messages(request: GetInterviewMessagesRequest):
    """
    获取访谈消息历史

    **注意**: 此端点暂未实现
    """
    raise HTTPException(status_code=501, detail="端点尚未实现")


@router.websocket("/{interview_id}/ws")
async def interview_websocket(websocket: WebSocket, interview_id: str):
    """
    WebSocket 实时访谈（不需要 API Key，通过 URL 参数认证）

    **注意**: 此端点暂未实现
    """
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Echo: {data}")
    except WebSocketDisconnect:
        pass
