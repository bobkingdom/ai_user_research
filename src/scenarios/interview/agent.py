"""
InterviewAgent - Claude Agent SDK based 1-on-1 audience interview agent.

Features:
- Agentic Loop: Multi-turn conversation with autonomous reasoning
- MCP Tools: Optional external tool calls (search, memory, etc.)
- SPIN Framework: Situation/Problem/Implication/Need-payoff methodology
"""
import os
import json
import uuid
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from anthropic import Anthropic

from .models import (
    AudienceProfileForInterview,
    InterviewConfig,
    InterviewSession,
    InterviewMessage,
    InterviewSummary,
    InterviewStage,
    MessageRole,
    Insight,
    InsightType,
)
from ...core.prompts import PromptTemplates

logger = logging.getLogger(__name__)


class AgentResponse:
    """
    Agent响应数据结构
    """
    def __init__(
        self,
        content: str,
        stop_reason: str,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
        insights: Optional[List[Insight]] = None,
    ):
        self.content = content
        self.stop_reason = stop_reason
        self.tool_calls = tool_calls or []
        self.insights = insights or []


class InterviewAgent:
    """
    基于Claude Agent SDK的1对1受众访谈代理

    特性:
    - Agentic Loop: 多轮对话循环，自主推理
    - MCP工具: 可选的外部工具调用（如搜索、数据查询）
    - SPIN框架: Situation/Problem/Implication/Need-payoff
    """

    def __init__(
        self,
        audience_profile: AudienceProfileForInterview,
        interview_config: InterviewConfig,
        mcp_tools: Optional[List[Dict[str, Any]]] = None,
        api_key: Optional[str] = None,
    ):
        """
        初始化访谈代理

        Args:
            audience_profile: 受众画像
            interview_config: 访谈配置
            mcp_tools: MCP工具列表（可选）
            api_key: Anthropic API Key（默认从环境变量读取）
        """
        self.profile = audience_profile
        self.config = interview_config
        self.mcp_tools = mcp_tools or []

        # 初始化 Anthropic 客户端
        self.client = Anthropic(api_key=api_key or os.getenv("ANTHROPIC_API_KEY"))

        # 会话状态
        self.session: Optional[InterviewSession] = None
        self.system_prompt: Optional[str] = None

        logger.info(
            f"InterviewAgent initialized for {audience_profile.name}, "
            f"topic: {interview_config.research_topic}"
        )

    def _build_system_prompt(self) -> str:
        """
        构建系统提示词

        复用 backhour_ai 的受众对话提示词模板
        """
        # 获取受众画像上下文
        context = self.profile.to_prompt_context()

        # 渲染基础系统提示词
        base_prompt = PromptTemplates.render_audience_prompt(context)

        # 添加 SPIN 框架说明
        spin_context = f"""

## Interview Context

You are participating in a user research interview.

Topic: {self.config.research_topic}

Research Objectives:
{chr(10).join(f'- {obj}' for obj in self.config.research_objectives)}

{PromptTemplates.SPIN_FRAMEWORK}

Please engage naturally in this conversation, sharing your authentic experiences and thoughts related to this topic.
"""

        return base_prompt + spin_context

    async def start_interview(self) -> InterviewSession:
        """
        启动访谈会话

        Returns:
            创建的访谈会话
        """
        # 创建会话
        session_id = str(uuid.uuid4())
        self.session = InterviewSession(
            session_id=session_id,
            audience_profile=self.profile,
            config=self.config,
            current_stage=InterviewStage.OPENING,
        )

        # 构建系统提示词
        self.system_prompt = self._build_system_prompt()

        # 生成开场白
        opening_prompt = PromptTemplates.render_opening_prompt(
            research_topic=self.config.research_topic,
            research_objectives=self.config.research_objectives,
        )

        # 调用 Claude 生成开场白
        response = await self._call_claude(opening_prompt)

        # 添加到会话历史
        self.session.add_message(
            InterviewMessage(
                role=MessageRole.USER,
                content=opening_prompt,
            )
        )
        self.session.add_message(
            InterviewMessage(
                role=MessageRole.ASSISTANT,
                content=response.content,
            )
        )

        logger.info(f"Interview session {session_id} started")
        return self.session

    async def respond(self, user_message: str) -> AgentResponse:
        """
        处理用户输入，返回受众回复

        实现 Agentic Loop: Think -> Act -> Observe

        Args:
            user_message: 用户（研究人员）的问题或回应

        Returns:
            Agent响应，包含内容、工具调用等
        """
        if not self.session or not self.session.is_active:
            raise ValueError("Interview session not active. Call start_interview() first.")

        # 添加用户消息到历史
        self.session.add_message(
            InterviewMessage(
                role=MessageRole.USER,
                content=user_message,
            )
        )

        # Agentic Loop
        response = await self._agentic_loop()

        # 添加助手回复到历史
        self.session.add_message(
            InterviewMessage(
                role=MessageRole.ASSISTANT,
                content=response.content,
                tool_calls=response.tool_calls if response.tool_calls else None,
            )
        )

        # 自动提取洞察（如果启用）
        if self.config.auto_extract_insights:
            insights = await self._extract_insights_from_response(response.content, user_message)
            for insight in insights:
                self.session.add_insight(insight)
            response.insights = insights

        return response

    async def _agentic_loop(self) -> AgentResponse:
        """
        Agentic Loop 核心实现

        循环：思考 -> 行动 -> 观察，直到完成任务
        """
        max_iterations = 5  # 防止无限循环
        iteration = 0

        while iteration < max_iterations:
            iteration += 1

            # 调用 Claude API
            response = await self._call_claude()

            # 检查停止原因
            if response.stop_reason == "end_turn":
                # 正常结束，返回响应
                return response

            elif response.stop_reason == "tool_use":
                # 需要执行工具调用
                if not self.config.enable_mcp_tools:
                    logger.warning("Tool use requested but MCP tools disabled")
                    return AgentResponse(
                        content=response.content,
                        stop_reason="end_turn",
                    )

                # 执行工具调用
                tool_results = await self._execute_tools(response.tool_calls)

                # 将工具结果添加到对话历史
                self.session.add_message(
                    InterviewMessage(
                        role=MessageRole.USER,  # Tool results are treated as user messages
                        content="",
                        tool_results=tool_results,
                    )
                )

                # 继续循环，让Claude处理工具结果
                continue

            else:
                # 其他停止原因，返回响应
                logger.info(f"Stopped with reason: {response.stop_reason}")
                return response

        # 达到最大迭代次数
        logger.warning(f"Reached max iterations ({max_iterations}) in agentic loop")
        return AgentResponse(
            content="I apologize, but I need to wrap up this part of our conversation.",
            stop_reason="max_iterations",
        )

    async def _call_claude(self, user_message: Optional[str] = None) -> AgentResponse:
        """
        调用 Claude API

        Args:
            user_message: 可选的用户消息（用于开场白等）

        Returns:
            Agent响应
        """
        # 构建消息历史
        messages = self.session.get_conversation_history() if self.session else []

        # 如果提供了新消息，添加到历史
        if user_message:
            messages.append({"role": "user", "content": user_message})

        # 准备工具定义（如果启用）
        tools = self.mcp_tools if self.config.enable_mcp_tools else None

        try:
            # 调用 Claude API
            response = self.client.messages.create(
                model=self.config.model_id,
                max_tokens=2048,
                system=self.system_prompt,
                messages=messages,
                tools=tools,
            )

            # 提取内容
            content = ""
            tool_calls = []

            for block in response.content:
                if block.type == "text":
                    content += block.text
                elif block.type == "tool_use":
                    tool_calls.append({
                        "id": block.id,
                        "name": block.name,
                        "input": block.input,
                    })

            return AgentResponse(
                content=content.strip(),
                stop_reason=response.stop_reason,
                tool_calls=tool_calls,
            )

        except Exception as e:
            logger.error(f"Error calling Claude API: {e}")
            raise

    async def _execute_tools(self, tool_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        执行工具调用

        Args:
            tool_calls: 工具调用列表

        Returns:
            工具结果列表
        """
        results = []

        for tool_call in tool_calls:
            tool_name = tool_call["name"]
            tool_input = tool_call["input"]

            logger.info(f"Executing tool: {tool_name} with input: {tool_input}")

            # 这里应该调用实际的MCP工具
            # 目前返回模拟结果
            result = {
                "tool_use_id": tool_call["id"],
                "content": f"Tool {tool_name} executed successfully (mock result)",
            }

            results.append(result)

        return results

    async def _extract_insights_from_response(
        self,
        assistant_content: str,
        user_message: str,
    ) -> List[Insight]:
        """
        从对话中提取洞察

        Args:
            assistant_content: 助手回复内容
            user_message: 用户问题

        Returns:
            提取的洞察列表
        """
        # 简单的关键词提取逻辑
        insights = []

        # 痛点识别
        pain_keywords = ["frustrated", "annoying", "difficult", "problem", "challenge", "struggle"]
        if any(keyword in assistant_content.lower() for keyword in pain_keywords):
            insights.append(
                Insight(
                    content=f"Pain point mentioned in response to: {user_message[:50]}...",
                    insight_type=InsightType.PAIN_POINT,
                    confidence_score=0.7,
                    evidence=assistant_content[:100] + "...",
                    stage=self.session.current_stage,
                )
            )

        # 需求识别
        need_keywords = ["need", "want", "wish", "would like", "looking for", "ideal"]
        if any(keyword in assistant_content.lower() for keyword in need_keywords):
            insights.append(
                Insight(
                    content=f"Need expressed in response to: {user_message[:50]}...",
                    insight_type=InsightType.NEED,
                    confidence_score=0.7,
                    evidence=assistant_content[:100] + "...",
                    stage=self.session.current_stage,
                )
            )

        # 情感识别
        emotion_keywords = ["excited", "happy", "worried", "anxious", "love", "hate"]
        if any(keyword in assistant_content.lower() for keyword in emotion_keywords):
            insights.append(
                Insight(
                    content=f"Emotional response to: {user_message[:50]}...",
                    insight_type=InsightType.EMOTION,
                    confidence_score=0.6,
                    evidence=assistant_content[:100] + "...",
                    stage=self.session.current_stage,
                )
            )

        return insights

    async def end_interview(self) -> InterviewSummary:
        """
        结束访谈，生成总结

        Returns:
            访谈总结
        """
        if not self.session:
            raise ValueError("No active interview session")

        # 结束会话
        self.session.end_session()

        # 计算时长
        duration = (self.session.ended_at - self.session.started_at).total_seconds()

        # 统计洞察
        insights_by_type = {}
        for insight in self.session.insights:
            insight_type = insight.insight_type
            insights_by_type[insight_type] = insights_by_type.get(insight_type, 0) + 1

        # 提取关键发现
        key_findings = [
            f"{count} {insight_type} insights extracted"
            for insight_type, count in insights_by_type.items()
        ]

        summary = InterviewSummary(
            session_id=self.session.session_id,
            total_messages=len(self.session.messages),
            total_insights=len(self.session.insights),
            duration_seconds=int(duration),
            insights_by_type=insights_by_type,
            key_findings=key_findings,
            messages=self.session.messages,
            insights=self.session.insights,
        )

        logger.info(
            f"Interview session {self.session.session_id} ended. "
            f"Duration: {duration:.0f}s, Messages: {len(self.session.messages)}, "
            f"Insights: {len(self.session.insights)}"
        )

        return summary

    def get_session(self) -> Optional[InterviewSession]:
        """获取当前会话"""
        return self.session

    def set_stage(self, stage: InterviewStage):
        """设置当前访谈阶段"""
        if self.session:
            self.session.current_stage = stage
            logger.info(f"Interview stage changed to: {stage}")
