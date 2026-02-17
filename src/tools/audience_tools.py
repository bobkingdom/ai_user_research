"""
受众生成工具集
提供基于 SmolaAgents @tool 装饰器的工具函数
用于三步流水线：基础信息生成 → 人格特征生成 → 行为模式生成
"""

import json
import logging
from typing import Dict, Any
from smolagents import tool

logger = logging.getLogger(__name__)


# ==================== 工具1: 基础信息生成 ====================

@tool
def generate_demographics(description: str) -> str:
    """
    根据描述生成受众基础人口统计信息

    Args:
        description: 受众描述文本，例如 "35岁左右的互联网产品经理，在一线城市工作"

    Returns:
        JSON字符串，包含 demographics 和 professional 字段

    生成内容包括：
    - demographics: age, gender, location, education, income_level
    - professional: industry, position, company_size, work_experience, career_goals

    要求：
    1. 年龄、性别、地区等人口统计信息
    2. 教育背景和收入水平
    3. 职业信息（行业、职位、工作年限）
    4. 确保信息之间逻辑一致
    """

    logger.info(f"🔧 [generate_demographics] 输入描述: {description[:100]}...")

    # 这是一个工具定义，实际执行由 ToolCallingAgent 完成
    # Agent 会调用 LLM 并自动填充返回值
    # 这里的实现不会被执行，仅作为文档和类型提示

    return json.dumps({
        "demographics": {
            "age": 0,
            "gender": "",
            "location": "",
            "education": "",
            "income_level": ""
        },
        "professional": {
            "industry": "",
            "position": "",
            "company_size": "",
            "work_experience": 0,
            "career_goals": ""
        }
    }, ensure_ascii=False)


# ==================== 工具2: 人格特征生成 ====================

@tool
def generate_personality(basic_info_json: str) -> str:
    """
    基于受众基础信息，生成人格特征

    Args:
        basic_info_json: 基础信息JSON字符串（来自 generate_demographics 的输出）

    Returns:
        JSON字符串，包含 personality 字段

    生成内容包括：
    - personality_type: MBTI/Big Five 人格类型
    - communication_style: 沟通风格
    - core_traits: 核心特质列表
    - key_strengths: 核心优势列表
    - key_weaknesses: 核心劣势列表
    - behavioral_patterns: 行为模式列表

    要求：
    1. MBTI/Big Five 人格类型
    2. 沟通风格和行为模式
    3. 核心优势和劣势
    4. 压力反应和冲突处理方式
    5. 确保与基础信息匹配（如：高管通常决策果断）
    """

    logger.info(f"🔧 [generate_personality] 输入基础信息: {basic_info_json[:100]}...")

    return json.dumps({
        "personality": {
            "personality_type": "",
            "communication_style": "",
            "core_traits": [],
            "key_strengths": [],
            "key_weaknesses": [],
            "behavioral_patterns": []
        }
    }, ensure_ascii=False)


# ==================== 工具3: 行为模式生成 ====================

@tool
def generate_lifestyle(personality_json: str) -> str:
    """
    基于受众信息和人格特征，生成生活方式和行为模式

    Args:
        personality_json: 人格特征JSON字符串（来自 generate_personality 的输出）

    Returns:
        JSON字符串，包含 lifestyle 字段

    生成内容包括：
    - hobbies: 兴趣爱好列表
    - values: 核心价值观列表
    - brand_preferences: 品牌偏好列表
    - media_consumption: 媒体使用习惯
    - decision_making_style: 决策风格

    要求：
    1. 消费习惯和品牌偏好
    2. 媒体使用习惯
    3. 决策风格和购买行为
    4. 生活方式和兴趣爱好
    5. 确保行为模式与人格特征一致
    """

    logger.info(f"🔧 [generate_lifestyle] 输入人格特征: {personality_json[:100]}...")

    return json.dumps({
        "lifestyle": {
            "hobbies": [],
            "values": [],
            "brand_preferences": [],
            "media_consumption": "",
            "decision_making_style": ""
        }
    }, ensure_ascii=False)


# ==================== 工具4: 数据验证 ====================

@tool
def validate_audience_profile(profile_json: str) -> str:
    """
    验证完整受众画像的数据质量和一致性

    Args:
        profile_json: 完整受众画像JSON字符串

    Returns:
        JSON字符串，包含验证结果和错误信息

    验证项：
    1. 必填字段完整性
    2. 数据类型正确性
    3. 逻辑一致性（如：年龄与职位匹配）
    4. 内在关联性（如：人格与行为模式一致）
    """

    logger.info(f"🔧 [validate_audience_profile] 验证画像: {profile_json[:100]}...")

    try:
        profile_data = json.loads(profile_json)
        errors = []

        # 基础字段检查
        required_fields = ["demographics", "professional", "personality", "lifestyle"]
        for field in required_fields:
            if field not in profile_data or not profile_data[field]:
                errors.append(f"缺少必填字段: {field}")

        # 人口统计信息检查
        if "demographics" in profile_data:
            demo = profile_data["demographics"]
            if not demo.get("age") or demo["age"] < 18 or demo["age"] > 100:
                errors.append("年龄数据无效")
            if not demo.get("gender"):
                errors.append("缺少性别信息")
            if not demo.get("location"):
                errors.append("缺少地区信息")

        # 职业信息检查
        if "professional" in profile_data:
            prof = profile_data["professional"]
            if not prof.get("industry"):
                errors.append("缺少行业信息")
            if not prof.get("position"):
                errors.append("缺少职位信息")
            work_exp = prof.get("work_experience", 0)
            age = profile_data.get("demographics", {}).get("age", 0)
            if work_exp > age - 18:
                errors.append(f"工作经验({work_exp}年)与年龄({age}岁)不匹配")

        # 人格特征检查
        if "personality" in profile_data:
            pers = profile_data["personality"]
            if not pers.get("personality_type"):
                errors.append("缺少人格类型")
            if not pers.get("core_traits"):
                errors.append("缺少核心特质")

        # 生活方式检查
        if "lifestyle" in profile_data:
            life = profile_data["lifestyle"]
            if not life.get("values"):
                errors.append("缺少核心价值观")

        if errors:
            return json.dumps({
                "valid": False,
                "errors": errors
            }, ensure_ascii=False)

        return json.dumps({
            "valid": True,
            "errors": []
        }, ensure_ascii=False)

    except json.JSONDecodeError as e:
        logger.error(f"❌ JSON解析失败: {e}")
        return json.dumps({
            "valid": False,
            "errors": [f"JSON格式错误: {str(e)}"]
        }, ensure_ascii=False)
    except Exception as e:
        logger.error(f"❌ 验证失败: {e}")
        return json.dumps({
            "valid": False,
            "errors": [f"验证异常: {str(e)}"]
        }, ensure_ascii=False)


# ==================== 工具5: 数据整合 ====================

@tool
def merge_audience_data(demographics_json: str, personality_json: str, lifestyle_json: str) -> str:
    """
    整合三个阶段的生成结果为完整受众画像

    Args:
        demographics_json: 基础信息JSON字符串
        personality_json: 人格特征JSON字符串
        lifestyle_json: 生活方式JSON字符串

    Returns:
        完整受众画像JSON字符串
    """

    logger.info("🔧 [merge_audience_data] 整合受众数据...")

    try:
        demographics_data = json.loads(demographics_json)
        personality_data = json.loads(personality_json)
        lifestyle_data = json.loads(lifestyle_json)

        merged = {
            "demographics": demographics_data.get("demographics", {}),
            "professional": demographics_data.get("professional", {}),
            "personality": personality_data.get("personality", {}),
            "lifestyle": lifestyle_data.get("lifestyle", {})
        }

        logger.info("✅ [merge_audience_data] 数据整合完成")
        return json.dumps(merged, ensure_ascii=False)

    except json.JSONDecodeError as e:
        logger.error(f"❌ JSON解析失败: {e}")
        raise
    except Exception as e:
        logger.error(f"❌ 数据整合失败: {e}")
        raise
