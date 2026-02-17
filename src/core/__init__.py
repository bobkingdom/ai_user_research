"""
核心数据模型模块
包含受众画像、问卷定义、问卷回答等核心数据结构
"""

from .models import (
    QuestionType,
    AudienceProfile,
    SurveyQuestion,
    SurveyDefinition,
    SurveyResponse,
    DeploymentResult,
    GenerationStatus,
    AudienceSegment,
    GenerationTask,
    ParticipantRole,
    FocusGroupStatus,
    FocusGroupParticipant,
    FocusGroupDefinition,
    FocusGroupMessage,
    FocusGroupRoundResult,
    FocusGroupSession,
)

__all__ = [
    "QuestionType",
    "AudienceProfile",
    "SurveyQuestion",
    "SurveyDefinition",
    "SurveyResponse",
    "DeploymentResult",
    "GenerationStatus",
    "AudienceSegment",
    "GenerationTask",
    "ParticipantRole",
    "FocusGroupStatus",
    "FocusGroupParticipant",
    "FocusGroupDefinition",
    "FocusGroupMessage",
    "FocusGroupRoundResult",
    "FocusGroupSession",
]
