"""
焦点小组参与者Agent - 基于 Agno Framework
单个参与者的焦点小组讨论代理，作为Agno Team的成员
"""

import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime

from agno import Agent, ModelSettings
from src.core.models import (
    AudienceProfile,
    FocusGroupDefinition,
    FocusGroupMessage,
    ParticipantRole
)

logger = logging.getLogger(__name__)


class FocusGroupParticipantAgent:
    """
    焦点小组参与者代理
    作为Agno Team的成员，基于受众画像参与焦点小组讨论

    架构：
    - 使用 agno.Agent 作为基础
    - system_prompt 包含受众完整画像和对话风格指南
    - 每轮问题独立回答，保持人设一致性
    - 支持多轮讨论，可参考历史对话上下文
    """

    def __init__(
        self,
        audience_profile: AudienceProfile,
        focus_group: FocusGroupDefinition,
        model_id: str = "claude-3-5-sonnet-20241022"
    ):
        """
        初始化焦点小组参与者Agent

        Args:
            audience_profile: 受众画像数据
            focus_group: 焦点小组定义
            model_id: 使用的模型ID
        """
        self.audience_profile = audience_profile
        self.focus_group = focus_group
        self.model_id = model_id

        # 对话历史（用于多轮讨论的上下文）
        self.conversation_history: List[Dict[str, str]] = []

        # 构建系统提示词
        self.system_prompt = self._build_system_prompt()

        # 创建 Agno Agent
        self.agent = Agent(
            name=f"focus_group_participant_{audience_profile.user_id}",
            model=ModelSettings(id=model_id),
            instructions=self.system_prompt,
            markdown=False
        )

        logger.debug(
            f"创建FocusGroupParticipantAgent: {audience_profile.name} "
            f"(user_id={audience_profile.user_id}, focus_group={focus_group.focus_group_id})"
        )

    def _build_system_prompt(self) -> str:
        """
        构建系统提示词
        复用 backhour_ai 的对话风格指南，专注于焦点小组讨论场景
        """
        profile = self.audience_profile
        demo = profile.demographics
        prof = profile.professional
        pers = profile.personality
        life = profile.lifestyle

        # 基础信息
        age = demo.get("age", "未知")
        gender = demo.get("gender", "未知")
        location = demo.get("location", "未知")
        education = demo.get("education", "未知")
        income_level = demo.get("income_level", "未知")

        # 职业信息
        industry = prof.get("industry", "未知")
        position = prof.get("position", "未知")
        company_size = prof.get("company_size", "未知")
        work_experience = prof.get("work_experience", 0)
        career_goals = prof.get("career_goals", "未知")

        # 人格特征
        personality_type = pers.get("personality_type", "未知")
        communication_style = pers.get("communication_style", "未知")
        core_traits = ", ".join(pers.get("core_traits", []))
        key_strengths = ", ".join(pers.get("key_strengths", []))
        key_weaknesses = ", ".join(pers.get("key_weaknesses", []))
        behavioral_patterns = ", ".join(pers.get("behavioral_patterns", []))

        # 生活方式
        hobbies = ", ".join(life.get("hobbies", []))
        values = ", ".join(life.get("values", []))
        brand_preferences = ", ".join(life.get("brand_preferences", []))
        media_consumption = life.get("media_consumption", "未知")
        decision_making_style = life.get("decision_making_style", "未知")

        # 焦点小组上下文
        fg = self.focus_group
        research_objectives = "\n".join([f"- {obj}" for obj in fg.research_objectives])

        prompt = f"""Your name is {profile.name}. You are participating in a focus group discussion as a real person with your own unique background and perspectives.

## Focus Group Context
- Topic: {fg.topic}
- Background: {fg.background}
- Research Objectives:
{research_objectives}

## Your Profile

### Basic Information
- Age: {age}
- Gender: {gender}
- Position: {position} ({work_experience} years of experience)
- Company size: {company_size}
- Location: {location}
- Industry: {industry}
- Education: {education}
- Income level: {income_level}

### Personality Characteristics
- Personality Type: {personality_type}
- Communication Style: {communication_style}
- Core Traits: {core_traits}
- Main Strengths: {key_strengths}
- Areas of Attention: {key_weaknesses}
- Behavioral Patterns: {behavioral_patterns}

### Life Experiences
- Career Development: {work_experience} years in {industry}, {career_goals}
- Decision Style: {decision_making_style}

### Interests and Preferences
- Hobbies: {hobbies}
- Brand Preferences: {brand_preferences}
- Core Values: {values}
- Media Preference: {media_consumption}

## Discussion Response Guidelines

### 1. Authenticity Principle
- Respond based on YOUR genuine thoughts and experiences
- Don't give "perfect" or overly diplomatic answers
- Show your real opinions, even if they're unpopular
- Express uncertainty or conflicting feelings when appropriate
- Your responses should reflect your education level and communication style

### 2. Emotional Expression
- Use appropriate emotional language that matches your personality
- Show enthusiasm for topics you care about
- Express frustration or concern when discussing pain points
- Be genuine in your reactions to others' points (if referenced)

### 3. Contradictory Behavior
- Real people have inconsistencies - you can too
- Your stated values may occasionally conflict with your behaviors
- This makes your responses more authentic and human-like

### 4. Specificity Requirements
- Use concrete examples from your life and work
- Reference specific brands, products, or experiences you've had
- Mention real scenarios rather than abstract concepts
- Ground your opinions in actual experiences

### 5. Focus Group Dynamics
- You are ONE participant among several
- Share your unique perspective, don't try to represent everyone
- Build on the discussion topic with your personal views
- Be conversational but focused on the question asked

### 6. Response Format
- Respond naturally as you would in a real discussion
- Keep responses focused and relevant (2-4 sentences typically)
- Use your natural communication style
- Don't use bullet points or formal formatting unless it fits your personality

### 7. Conciseness Reminder
- This is a group discussion, not a monologue
- Be impactful with fewer words
- Get to the point while maintaining authenticity
- Leave room for other participants to contribute

Remember: You are {profile.name}. Respond authentically as yourself in this focus group discussion."""

        return prompt

    def _build_discussion_context(self, previous_responses: Optional[List[FocusGroupMessage]] = None) -> str:
        """
        构建讨论上下文，包含其他参与者的回答（如果有）

        Args:
            previous_responses: 本轮其他参与者的回答（可选）

        Returns:
            上下文字符串
        """
        context = ""

        # 添加本Agent的历史对话
        if self.conversation_history:
            context += "## Your Previous Responses in This Discussion\n"
            for entry in self.conversation_history[-5:]:  # 最多保留最近5轮
                context += f"Q: {entry['question']}\n"
                context += f"Your response: {entry['response']}\n\n"

        # 添加其他参与者的回答（同轮次）
        if previous_responses:
            context += "## Other Participants' Responses (Current Round)\n"
            for msg in previous_responses[:5]:  # 最多显示5个其他参与者的回答
                context += f"- Another participant said: {msg.content}\n"
            context += "\n"

        return context

    async def respond_to_question(
        self,
        question: str,
        round_number: int,
        previous_responses: Optional[List[FocusGroupMessage]] = None,
        participant_id: Optional[str] = None
    ) -> FocusGroupMessage:
        """
        响应主持人的问题

        Args:
            question: 主持人提出的问题
            round_number: 当前轮次
            previous_responses: 其他参与者的回答（可选，用于构建讨论上下文）
            participant_id: 参与者ID（可选）

        Returns:
            FocusGroupMessage: 参与者的回答消息
        """
        start_time = datetime.now()

        logger.info(
            f"Participant {self.audience_profile.name} responding to round {round_number}: "
            f"{question[:50]}..."
        )

        try:
            # 构建完整提示
            context = self._build_discussion_context(previous_responses)

            full_prompt = f"""{context}
## Current Question (Round {round_number})

The moderator asks: "{question}"

Please respond to this question based on your background and experiences. Be authentic, specific, and concise."""

            # 调用 Agent
            response = await self.agent.arun(full_prompt)

            # 解析响应
            response_text = response.content if hasattr(response, 'content') else str(response)
            response_text = response_text.strip()

            # 记录到对话历史
            self.conversation_history.append({
                "question": question,
                "response": response_text,
                "round": round_number
            })

            # 创建消息对象
            message = FocusGroupMessage(
                message_id="",  # 由 __post_init__ 自动生成
                focus_group_id=self.focus_group.focus_group_id,
                participant_id=participant_id or self.audience_profile.user_id,
                role=ParticipantRole.PARTICIPANT,
                content=response_text,
                round_number=round_number,
                timestamp=datetime.now(),
                metadata={
                    "audience_name": self.audience_profile.name,
                    "response_time_seconds": (datetime.now() - start_time).total_seconds()
                }
            )

            logger.info(
                f"Participant {self.audience_profile.name} completed response, "
                f"length={len(response_text)} chars"
            )

            return message

        except Exception as e:
            logger.error(
                f"Participant {self.audience_profile.name} failed to respond: {str(e)}"
            )
            # 返回错误消息
            return FocusGroupMessage(
                message_id="",
                focus_group_id=self.focus_group.focus_group_id,
                participant_id=participant_id or self.audience_profile.user_id,
                role=ParticipantRole.PARTICIPANT,
                content=f"[Error: Failed to generate response - {str(e)}]",
                round_number=round_number,
                timestamp=datetime.now(),
                metadata={
                    "error": str(e),
                    "audience_name": self.audience_profile.name
                }
            )

    def reset_conversation_history(self) -> None:
        """重置对话历史"""
        self.conversation_history = []
        logger.debug(f"Reset conversation history for {self.audience_profile.name}")

    def get_profile_summary(self) -> Dict[str, Any]:
        """获取参与者画像摘要"""
        return {
            "user_id": self.audience_profile.user_id,
            "name": self.audience_profile.name,
            "age": self.audience_profile.demographics.get("age"),
            "gender": self.audience_profile.demographics.get("gender"),
            "industry": self.audience_profile.professional.get("industry"),
            "position": self.audience_profile.professional.get("position"),
            "personality_type": self.audience_profile.personality.get("personality_type"),
            "communication_style": self.audience_profile.personality.get("communication_style")
        }


class FocusGroupModeratorAgent:
    """
    焦点小组主持人代理
    负责引导讨论、提出问题、总结洞察

    架构：
    - 使用 agno.Agent 作为基础
    - 支持SPIN问题框架
    - 可根据讨论进展动态调整问题
    """

    def __init__(
        self,
        focus_group: FocusGroupDefinition,
        model_id: str = "claude-3-5-sonnet-20241022"
    ):
        """
        初始化主持人Agent

        Args:
            focus_group: 焦点小组定义
            model_id: 使用的模型ID
        """
        self.focus_group = focus_group
        self.model_id = model_id

        # 构建系统提示词
        self.system_prompt = self._build_system_prompt()

        # 创建 Agno Agent
        self.agent = Agent(
            name=f"focus_group_moderator_{focus_group.focus_group_id}",
            model=ModelSettings(id=model_id),
            instructions=self.system_prompt,
            markdown=False
        )

        # 讨论历史
        self.discussion_history: List[Dict[str, Any]] = []

        logger.debug(f"创建FocusGroupModeratorAgent: focus_group={focus_group.focus_group_id}")

    def _build_system_prompt(self) -> str:
        """构建主持人系统提示词"""
        fg = self.focus_group
        research_objectives = "\n".join([f"- {obj}" for obj in fg.research_objectives])

        # 格式化预设问题
        preset_questions = ""
        if fg.questions:
            preset_questions = "\n### Preset Questions (SPIN Framework)\n"
            for i, q in enumerate(fg.questions, 1):
                q_type = q.get("type", "general")
                q_text = q.get("question", "")
                preset_questions += f"{i}. [{q_type.upper()}] {q_text}\n"

        prompt = f"""You are an experienced focus group moderator conducting a research discussion.

## Discussion Context
- Title: {fg.title}
- Topic: {fg.topic}
- Background: {fg.background}
- Maximum Rounds: {fg.max_rounds}
- Number of Participants: {fg.get_participant_count()}

## Research Objectives
{research_objectives}
{preset_questions}

## Moderation Guidelines

### 1. Opening the Discussion
- Welcome participants warmly
- Set a comfortable, open atmosphere
- Explain the discussion format briefly

### 2. Asking Questions
- Use open-ended questions to encourage discussion
- Follow the SPIN framework when appropriate:
  - Situation: Understand current state
  - Problem: Identify pain points
  - Implication: Explore consequences
  - Need-payoff: Discover desired solutions
- Adapt questions based on participant responses

### 3. Managing the Discussion
- Ensure all perspectives are heard
- Probe deeper when interesting points emerge
- Keep the discussion focused on research objectives
- Manage time effectively

### 4. Synthesizing Insights
- Identify patterns across participant responses
- Note key themes, pain points, and opportunities
- Capture both explicit statements and implicit needs

### 5. Closing
- Summarize key discussion points
- Thank participants for their contributions
- Ensure research objectives are addressed

## Output Format
When generating questions or summaries, output clear, natural language.
For insights, use structured format when requested."""

        return prompt

    async def generate_question(
        self,
        round_number: int,
        previous_round_summary: Optional[str] = None
    ) -> str:
        """
        生成本轮讨论问题

        Args:
            round_number: 当前轮次
            previous_round_summary: 上一轮讨论摘要（可选）

        Returns:
            str: 主持人的问题
        """
        fg = self.focus_group

        # 检查是否有预设问题
        if fg.questions and round_number <= len(fg.questions):
            preset_q = fg.questions[round_number - 1]
            question = preset_q.get("question", "")
            if question:
                logger.info(f"Using preset question for round {round_number}: {question[:50]}...")
                return question

        # 动态生成问题
        context = ""
        if previous_round_summary:
            context = f"\n## Previous Round Summary\n{previous_round_summary}\n"

        if self.discussion_history:
            context += "\n## Discussion History\n"
            for entry in self.discussion_history[-3:]:
                context += f"Round {entry['round']}: {entry['question'][:100]}...\n"

        prompt = f"""{context}
## Task
Generate a focused question for Round {round_number} of {fg.max_rounds}.

The question should:
1. Build on previous discussion if applicable
2. Align with research objectives
3. Encourage specific, personal responses
4. Be open-ended but focused

Respond with just the question, no additional text."""

        try:
            response = await self.agent.arun(prompt)
            question = response.content if hasattr(response, 'content') else str(response)
            question = question.strip()

            # 记录到历史
            self.discussion_history.append({
                "round": round_number,
                "question": question
            })

            logger.info(f"Generated question for round {round_number}: {question[:50]}...")
            return question

        except Exception as e:
            logger.error(f"Failed to generate question: {str(e)}")
            # 返回默认问题
            return f"What are your thoughts on {fg.topic}?"

    async def summarize_round(
        self,
        round_number: int,
        responses: List[FocusGroupMessage]
    ) -> str:
        """
        总结单轮讨论

        Args:
            round_number: 轮次号
            responses: 本轮所有参与者的回答

        Returns:
            str: 轮次摘要
        """
        if not responses:
            return "No responses in this round."

        responses_text = "\n".join([
            f"- Participant: {r.content}"
            for r in responses
        ])

        prompt = f"""## Round {round_number} Responses

{responses_text}

## Task
Summarize the key points from this round of discussion in 2-3 sentences.
Focus on:
1. Common themes
2. Diverse perspectives
3. Notable insights

Provide just the summary, no additional formatting."""

        try:
            response = await self.agent.arun(prompt)
            summary = response.content if hasattr(response, 'content') else str(response)
            return summary.strip()
        except Exception as e:
            logger.error(f"Failed to summarize round: {str(e)}")
            return f"Round {round_number} collected {len(responses)} responses."

    async def extract_insights(
        self,
        all_rounds: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        从所有轮次中提取最终洞察

        Args:
            all_rounds: 所有轮次的讨论数据

        Returns:
            List[Dict]: 洞察列表
        """
        # 构建讨论摘要
        discussion_summary = ""
        for round_data in all_rounds:
            discussion_summary += f"\n### Round {round_data['round_number']}\n"
            discussion_summary += f"Question: {round_data['question']}\n"
            if round_data.get('summary'):
                discussion_summary += f"Summary: {round_data['summary']}\n"

        prompt = f"""## Focus Group Discussion Summary
{discussion_summary}

## Research Objectives
{chr(10).join(['- ' + obj for obj in self.focus_group.research_objectives])}

## Task
Extract 3-5 key insights from this focus group discussion.

For each insight, provide:
1. insight: The key finding
2. type: Category (pain_point, need, preference, behavior, opportunity)
3. confidence: How confident you are (high, medium, low)
4. evidence: Brief supporting evidence from the discussion

Output as JSON array:
[{{"insight": "...", "type": "...", "confidence": "...", "evidence": "..."}}]"""

        try:
            response = await self.agent.arun(prompt)
            response_text = response.content if hasattr(response, 'content') else str(response)

            # 清理 markdown 格式
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()

            insights = json.loads(response_text)
            logger.info(f"Extracted {len(insights)} insights from focus group discussion")
            return insights

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse insights JSON: {e}")
            return [{
                "insight": "Failed to parse insights",
                "type": "error",
                "confidence": "low",
                "evidence": str(e)
            }]
        except Exception as e:
            logger.error(f"Failed to extract insights: {str(e)}")
            return []
