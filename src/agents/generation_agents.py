"""
受众生成专业 Agents - 基于 SmolaAgents Framework
使用 ManagedAgent 模式，各Agent专注于特定生成任务
"""

import logging
from smolagents import ToolCallingAgent, ManagedAgent
from src.tools.audience_tools import (
    generate_demographics,
    generate_personality,
    generate_lifestyle,
    validate_audience_profile,
    merge_audience_data
)

logger = logging.getLogger(__name__)


# ==================== 专业 Agent 定义 ====================


def create_demographics_agent(model_id: str = "anthropic/claude-3-5-sonnet-20241022") -> ManagedAgent:
    """
    创建基础信息生成 Agent

    职责：
    - 根据受众描述生成人口统计信息
    - 生成职业背景信息
    - 确保基础信息逻辑一致

    Args:
        model_id: 使用的模型ID（默认使用Claude 3.5 Sonnet）

    Returns:
        ManagedAgent: 配置好的基础信息生成代理
    """
    base_agent = ToolCallingAgent(
        tools=[generate_demographics],
        model=model_id,
        max_steps=3
    )

    managed_agent = ManagedAgent(
        agent=base_agent,
        name="demographics_generator",
        description="生成受众基础人口统计信息和职业背景。根据受众描述，生成年龄、性别、地区、教育、收入等基础信息，以及行业、职位、工作年限等职业信息。"
    )

    logger.debug("创建 DemographicsAgent (ManagedAgent)")
    return managed_agent


def create_personality_agent(model_id: str = "anthropic/claude-3-5-sonnet-20241022") -> ManagedAgent:
    """
    创建人格特征生成 Agent

    职责：
    - 基于基础信息生成人格特征
    - 生成MBTI/Big Five人格类型
    - 定义沟通风格和行为模式
    - 识别核心优势和劣势

    Args:
        model_id: 使用的模型ID

    Returns:
        ManagedAgent: 配置好的人格特征生成代理
    """
    base_agent = ToolCallingAgent(
        tools=[generate_personality],
        model=model_id,
        max_steps=3
    )

    managed_agent = ManagedAgent(
        agent=base_agent,
        name="personality_generator",
        description="生成受众心理人格特征。基于受众基础信息，生成MBTI/Big Five人格类型、沟通风格、核心特质、优势劣势、行为模式等心理特征。确保人格特征与基础信息匹配（如：高管通常决策果断）。"
    )

    logger.debug("创建 PersonalityAgent (ManagedAgent)")
    return managed_agent


def create_lifestyle_agent(model_id: str = "anthropic/claude-3-5-sonnet-20241022") -> ManagedAgent:
    """
    创建生活方式生成 Agent

    职责：
    - 基于人格特征生成生活方式
    - 定义消费习惯和品牌偏好
    - 描述媒体使用习惯
    - 定义决策风格

    Args:
        model_id: 使用的模型ID

    Returns:
        ManagedAgent: 配置好的生活方式生成代理
    """
    base_agent = ToolCallingAgent(
        tools=[generate_lifestyle],
        model=model_id,
        max_steps=3
    )

    managed_agent = ManagedAgent(
        agent=base_agent,
        name="lifestyle_generator",
        description="生成受众生活方式和行为模式。基于人格特征，生成兴趣爱好、核心价值观、品牌偏好、媒体使用习惯、决策风格等行为模式。确保行为模式与人格特征一致。"
    )

    logger.debug("创建 LifestyleAgent (ManagedAgent)")
    return managed_agent


def create_validation_agent(model_id: str = "anthropic/claude-3-5-sonnet-20241022") -> ManagedAgent:
    """
    创建数据验证 Agent

    职责：
    - 验证受众画像数据完整性
    - 检查数据类型正确性
    - 验证逻辑一致性（年龄与职位匹配）
    - 验证内在关联性（人格与行为模式一致）

    Args:
        model_id: 使用的模型ID

    Returns:
        ManagedAgent: 配置好的数据验证代理
    """
    base_agent = ToolCallingAgent(
        tools=[validate_audience_profile],
        model=model_id,
        max_steps=2
    )

    managed_agent = ManagedAgent(
        agent=base_agent,
        name="profile_validator",
        description="验证完整受众画像的数据质量和一致性。检查必填字段完整性、数据类型正确性、逻辑一致性（如年龄与工作经验匹配）、内在关联性（如人格与行为模式一致）。"
    )

    logger.debug("创建 ValidationAgent (ManagedAgent)")
    return managed_agent


def create_merge_agent(model_id: str = "anthropic/claude-3-5-sonnet-20241022") -> ManagedAgent:
    """
    创建数据整合 Agent

    职责：
    - 整合三个阶段的生成结果
    - 合并为完整受众画像

    Args:
        model_id: 使用的模型ID

    Returns:
        ManagedAgent: 配置好的数据整合代理
    """
    base_agent = ToolCallingAgent(
        tools=[merge_audience_data],
        model=model_id,
        max_steps=2
    )

    managed_agent = ManagedAgent(
        agent=base_agent,
        name="data_merger",
        description="整合三个阶段的生成结果为完整受众画像。将基础信息、人格特征、生活方式三部分数据合并成完整的AudienceProfile。"
    )

    logger.debug("创建 MergeAgent (ManagedAgent)")
    return managed_agent


# ==================== Agent 工厂函数 ====================


def create_all_generation_agents(model_id: str = "anthropic/claude-3-5-sonnet-20241022") -> dict:
    """
    创建所有受众生成专业 Agents

    Args:
        model_id: 统一使用的模型ID

    Returns:
        dict: 包含所有专业Agent的字典
        {
            "demographics": ManagedAgent,
            "personality": ManagedAgent,
            "lifestyle": ManagedAgent,
            "validation": ManagedAgent,
            "merge": ManagedAgent
        }
    """
    agents = {
        "demographics": create_demographics_agent(model_id),
        "personality": create_personality_agent(model_id),
        "lifestyle": create_lifestyle_agent(model_id),
        "validation": create_validation_agent(model_id),
        "merge": create_merge_agent(model_id)
    }

    logger.info(f"✅ 创建了 {len(agents)} 个受众生成专业 Agents")
    return agents
