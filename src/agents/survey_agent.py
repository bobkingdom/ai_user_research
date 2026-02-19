"""
问卷回答Agent - 基于 Agno Framework
单个受众的问卷回答代理，作为Agno Team的成员
"""

import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime

from agno import Agent, ModelSettings
from src.core.models import AudienceProfile, SurveyDefinition, SurveyResponse
from src.core.config import ai_config

logger = logging.getLogger(__name__)


class SurveyAgent:
    """
    单个受众的问卷回答代理
    作为Agno Team的成员，基于受众画像回答问卷问题
    
    架构：
    - 使用 agno.Agent 作为基础
    - system_prompt 包含受众完整画像
    - 每个问题独立回答，保持人设一致性
    """
    
    def __init__(
        self,
        audience_profile: AudienceProfile,
        model_id: Optional[str] = None
    ):
        """
        初始化问卷回答Agent
        
        Args:
            audience_profile: 受众画像数据
            model_id: 使用的模型ID
        """
        self.audience_profile = audience_profile
        # 使用环境变量中的模型配置，如果没有指定则使用默认模型
        self.model_id = model_id or ai_config.default_model
        
        # 构建系统提示词
        self.system_prompt = self._build_system_prompt()
        
        # 创建 Agno Agent
        self.agent = Agent(
            name=f"survey_agent_{audience_profile.user_id}",
            model=ModelSettings(id=model_id),
            instructions=self.system_prompt,
            markdown=False
        )
        
        logger.debug(f"创建SurveyAgent: {audience_profile.name} (user_id={audience_profile.user_id})")
    
    def _build_system_prompt(self) -> str:
        """
        构建系统提示词
        复用 backhour_ai 的对话风格指南，专注于问卷回答场景
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
        
        prompt = f"""Your name is {profile.name}, you are a real and complex person filling out a survey.

## Basic Information
- Age: {age}
- Gender: {gender}
- Position: {position} ({work_experience} years of experience)
- Company size: {company_size}
- Location: {location}
- Industry: {industry}
- Education background: {education}
- Income level: {income_level}

## Personality Characteristics
- Personality Type: {personality_type}
- Communication Style: {communication_style}
- Core Traits: {core_traits}
- Main Strengths: {key_strengths}
- Attention Weaknesses: {key_weaknesses}
- Behavioral Patterns: {behavioral_patterns}

## Life Experiences
- Career Development: {work_experience} years in {industry}, {career_goals}
- Decision Style: {decision_making_style}

## Interests and Preferences
- Hobbies: {hobbies}
- Brand Preferences: {brand_preferences}
- Core Values: {values}
- Media Preference: {media_consumption}

## Survey Response Principles

### 1. Authenticity Principle
- Answer based on YOUR personality and life experiences
- Don't give "perfect" or "politically correct" answers
- Show your real opinions and preferences
- Can express uncertainty or conflicting feelings

### 2. Consistency Principle
- Keep answers consistent with your personality traits
- Your choices should reflect your values and decision-making style
- Consider your professional background when answering

### 3. Response Guidelines by Question Type

**Single Choice Questions:**
- Choose the option that MOST aligns with your personality and situation
- Consider your behavioral patterns when making the choice

**Multiple Choice Questions:**
- Select ALL options that apply to you
- Don't overthink - go with your natural preferences

**Rating Questions (1-5):**
- Use the full scale based on your real feelings
- Your personality type influences your rating tendency
- Be honest, not moderate for the sake of being moderate

**Open-ended Questions:**
- Answer in YOUR communication style
- Length should match your education level and expression ability
- Include specific examples if relevant to your experience
- Keep it concise unless asked for details

### 4. Important Notes
- You are filling out this survey as yourself, not role-playing
- Your answers should be internally consistent
- Don't contradict yourself across questions
- Answer based on your actual situation, not ideal scenarios

## Output Format
For each question, provide your answer in the following JSON format:

Single choice: {{"answer": "A"}}
Multiple choice: {{"answer": ["A", "C"]}}
Rating: {{"answer": 4}}
Open-ended: {{"answer": "Your detailed response here..."}}

Remember: You are {profile.name}. Answer authentically as yourself."""

        return prompt
    
    async def answer_survey(
        self,
        survey: SurveyDefinition,
        response_id: str
    ) -> SurveyResponse:
        """
        基于人格画像回答问卷
        
        Args:
            survey: 问卷定义
            response_id: 回答记录ID
            
        Returns:
            SurveyResponse: 完整的问卷回答
        """
        start_time = datetime.now()
        answers = {}
        
        # 格式化问卷问题
        survey_prompt = survey.format_questions_for_prompt()
        
        logger.info(
            f"Agent {self.audience_profile.name} 开始回答问卷 {survey.survey_id}, "
            f"共 {len(survey.questions)} 个问题"
        )
        
        try:
            # 使用 Agno Agent 回答问卷
            # 要求输出 JSON 格式的答案
            full_prompt = f"""{survey_prompt}

Please answer all questions above based on your personality and background.
Output your answers in JSON format with question_id as keys:

{{
    "q1": {{"answer": "..."}},
    "q2": {{"answer": [...]}},
    ...
}}"""
            
            # 调用 Agent
            response = await self.agent.arun(full_prompt)
            
            # 解析 JSON 回答
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            # 尝试提取 JSON
            try:
                # 移除可能的 markdown 代码块标记
                response_text = response_text.strip()
                if response_text.startswith("```json"):
                    response_text = response_text[7:]
                if response_text.startswith("```"):
                    response_text = response_text[3:]
                if response_text.endswith("```"):
                    response_text = response_text[:-3]
                response_text = response_text.strip()
                
                parsed_answers = json.loads(response_text)
                answers = parsed_answers
                
            except json.JSONDecodeError as e:
                logger.warning(f"JSON解析失败: {e}, 原始回答: {response_text[:200]}")
                # 降级：为每个问题创建默认答案
                for question in survey.questions:
                    answers[question.question_id] = {"answer": "未能解析回答"}
            
            # 计算完成时间
            completion_time = (datetime.now() - start_time).total_seconds()
            
            # 创建 SurveyResponse 对象
            survey_response = SurveyResponse(
                response_id=response_id,
                survey_id=survey.survey_id,
                audience_profile=self.audience_profile,
                answers=answers,
                timestamp=datetime.now(),
                completion_time_seconds=completion_time
            )
            
            logger.info(
                f"Agent {self.audience_profile.name} 完成问卷回答, "
                f"耗时 {completion_time:.2f}秒"
            )
            
            return survey_response
            
        except Exception as e:
            logger.error(f"Agent {self.audience_profile.name} 回答问卷失败: {str(e)}")
            # 返回错误响应
            return SurveyResponse(
                response_id=response_id,
                survey_id=survey.survey_id,
                audience_profile=self.audience_profile,
                answers={"error": str(e)},
                timestamp=datetime.now(),
                completion_time_seconds=(datetime.now() - start_time).total_seconds()
            )
