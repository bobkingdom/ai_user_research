"""
核心数据模型定义（Pydantic BaseModel）
字段与老项目 backhour_ai/models/models.py ORM 实体完全对齐
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
from pydantic import BaseModel, Field, field_validator
import uuid


# ==================== 枚举类型 ====================

class QuestionType(str, Enum):
    SINGLE_CHOICE = "single_choice"
    MULTIPLE_CHOICE = "multiple_choice"
    OPEN_ENDED = "open_ended"

class GenerationStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class ParticipantRole(str, Enum):
    MODERATOR = "moderator"
    PARTICIPANT = "participant"

class FocusGroupStatus(str, Enum):
    PREPARING = "preparing"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"


# ==================== 意图分析模型（对齐 intent_analysis 表） ====================

class IntentAnalysis(BaseModel):
    user_input: str = Field(..., description="用户原始输入")
    intent: str = Field(default="", description="分析出的用户意图（原始JSON）")

    surface_intent: Optional[str] = Field(None, description="表层意图")
    deep_intent_primary: Optional[str] = Field(None, description="核心深层意图")
    deep_intent_secondary: Optional[List[str]] = Field(None, description="次要深层意图列表")
    psychological_motivations: Optional[List[str]] = Field(None, description="心理动机列表")
    social_motivations: Optional[List[str]] = Field(None, description="社会动机列表")
    functional_motivations: Optional[List[str]] = Field(None, description="功能动机列表")
    possible_scenarios: Optional[List[str]] = Field(None, description="可能的使用场景列表")
    constraints: Optional[List[str]] = Field(None, description="约束条件列表")
    thinking_pattern: Optional[str] = Field(None, description="思维模式分析")
    cognitive_biases: Optional[List[str]] = Field(None, description="认知偏差列表")
    decision_framework: Optional[str] = Field(None, description="决策框架分析")
    primary_users: Optional[List[Dict[str, Any]]] = Field(None, description="主要用户特征列表")
    decision_makers: Optional[List[Dict[str, Any]]] = Field(None, description="决策者特征列表")
    influencers: Optional[List[Dict[str, Any]]] = Field(None, description="影响者特征列表")
    communication_matrix: Optional[str] = Field(None, description="不同角色的沟通策略")
    recommended_approach: Optional[str] = Field(None, description="推荐的响应策略")
    focus_areas: Optional[List[str]] = Field(None, description="需要关注的领域列表")
    anticipated_needs: Optional[List[str]] = Field(None, description="预期的后续需求列表")

    key_concepts: Optional[str] = Field(None, description="关键概念")
    segment_count: int = Field(default=0, description="细分数量")
    audience_count: int = Field(default=0, description="受众数量")
    survey_requirements: Optional[Dict[str, Any]] = Field(None, description="问卷需求")
    target_region: Optional[str] = Field(None, description="目标地区")
    portrait_keywords: Optional[List[str]] = Field(None, description="画像关键词列表")
    generate_language: str = Field(default="English", description="生成内容使用的语言")
    reasoning: Optional[str] = Field(None, description="分析推理过程")


# ==================== 受众细分模型（对齐 audience_segment 表） ====================

class AudienceSegment(BaseModel):
    segment_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="细分唯一标识")
    name: str = Field(..., description="细分名称（对应 audience_segment 字段）")
    description: Optional[str] = Field(None, description="细分描述")
    portrait: Optional[Dict[str, Any]] = Field(None, description="画像数据JSON")
    primary_needs: Optional[List[str]] = Field(None, description="核心需求")
    pain_points: Optional[List[str]] = Field(None, description="痛点")
    usage_scenarios: Optional[List[str]] = Field(None, description="使用场景")
    key_benefits: Optional[List[str]] = Field(None, description="关键利益点")
    purchase_motivators: Optional[List[str]] = Field(None, description="购买动机")
    traits_tendency: Optional[Dict[str, Any]] = Field(
        None,
        description="特质倾向: {traits, openness, neuroticism, extraversion, agreeableness, conscientiousness, prevalence}"
    )
    target_count: int = Field(default=0, description="目标生成数量（推理层使用）")


# ==================== 受众人格模型（对齐 personality 表） ====================

class Personality(BaseModel):
    core_traits: List[str] = Field(default_factory=list, description="核心特质JSON数组")
    personality_type: str = Field(default="", description="MBTI人格类型")
    key_strengths: List[str] = Field(default_factory=list, description="关键优势JSON数组")
    key_weaknesses: List[str] = Field(default_factory=list, description="关键劣势JSON数组")

    behavioral_patterns: List[str] = Field(default_factory=list, description="行为模式JSON数组")
    communication_style: str = Field(default="", description="沟通风格")
    conflict_resolution: str = Field(default="", description="冲突处理方式")
    decision_process: str = Field(default="", description="决策过程")

    cognitive_biases: List[str] = Field(default_factory=list, description="认知偏差JSON数组")
    learning_style: str = Field(default="", description="学习风格")
    problem_solving_approach: str = Field(default="", description="问题解决方法")
    worldview: str = Field(default="", description="世界观")

    emotional_patterns: List[str] = Field(default_factory=list, description="情绪模式JSON数组")
    stress_responses: str = Field(default="", description="压力反应")
    coping_mechanisms: str = Field(default="", description="应对机制")
    emotional_triggers: List[str] = Field(default_factory=list, description="情绪触发器JSON数组")

    life_experiences: List[str] = Field(default_factory=list, description="人生经历JSON数组")
    growth_areas: List[str] = Field(default_factory=list, description="成长领域JSON数组")
    aspirations: List[str] = Field(default_factory=list, description="抱负JSON数组")

    background_event: str = Field(default="", description="背景事件")
    event_impact: str = Field(default="", description="事件影响")


# ==================== 受众画像模型（对齐 audience 表） ====================

class AudienceProfile(BaseModel):
    user_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="UUID唯一标识")
    name: str = Field(..., description="姓名")
    avatar: Optional[str] = Field(None, description="头像URL")

    age: int = Field(..., ge=0, le=120, description="年龄")
    gender: str = Field(..., description="性别")
    location: str = Field(..., description="地理位置")
    education: str = Field(..., description="教育程度")
    marital_status: str = Field(default="", description="婚姻状况")
    income_level: str = Field(..., description="收入水平")

    hobbies: List[str] = Field(default_factory=list, description="兴趣爱好")
    brand_preferences: List[str] = Field(default_factory=list, description="品牌偏好")
    leisure_activities: List[str] = Field(default_factory=list, description="休闲活动")
    media_consumption: str = Field(default="", description="媒体消费习惯")

    industry: str = Field(..., description="所属行业")
    position: str = Field(..., description="职位")
    work_experience: int = Field(default=0, ge=0, description="工作年限")
    company_size: str = Field(default="", description="公司规模")
    career_goals: str = Field(default="", description="职业目标")

    values: List[str] = Field(default_factory=list, description="核心价值观")
    life_attitudes: str = Field(default="", description="生活态度")
    decision_making_style: str = Field(default="", description="决策风格")
    risk_tolerance: str = Field(default="", description="风险承受度")
    social_style: str = Field(default="", description="社交风格")

    category_context: Optional[List[Dict[str, Any]]] = Field(None, description="分类上下文JSON数组")

    personality: Optional[Personality] = Field(None, description="人格特征（对应 personality 表）")

    segment_id: Optional[str] = Field(None, description="所属细分ID")

    @field_validator('user_id', mode='before')
    @classmethod
    def set_user_id(cls, v):
        return v or str(uuid.uuid4())

    def to_prompt(self) -> str:
        parts = [
            "# 受众画像\n",
            f"## 基础信息",
            f"- 姓名: {self.name}",
            f"- 年龄: {self.age}岁",
            f"- 性别: {self.gender}",
            f"- 地理位置: {self.location}",
            f"- 教育程度: {self.education}",
            f"- 婚姻状况: {self.marital_status}",
            f"- 收入水平: {self.income_level}\n",
            f"## 职业信息",
            f"- 所属行业: {self.industry}",
            f"- 职位: {self.position}",
            f"- 公司规模: {self.company_size}",
            f"- 工作年限: {self.work_experience}年",
            f"- 职业目标: {self.career_goals}\n",
            f"## 兴趣与生活方式",
            f"- 兴趣爱好: {', '.join(self.hobbies)}",
            f"- 品牌偏好: {', '.join(self.brand_preferences)}",
            f"- 休闲活动: {', '.join(self.leisure_activities)}",
            f"- 媒体消费: {self.media_consumption}",
            f"- 核心价值观: {', '.join(self.values)}",
            f"- 生活态度: {self.life_attitudes}",
            f"- 决策风格: {self.decision_making_style}",
            f"- 风险承受: {self.risk_tolerance}",
            f"- 社交风格: {self.social_style}\n",
        ]

        if self.personality:
            p = self.personality
            parts.extend([
                f"## 人格特征",
                f"- 人格类型: {p.personality_type}",
                f"- 沟通风格: {p.communication_style}",
                f"- 核心特质: {', '.join(p.core_traits)}",
                f"- 关键优势: {', '.join(p.key_strengths)}",
                f"- 关键弱点: {', '.join(p.key_weaknesses)}",
                f"- 行为模式: {', '.join(p.behavioral_patterns)}",
                f"- 冲突处理: {p.conflict_resolution}",
                f"- 决策过程: {p.decision_process}",
                f"- 认知偏差: {', '.join(p.cognitive_biases)}",
                f"- 学习风格: {p.learning_style}",
                f"- 解决问题: {p.problem_solving_approach}",
                f"- 世界观: {p.worldview}",
                f"- 情绪模式: {', '.join(p.emotional_patterns)}",
                f"- 压力反应: {p.stress_responses}",
                f"- 应对机制: {p.coping_mechanisms}",
                f"- 情绪触发: {', '.join(p.emotional_triggers)}",
                f"- 人生经历: {', '.join(p.life_experiences)}",
                f"- 成长领域: {', '.join(p.growth_areas)}",
                f"- 抱负: {', '.join(p.aspirations)}",
                f"- 背景事件: {p.background_event}",
                f"- 事件影响: {p.event_impact}\n",
            ])

        return "\n".join(parts)


# ==================== 问卷相关模型 ====================

class SurveyQuestion(BaseModel):
    question_id: str = Field(..., description="问题唯一标识")
    question_text: str = Field(..., description="问题内容")
    question_type: QuestionType = Field(..., description="问题类型")
    options: Optional[List[str]] = Field(None, description="选项列表（选择题）")
    required: bool = Field(default=True, description="是否必填")
    max_length: Optional[int] = Field(None, description="最大回答长度（开放题）")


class SurveyDefinition(BaseModel):
    survey_id: str = Field(..., description="问卷唯一标识")
    title: str = Field(..., description="问卷标题")
    description: str = Field(default="", description="问卷描述")
    questions: List[SurveyQuestion] = Field(default_factory=list, description="问题列表")
    target_audience_count: int = Field(default=0, description="目标受众数量")
    created_at: Optional[datetime] = Field(default=None, description="创建时间")

    def format_questions_for_prompt(self) -> str:
        formatted = f"# {self.title}\n\n{self.description}\n\n"
        for i, question in enumerate(self.questions, 1):
            formatted += f"{i}. {question.question_text}\n"
            if question.question_type == QuestionType.SINGLE_CHOICE:
                formatted += "   (单选题)\n"
                if question.options:
                    for opt_idx, option in enumerate(question.options, 1):
                        formatted += f"   {chr(64 + opt_idx)}. {option}\n"
            elif question.question_type == QuestionType.MULTIPLE_CHOICE:
                formatted += "   (多选题)\n"
                if question.options:
                    for opt_idx, option in enumerate(question.options, 1):
                        formatted += f"   {chr(64 + opt_idx)}. {option}\n"
            elif question.question_type == QuestionType.OPEN_ENDED:
                formatted += "   (开放题)\n"
            formatted += "\n"
        return formatted

    def get_question_by_id(self, question_id: str) -> Optional[SurveyQuestion]:
        for question in self.questions:
            if question.question_id == question_id:
                return question
        return None


class SurveyResponse(BaseModel):
    response_id: str = Field(..., description="回答唯一标识")
    survey_id: str = Field(..., description="问卷ID")
    audience_profile: AudienceProfile = Field(..., description="受众画像")
    answers: Dict[str, Any] = Field(default_factory=dict, description="question_id -> answer")
    timestamp: Optional[datetime] = Field(default=None, description="回答时间")
    completion_time_seconds: Optional[float] = Field(None, description="完成耗时秒数")


class DeploymentResult(BaseModel):
    task_id: str = Field(..., description="任务ID")
    survey_id: str = Field(..., description="问卷ID")
    total_audiences: int = Field(..., description="总受众数")
    successful_responses: int = Field(default=0, description="成功回答数")
    failed_responses: int = Field(default=0, description="失败回答数")
    responses: List[SurveyResponse] = Field(default_factory=list, description="回答列表")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="错误列表")
    execution_time_seconds: Optional[float] = Field(None, description="执行耗时")
    is_existing_task: bool = Field(default=False, description="是否为已存在任务")

    @property
    def success_rate(self) -> float:
        if self.total_audiences == 0:
            return 0.0
        return self.successful_responses / self.total_audiences * 100


# ==================== 受众生成任务模型 ====================

class GenerationTask(BaseModel):
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="任务ID")
    segment: AudienceSegment = Field(..., description="受众细分")
    status: GenerationStatus = Field(default=GenerationStatus.PENDING, description="任务状态")
    generated_profiles: List[AudienceProfile] = Field(default_factory=list, description="已生成画像列表")
    error_message: Optional[str] = Field(None, description="错误信息")
    started_at: Optional[datetime] = Field(None, description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")

    @property
    def progress_percentage(self) -> float:
        if self.segment.target_count == 0:
            return 0.0
        return len(self.generated_profiles) / self.segment.target_count * 100

    @property
    def is_complete(self) -> bool:
        return len(self.generated_profiles) >= self.segment.target_count


# ==================== 焦点小组模型 ====================

class FocusGroupParticipant(BaseModel):
    participant_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="参与者ID")
    audience_profile: AudienceProfile = Field(..., description="受众画像")
    role: ParticipantRole = Field(default=ParticipantRole.PARTICIPANT, description="角色")
    joined_at: Optional[datetime] = Field(default=None, description="加入时间")

    model_config = {"use_enum_values": True}


class FocusGroupDefinition(BaseModel):
    focus_group_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="焦点小组ID")
    title: str = Field(..., description="焦点小组标题")
    topic: str = Field(..., description="研究主题")
    background: str = Field(default="", description="背景信息")
    research_objectives: List[str] = Field(default_factory=list, description="研究目标列表")
    participants: List[FocusGroupParticipant] = Field(default_factory=list, description="参与者列表")
    questions: List[Dict[str, Any]] = Field(default_factory=list, description="SPIN问题框架")
    max_rounds: int = Field(default=5, description="最大讨论轮数")
    created_at: Optional[datetime] = Field(default=None, description="创建时间")

    def get_participant_count(self) -> int:
        return sum(1 for p in self.participants if p.role == ParticipantRole.PARTICIPANT)


class FocusGroupMessage(BaseModel):
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="消息ID")
    focus_group_id: str = Field(..., description="焦点小组ID")
    participant_id: str = Field(..., description="参与者ID")
    role: ParticipantRole = Field(..., description="角色")
    content: str = Field(..., description="消息内容")
    round_number: int = Field(..., description="轮次号")
    timestamp: Optional[datetime] = Field(default=None, description="时间戳")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据")

    model_config = {"use_enum_values": True}


class FocusGroupRoundResult(BaseModel):
    round_number: int = Field(..., description="轮次号")
    host_question: str = Field(..., description="主持人问题")
    responses: List[FocusGroupMessage] = Field(default_factory=list, description="回答列表")
    insights: List[str] = Field(default_factory=list, description="洞察列表")
    started_at: Optional[datetime] = Field(None, description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")

    @property
    def response_count(self) -> int:
        return len(self.responses)

    @property
    def duration_seconds(self) -> Optional[float]:
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


class FocusGroupSession(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="会话ID")
    definition: FocusGroupDefinition = Field(..., description="焦点小组定义")
    status: FocusGroupStatus = Field(default=FocusGroupStatus.PREPARING, description="状态")
    current_round: int = Field(default=0, description="当前轮次")
    rounds: List[FocusGroupRoundResult] = Field(default_factory=list, description="轮次结果列表")
    final_insights: List[Dict[str, Any]] = Field(default_factory=list, description="最终洞察")
    error_message: Optional[str] = Field(None, description="错误信息")
    started_at: Optional[datetime] = Field(None, description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")

    @property
    def progress_percentage(self) -> float:
        if self.definition.max_rounds == 0:
            return 0.0
        return (self.current_round / self.definition.max_rounds) * 100

    @property
    def total_messages(self) -> int:
        return sum(r.response_count for r in self.rounds)

    @property
    def duration_seconds(self) -> Optional[float]:
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    def start(self) -> None:
        self.status = FocusGroupStatus.ACTIVE
        self.started_at = datetime.now()

    def complete(self, insights: Optional[List[Dict[str, Any]]] = None) -> None:
        self.status = FocusGroupStatus.COMPLETED
        self.completed_at = datetime.now()
        if insights:
            self.final_insights = insights

    def fail(self, error_message: str) -> None:
        self.status = FocusGroupStatus.FAILED
        self.error_message = error_message
        self.completed_at = datetime.now()

    def add_round(self, round_result: FocusGroupRoundResult) -> None:
        self.rounds.append(round_result)
        self.current_round = round_result.round_number


# ==================== 模块导出 ====================

__all__ = [
    "QuestionType",
    "GenerationStatus",
    "ParticipantRole",
    "FocusGroupStatus",
    "IntentAnalysis",
    "AudienceSegment",
    "Personality",
    "AudienceProfile",
    "SurveyQuestion",
    "SurveyDefinition",
    "SurveyResponse",
    "DeploymentResult",
    "GenerationTask",
    "FocusGroupParticipant",
    "FocusGroupDefinition",
    "FocusGroupMessage",
    "FocusGroupRoundResult",
    "FocusGroupSession",
]
