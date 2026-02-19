"""
配置管理模块
从环境变量中读取API Keys和模型配置
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class AIConfig(BaseSettings):
    """AI模型相关配置"""

    # API Keys
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None
    openrouter_api_url: str = "https://openrouter.ai/api/v1"

    # 模型配置
    openrouter_default_model: str = "google/gemini-3-flash-preview"
    openrouter_image_model: str = "google/gemini-3-pro-image-preview"
    openrouter_chat_model: str = "minimax/minimax-m2-her"
    openrouter_summary_model: Optional[str] = None

    # 默认模型（用于Agno等框架）
    default_model: str = "claude-3-5-sonnet-20241022"

    # SmolaAgents使用的模型（OpenRouter格式）
    default_smolagents_model: str = "anthropic/claude-3-5-sonnet-20241022"

    # 并发配置
    survey_max_concurrency: int = 100
    focus_group_max_concurrency: int = 50

    # 日志配置
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # 忽略额外的环境变量

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 优先使用OpenRouter模型，如果配置了OpenRouter API Key
        if self.openrouter_api_key:
            # 对于SmolaAgents，使用OpenRouter格式（但不需要加anthropic/前缀）
            # 因为OpenRouter的模型ID已经包含了提供商前缀
            self.default_smolagents_model = self.openrouter_default_model

            # 对于Agno，直接使用模型名称
            if self.openrouter_default_model.startswith("google/"):
                self.default_model = self.openrouter_default_model
            elif self.openrouter_chat_model:
                self.default_model = self.openrouter_chat_model
        else:
            # 回退到默认的Claude模型
            self.default_smolagents_model = "anthropic/claude-3-5-sonnet-20241022"

    @property
    def has_anthropic_key(self) -> bool:
        return bool(self.anthropic_api_key)

    @property
    def has_openai_key(self) -> bool:
        return bool(self.openai_api_key)

    @property
    def has_openrouter_key(self) -> bool:
        return bool(self.openrouter_api_key)

    @property
    def primary_api_provider(self) -> str:
        """返回主要使用的API提供商"""
        if self.has_openrouter_key:
            return "openrouter"
        elif self.has_anthropic_key:
            return "anthropic"
        elif self.has_openai_key:
            return "openai"
        else:
            return "none"


# 全局配置实例
ai_config = AIConfig()