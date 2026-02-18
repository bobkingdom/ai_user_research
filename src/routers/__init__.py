"""
API 路由模块
"""
from .audience_router import router as audience_router
from .interview_router import router as interview_router
from .focus_group_router import router as focus_group_router
from .survey_router import router as survey_router

__all__ = [
    "audience_router",
    "interview_router",
    "focus_group_router",
    "survey_router",
]
