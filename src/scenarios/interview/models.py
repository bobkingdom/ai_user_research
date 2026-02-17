"""
Interview-specific data models.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class MessageRole(str, Enum):
    """消息角色枚举"""
    USER = "user"          # 研究人员
    ASSISTANT = "assistant"  # AI受众
    SYSTEM = "system"      # 系统提示


class InterviewStage(str, Enum):
    """访谈阶段枚举"""
    OPENING = "opening"              # 开场白
    SITUATION = "situation"          # SPIN-S: 现状探索
    PROBLEM = "problem"              # SPIN-P: 问题识别
    IMPLICATION = "implication"      # SPIN-I: 影响探究
    NEED_PAYOFF = "need_payoff"      # SPIN-N: 需求确认
    CUSTOM = "custom"                # 自由对话
    CLOSING = "closing"              # 结束总结


class InsightType(str, Enum):
    """洞察类型枚举"""
    PAIN_POINT = "pain_point"        # 痛点
    NEED = "need"                    # 需求
    PREFERENCE = "preference"        # 偏好
    BEHAVIOR = "behavior"            # 行为模式
    EMOTION = "emotion"              # 情感反应


class InterviewMessage(BaseModel):
    """访谈消息数据模型"""
    role: MessageRole = Field(..., description="消息角色")
    content: str = Field(..., description="消息内容")
    timestamp: datetime = Field(default_factory=datetime.now, description="时间戳")
    tool_calls: Optional[List[Dict[str, Any]]] = Field(None, description="工具调用(如有)")
    tool_results: Optional[List[Dict[str, Any]]] = Field(None, description="工具结果(如有)")

    class Config:
        use_enum_values = True


class Insight(BaseModel):
    """洞察数据模型"""
    content: str = Field(..., description="洞察内容")
    insight_type: InsightType = Field(..., description="洞察类型")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="置信度(0-1)")
    evidence: str = Field(..., description="证据(来自对话内容)")
    stage: Optional[InterviewStage] = Field(None, description="来源阶段")
    timestamp: datetime = Field(default_factory=datetime.now, description="提取时间")

    class Config:
        use_enum_values = True


class InterviewConfig(BaseModel):
    """访谈配置参数"""
    research_topic: str = Field(..., description="研究主题")
    research_objectives: List[str] = Field(..., description="研究目标")
    max_rounds: int = Field(20, description="最大对话轮数")
    timeout_seconds: int = Field(3600, description="超时时间(秒)")
    enable_mcp_tools: bool = Field(True, description="是否启用MCP工具")
    auto_extract_insights: bool = Field(True, description="是否自动提取洞察")
    model_id: str = Field("claude-3-5-sonnet-20241022", description="使用的模型ID")


class AudienceProfileForInterview(BaseModel):
    """
    受众画像数据模型 (用于访谈场景)

    包含人口统计、职业信息、人格特征、生活方式等完整信息
    """
    user_id: str = Field(..., description="唯一标识符(UUID)")
    name: str = Field(..., description="姓名")

    # 基础人口统计信息
    age: Optional[int] = Field(None, description="年龄")
    gender: Optional[str] = Field(None, description="性别")
    location: Optional[str] = Field(None, description="所在地")
    education: Optional[str] = Field(None, description="教育背景")
    income_level: Optional[str] = Field(None, description="收入水平")
    marital_status: Optional[str] = Field(None, description="婚姻状况")

    # 职业信息
    industry: Optional[str] = Field(None, description="所属行业")
    position: Optional[str] = Field(None, description="职位")
    company_size: Optional[str] = Field(None, description="公司规模")
    work_experience: Optional[int] = Field(None, description="工作年限")
    career_goals: Optional[str] = Field(None, description="职业目标")

    # 人格特征
    personality_type: Optional[str] = Field(None, description="人格类型(MBTI/Big Five)")
    communication_style: Optional[str] = Field(None, description="沟通风格")
    core_traits: Optional[List[str]] = Field(default_factory=list, description="核心性格特征")
    key_strengths: Optional[List[str]] = Field(default_factory=list, description="主要优势")
    key_weaknesses: Optional[List[str]] = Field(default_factory=list, description="主要劣势")
    behavioral_patterns: Optional[List[str]] = Field(default_factory=list, description="行为模式")

    # 生活方式
    hobbies: Optional[List[str]] = Field(default_factory=list, description="兴趣爱好")
    values: Optional[List[str]] = Field(default_factory=list, description="核心价值观")
    brand_preferences: Optional[List[str]] = Field(default_factory=list, description="品牌偏好")
    leisure_activities: Optional[List[str]] = Field(default_factory=list, description="休闲活动")
    media_consumption: Optional[str] = Field(None, description="媒体消费习惯")
    decision_making_style: Optional[str] = Field(None, description="决策风格")
    risk_tolerance: Optional[str] = Field(None, description="风险承受度")
    social_style: Optional[str] = Field(None, description="社交风格")
    life_attitudes: Optional[str] = Field(None, description="生活态度")

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式(用于生成提示词)"""
        return self.model_dump(exclude_none=True)

    def to_prompt_context(self) -> Dict[str, Any]:
        """生成用于提示词的上下文字典"""
        return {
            "name": self.name,
            "age": self.age or "unknown",
            "gender": self.gender or "unknown",
            "position": self.position or "unknown",
            "work_experience": self.work_experience or "many years",
            "company_size": self.company_size or "medium company",
            "location": self.location or "unknown",
            "industry": self.industry or "unknown",
            "education": self.education or "unknown",
            "income_level": self.income_level or "medium",
            "personality_type": self.personality_type or "",
            "communication_style": self.communication_style or "",
            "core_traits": ", ".join(self.core_traits) if self.core_traits else "",
            "key_strengths": ", ".join(self.key_strengths) if self.key_strengths else "",
            "key_weaknesses": ", ".join(self.key_weaknesses) if self.key_weaknesses else "",
            "behavioral_patterns": ", ".join(self.behavioral_patterns) if self.behavioral_patterns else "",
            "career_goals": self.career_goals or "want to gain more development",
            "life_attitudes": self.life_attitudes or "want to balance work and life",
            "decision_making_style": self.decision_making_style or "rational analysis",
            "risk_tolerance": self.risk_tolerance or "cautious",
            "marital_status": self.marital_status or "married",
            "social_style": self.social_style or "introverted",
            "media_consumption": self.media_consumption or "mainly through mobile and social media",
            "hobbies": ", ".join(self.hobbies) if self.hobbies else "unknown",
            "brand_preferences": ", ".join(self.brand_preferences) if self.brand_preferences else "unknown",
            "leisure_activities": ", ".join(self.leisure_activities) if self.leisure_activities else "simple life",
            "values": ", ".join(self.values) if self.values else "",
        }


class InterviewSession(BaseModel):
    """
    访谈会话数据模型

    管理完整的访谈生命周期
    """
    session_id: str = Field(..., description="会话唯一标识")
    audience_profile: AudienceProfileForInterview = Field(..., description="受众画像")
    config: InterviewConfig = Field(..., description="访谈配置")

    # 会话状态
    current_stage: InterviewStage = Field(InterviewStage.OPENING, description="当前阶段")
    messages: List[InterviewMessage] = Field(default_factory=list, description="对话历史")
    insights: List[Insight] = Field(default_factory=list, description="提取的洞察")

    # 元数据
    started_at: datetime = Field(default_factory=datetime.now, description="开始时间")
    ended_at: Optional[datetime] = Field(None, description="结束时间")
    is_active: bool = Field(True, description="是否活跃")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="额外元数据")

    def add_message(self, message: InterviewMessage):
        """添加消息到历史"""
        self.messages.append(message)

    def add_insight(self, insight: Insight):
        """添加洞察"""
        self.insights.append(insight)

    def get_conversation_history(self) -> List[Dict[str, str]]:
        """获取对话历史(Claude API格式)"""
        return [
            {"role": msg.role, "content": msg.content}
            for msg in self.messages
            if msg.role in [MessageRole.USER, MessageRole.ASSISTANT]
        ]

    def end_session(self):
        """结束会话"""
        self.is_active = False
        self.ended_at = datetime.now()

    class Config:
        use_enum_values = True


class InterviewSummary(BaseModel):
    """访谈总结数据模型"""
    session_id: str = Field(..., description="会话ID")
    total_messages: int = Field(..., description="总消息数")
    total_insights: int = Field(..., description="总洞察数")
    duration_seconds: int = Field(..., description="持续时间(秒)")

    # 按类型统计洞察
    insights_by_type: Dict[str, int] = Field(default_factory=dict, description="按类型统计洞察")

    # 关键发现
    key_findings: List[str] = Field(default_factory=list, description="关键发现")

    # 完整数据
    messages: List[InterviewMessage] = Field(default_factory=list, description="完整对话历史")
    insights: List[Insight] = Field(default_factory=list, description="完整洞察列表")

    metadata: Dict[str, Any] = Field(default_factory=dict, description="额外元数据")
