"""
核心数据模型定义
包含受众画像、问卷定义、问卷回答等核心数据结构
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
import uuid


class QuestionType(Enum):
    """问题类型枚举"""
    SINGLE_CHOICE = "single_choice"
    MULTIPLE_CHOICE = "multiple_choice"
    TEXT = "text"
    RATING = "rating"


@dataclass
class AudienceProfile:
    """
    受众画像数据模型
    包含完整的受众信息：基础信息、职业、人格、生活方式
    """
    user_id: str
    name: str

    # 基础信息
    demographics: Dict[str, Any] = field(default_factory=dict)

    # 职业信息
    professional: Dict[str, Any] = field(default_factory=dict)

    # 人格特征
    personality: Dict[str, Any] = field(default_factory=dict)

    # 生活方式
    lifestyle: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "user_id": self.user_id,
            "name": self.name,
            "demographics": self.demographics,
            "professional": self.professional,
            "personality": self.personality,
            "lifestyle": self.lifestyle
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AudienceProfile":
        """从字典创建实例"""
        return cls(
            user_id=data.get("user_id", ""),
            name=data.get("name", ""),
            demographics=data.get("demographics", {}),
            professional=data.get("professional", {}),
            personality=data.get("personality", {}),
            lifestyle=data.get("lifestyle", {})
        )


@dataclass
class SurveyQuestion:
    """
    问卷问题模型
    支持单选、多选、文本、评分等多种题型
    """
    question_id: str
    question_text: str
    question_type: QuestionType
    options: Optional[List[str]] = None
    required: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "question_id": self.question_id,
            "question_text": self.question_text,
            "question_type": self.question_type.value,
            "options": self.options,
            "required": self.required
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SurveyQuestion":
        """从字典创建实例"""
        question_type = data.get("question_type", "text")
        if isinstance(question_type, str):
            question_type = QuestionType(question_type)

        return cls(
            question_id=data.get("question_id", ""),
            question_text=data.get("question_text", ""),
            question_type=question_type,
            options=data.get("options"),
            required=data.get("required", True)
        )


@dataclass
class SurveyDefinition:
    """
    问卷定义模型
    包含问卷的所有问题和元信息
    """
    survey_id: str
    title: str
    description: str
    questions: List[SurveyQuestion]
    target_audience_count: int = 0
    created_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "survey_id": self.survey_id,
            "title": self.title,
            "description": self.description,
            "questions": [q.to_dict() for q in self.questions],
            "target_audience_count": self.target_audience_count,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SurveyDefinition":
        """从字典创建实例"""
        questions_data = data.get("questions", [])
        questions = [SurveyQuestion.from_dict(q) for q in questions_data]

        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        return cls(
            survey_id=data.get("survey_id", ""),
            title=data.get("title", ""),
            description=data.get("description", ""),
            questions=questions,
            target_audience_count=data.get("target_audience_count", 0),
            created_at=created_at
        )

    def format_questions_for_prompt(self) -> str:
        """格式化问题为提示词格式"""
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

            elif question.question_type == QuestionType.RATING:
                formatted += "   (评分题: 1-5分)\n"

            elif question.question_type == QuestionType.TEXT:
                formatted += "   (开放题)\n"

            formatted += "\n"

        return formatted


@dataclass
class SurveyResponse:
    """
    问卷回答模型
    记录某个受众对问卷的完整回答
    """
    response_id: str
    survey_id: str
    audience_profile: AudienceProfile
    answers: Dict[str, Any]  # question_id -> answer
    timestamp: Optional[datetime] = None
    completion_time_seconds: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "response_id": self.response_id,
            "survey_id": self.survey_id,
            "audience_profile": self.audience_profile.to_dict(),
            "answers": self.answers,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "completion_time_seconds": self.completion_time_seconds
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SurveyResponse":
        """从字典创建实例"""
        audience_data = data.get("audience_profile", {})
        audience_profile = AudienceProfile.from_dict(audience_data)

        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)

        return cls(
            response_id=data.get("response_id", ""),
            survey_id=data.get("survey_id", ""),
            audience_profile=audience_profile,
            answers=data.get("answers", {}),
            timestamp=timestamp,
            completion_time_seconds=data.get("completion_time_seconds")
        )


@dataclass
class DeploymentResult:
    """
    投放结果模型
    包含投放的统计信息和所有回答
    """
    task_id: str
    survey_id: str
    total_audiences: int
    successful_responses: int
    failed_responses: int
    responses: List[SurveyResponse] = field(default_factory=list)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    execution_time_seconds: Optional[float] = None
    is_existing_task: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "task_id": self.task_id,
            "survey_id": self.survey_id,
            "total_audiences": self.total_audiences,
            "successful_responses": self.successful_responses,
            "failed_responses": self.failed_responses,
            "responses": [r.to_dict() for r in self.responses],
            "errors": self.errors,
            "execution_time_seconds": self.execution_time_seconds,
            "is_existing_task": self.is_existing_task
        }

    @property
    def success_rate(self) -> float:
        """计算成功率"""
        if self.total_audiences == 0:
            return 0.0
        return self.successful_responses / self.total_audiences * 100


# ==================== 场景四：受众生成流水线模型 ====================


class GenerationStatus(Enum):
    """受众生成任务状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AudienceSegment:
    """
    受众分群数据模型
    定义目标受众群体的特征和生成要求
    """
    segment_id: str
    name: str
    description: str
    target_count: int
    demographics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "segment_id": self.segment_id,
            "name": self.name,
            "description": self.description,
            "target_count": self.target_count,
            "demographics": self.demographics
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AudienceSegment":
        """从字典创建实例"""
        return cls(
            segment_id=data.get("segment_id", ""),
            name=data.get("name", ""),
            description=data.get("description", ""),
            target_count=data.get("target_count", 0),
            demographics=data.get("demographics", {})
        )


@dataclass
class GenerationTask:
    """
    受众生成任务模型
    记录批量生成的状态和结果
    """
    task_id: str
    segment: AudienceSegment
    status: GenerationStatus
    generated_profiles: List[AudienceProfile] = field(default_factory=list)
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "task_id": self.task_id,
            "segment": self.segment.to_dict(),
            "status": self.status.value,
            "generated_profiles": [p.to_dict() for p in self.generated_profiles],
            "error_message": self.error_message,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GenerationTask":
        """从字典创建实例"""
        segment_data = data.get("segment", {})
        segment = AudienceSegment.from_dict(segment_data)

        status = data.get("status", "pending")
        if isinstance(status, str):
            status = GenerationStatus(status)

        profiles_data = data.get("generated_profiles", [])
        profiles = [AudienceProfile.from_dict(p) for p in profiles_data]

        started_at = data.get("started_at")
        if isinstance(started_at, str):
            started_at = datetime.fromisoformat(started_at)

        completed_at = data.get("completed_at")
        if isinstance(completed_at, str):
            completed_at = datetime.fromisoformat(completed_at)

        return cls(
            task_id=data.get("task_id", ""),
            segment=segment,
            status=status,
            generated_profiles=profiles,
            error_message=data.get("error_message"),
            started_at=started_at,
            completed_at=completed_at
        )

    @property
    def progress_percentage(self) -> float:
        """计算生成进度百分比"""
        if self.segment.target_count == 0:
            return 0.0
        return len(self.generated_profiles) / self.segment.target_count * 100

    @property
    def is_complete(self) -> bool:
        """检查任务是否完成"""
        return len(self.generated_profiles) >= self.segment.target_count


# ==================== 场景三：焦点小组批量模型 ====================


class ParticipantRole(Enum):
    """参与者角色枚举"""
    MODERATOR = "moderator"      # 主持人
    PARTICIPANT = "participant"  # 参与者


class FocusGroupStatus(Enum):
    """焦点小组状态枚举"""
    PREPARING = "preparing"    # 准备中
    ACTIVE = "active"          # 进行中
    COMPLETED = "completed"    # 已完成
    FAILED = "failed"          # 失败


@dataclass
class FocusGroupParticipant:
    """
    焦点小组参与者模型
    将受众画像与焦点小组角色关联
    """
    participant_id: str
    audience_profile: AudienceProfile
    role: ParticipantRole = ParticipantRole.PARTICIPANT
    joined_at: Optional[datetime] = None

    def __post_init__(self):
        if not self.participant_id:
            self.participant_id = str(uuid.uuid4())
        if not self.joined_at:
            self.joined_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "participant_id": self.participant_id,
            "audience_profile": self.audience_profile.to_dict(),
            "role": self.role.value,
            "joined_at": self.joined_at.isoformat() if self.joined_at else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FocusGroupParticipant":
        """从字典创建实例"""
        audience_data = data.get("audience_profile", {})
        audience_profile = AudienceProfile.from_dict(audience_data)

        role = data.get("role", "participant")
        if isinstance(role, str):
            role = ParticipantRole(role)

        joined_at = data.get("joined_at")
        if isinstance(joined_at, str):
            joined_at = datetime.fromisoformat(joined_at)

        return cls(
            participant_id=data.get("participant_id", ""),
            audience_profile=audience_profile,
            role=role,
            joined_at=joined_at
        )


@dataclass
class FocusGroupDefinition:
    """
    焦点小组定义模型
    包含焦点小组的主题、背景、研究目标和SPIN问题框架
    """
    focus_group_id: str
    title: str
    topic: str
    background: str
    research_objectives: List[str]
    participants: List[FocusGroupParticipant] = field(default_factory=list)
    questions: List[Dict[str, Any]] = field(default_factory=list)  # SPIN问题框架
    max_rounds: int = 5
    created_at: Optional[datetime] = None

    def __post_init__(self):
        if not self.focus_group_id:
            self.focus_group_id = str(uuid.uuid4())
        if not self.created_at:
            self.created_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "focus_group_id": self.focus_group_id,
            "title": self.title,
            "topic": self.topic,
            "background": self.background,
            "research_objectives": self.research_objectives,
            "participants": [p.to_dict() for p in self.participants],
            "questions": self.questions,
            "max_rounds": self.max_rounds,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FocusGroupDefinition":
        """从字典创建实例"""
        participants_data = data.get("participants", [])
        participants = [FocusGroupParticipant.from_dict(p) for p in participants_data]

        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        return cls(
            focus_group_id=data.get("focus_group_id", ""),
            title=data.get("title", ""),
            topic=data.get("topic", ""),
            background=data.get("background", ""),
            research_objectives=data.get("research_objectives", []),
            participants=participants,
            questions=data.get("questions", []),
            max_rounds=data.get("max_rounds", 5),
            created_at=created_at
        )

    def get_participant_count(self) -> int:
        """获取参与者数量（不含主持人）"""
        return sum(1 for p in self.participants if p.role == ParticipantRole.PARTICIPANT)


@dataclass
class FocusGroupMessage:
    """
    焦点小组消息模型
    记录讨论过程中的每条消息
    """
    message_id: str
    focus_group_id: str
    participant_id: str
    role: ParticipantRole
    content: str
    round_number: int
    timestamp: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.message_id:
            self.message_id = str(uuid.uuid4())
        if not self.timestamp:
            self.timestamp = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "message_id": self.message_id,
            "focus_group_id": self.focus_group_id,
            "participant_id": self.participant_id,
            "role": self.role.value,
            "content": self.content,
            "round_number": self.round_number,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FocusGroupMessage":
        """从字典创建实例"""
        role = data.get("role", "participant")
        if isinstance(role, str):
            role = ParticipantRole(role)

        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)

        return cls(
            message_id=data.get("message_id", ""),
            focus_group_id=data.get("focus_group_id", ""),
            participant_id=data.get("participant_id", ""),
            role=role,
            content=data.get("content", ""),
            round_number=data.get("round_number", 0),
            timestamp=timestamp,
            metadata=data.get("metadata", {})
        )


@dataclass
class FocusGroupRoundResult:
    """
    焦点小组单轮讨论结果
    记录一轮讨论的问题、回答和洞察
    """
    round_number: int
    host_question: str
    responses: List[FocusGroupMessage] = field(default_factory=list)
    insights: List[str] = field(default_factory=list)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "round_number": self.round_number,
            "host_question": self.host_question,
            "responses": [r.to_dict() for r in self.responses],
            "insights": self.insights,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FocusGroupRoundResult":
        """从字典创建实例"""
        responses_data = data.get("responses", [])
        responses = [FocusGroupMessage.from_dict(r) for r in responses_data]

        started_at = data.get("started_at")
        if isinstance(started_at, str):
            started_at = datetime.fromisoformat(started_at)

        completed_at = data.get("completed_at")
        if isinstance(completed_at, str):
            completed_at = datetime.fromisoformat(completed_at)

        return cls(
            round_number=data.get("round_number", 0),
            host_question=data.get("host_question", ""),
            responses=responses,
            insights=data.get("insights", []),
            started_at=started_at,
            completed_at=completed_at
        )

    @property
    def response_count(self) -> int:
        """获取回答数量"""
        return len(self.responses)

    @property
    def duration_seconds(self) -> Optional[float]:
        """计算本轮讨论耗时"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


@dataclass
class FocusGroupSession:
    """
    焦点小组会话模型
    记录完整的焦点小组讨论状态和结果
    """
    session_id: str
    definition: FocusGroupDefinition
    status: FocusGroupStatus = FocusGroupStatus.PREPARING
    current_round: int = 0
    rounds: List[FocusGroupRoundResult] = field(default_factory=list)
    final_insights: List[Dict[str, Any]] = field(default_factory=list)
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    def __post_init__(self):
        if not self.session_id:
            self.session_id = str(uuid.uuid4())

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "session_id": self.session_id,
            "definition": self.definition.to_dict(),
            "status": self.status.value,
            "current_round": self.current_round,
            "rounds": [r.to_dict() for r in self.rounds],
            "final_insights": self.final_insights,
            "error_message": self.error_message,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FocusGroupSession":
        """从字典创建实例"""
        definition_data = data.get("definition", {})
        definition = FocusGroupDefinition.from_dict(definition_data)

        status = data.get("status", "preparing")
        if isinstance(status, str):
            status = FocusGroupStatus(status)

        rounds_data = data.get("rounds", [])
        rounds = [FocusGroupRoundResult.from_dict(r) for r in rounds_data]

        started_at = data.get("started_at")
        if isinstance(started_at, str):
            started_at = datetime.fromisoformat(started_at)

        completed_at = data.get("completed_at")
        if isinstance(completed_at, str):
            completed_at = datetime.fromisoformat(completed_at)

        return cls(
            session_id=data.get("session_id", ""),
            definition=definition,
            status=status,
            current_round=data.get("current_round", 0),
            rounds=rounds,
            final_insights=data.get("final_insights", []),
            error_message=data.get("error_message"),
            started_at=started_at,
            completed_at=completed_at
        )

    @property
    def progress_percentage(self) -> float:
        """计算讨论进度百分比"""
        if self.definition.max_rounds == 0:
            return 0.0
        return (self.current_round / self.definition.max_rounds) * 100

    @property
    def total_messages(self) -> int:
        """获取总消息数"""
        return sum(r.response_count for r in self.rounds)

    @property
    def duration_seconds(self) -> Optional[float]:
        """计算会话总耗时"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    def start(self) -> None:
        """开始会话"""
        self.status = FocusGroupStatus.ACTIVE
        self.started_at = datetime.now()

    def complete(self, insights: List[Dict[str, Any]] = None) -> None:
        """完成会话"""
        self.status = FocusGroupStatus.COMPLETED
        self.completed_at = datetime.now()
        if insights:
            self.final_insights = insights

    def fail(self, error_message: str) -> None:
        """标记会话失败"""
        self.status = FocusGroupStatus.FAILED
        self.error_message = error_message
        self.completed_at = datetime.now()

    def add_round(self, round_result: FocusGroupRoundResult) -> None:
        """添加一轮讨论结果"""
        self.rounds.append(round_result)
        self.current_round = round_result.round_number