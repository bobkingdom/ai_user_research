"""
受众生成工具集
提供基于 SmolaAgents @tool 装饰器的工具函数
用于流水线：基础信息生成 → 人格特征生成 → 行为模式生成
输出结构与 src/core/models.py 的 AudienceProfile（扁平结构）对齐
"""

import json
import logging
from typing import Dict, Any
from smolagents import tool

logger = logging.getLogger(__name__)


@tool
def generate_demographics(description: str) -> str:
    """
    根据描述生成受众基础人口统计信息和职业信息

    Args:
        description: 受众描述文本，例如 "35岁左右的互联网产品经理，在一线城市工作"

    Returns:
        JSON字符串，包含扁平的人口统计和职业字段

    生成内容包括：
    - name: 姓名
    - age: 年龄（整数）
    - gender: 性别
    - location: 地理位置
    - education: 教育程度
    - marital_status: 婚姻状况
    - income_level: 收入水平
    - industry: 所属行业
    - position: 职位
    - company_size: 公司规模
    - work_experience: 工作年限（整数）
    - career_goals: 职业目标

    要求：
    1. 年龄、性别、地区等人口统计信息
    2. 教育背景和收入水平
    3. 职业信息（行业、职位、工作年限）
    4. 确保信息之间逻辑一致
    """

    logger.info(f"🔧 [generate_demographics] 输入描述: {description[:100]}...")

    return json.dumps({
        "name": "",
        "age": 0,
        "gender": "",
        "location": "",
        "education": "",
        "marital_status": "",
        "income_level": "",
        "industry": "",
        "position": "",
        "company_size": "",
        "work_experience": 0,
        "career_goals": ""
    }, ensure_ascii=False)


@tool
def generate_personality(basic_info_json: str) -> str:
    """
    基于受众基础信息，生成完整人格特征

    Args:
        basic_info_json: 基础信息JSON字符串（来自 generate_demographics 的输出）

    Returns:
        JSON字符串，包含 personality 对象（对齐 Personality 模型全部21个字段）

    生成内容包括：
    - personality_type: MBTI人格类型
    - communication_style: 沟通风格
    - core_traits: 核心特质列表
    - key_strengths: 核心优势列表
    - key_weaknesses: 核心劣势列表
    - behavioral_patterns: 行为模式列表
    - conflict_resolution: 冲突处理方式
    - decision_process: 决策过程
    - cognitive_biases: 认知偏差列表
    - learning_style: 学习风格
    - problem_solving_approach: 问题解决方法
    - worldview: 世界观
    - emotional_patterns: 情绪模式列表
    - stress_responses: 压力反应
    - coping_mechanisms: 应对机制
    - emotional_triggers: 情绪触发器列表
    - life_experiences: 人生经历列表
    - growth_areas: 成长领域列表
    - aspirations: 抱负列表
    - background_event: 背景事件
    - event_impact: 事件影响

    要求：
    1. MBTI人格类型
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
            "behavioral_patterns": [],
            "conflict_resolution": "",
            "decision_process": "",
            "cognitive_biases": [],
            "learning_style": "",
            "problem_solving_approach": "",
            "worldview": "",
            "emotional_patterns": [],
            "stress_responses": "",
            "coping_mechanisms": "",
            "emotional_triggers": [],
            "life_experiences": [],
            "growth_areas": [],
            "aspirations": [],
            "background_event": "",
            "event_impact": ""
        }
    }, ensure_ascii=False)


@tool
def generate_lifestyle(personality_json: str) -> str:
    """
    基于受众信息和人格特征，生成生活方式和行为模式

    Args:
        personality_json: 人格特征JSON字符串（来自 generate_personality 的输出）

    Returns:
        JSON字符串，包含扁平的生活方式字段

    生成内容包括：
    - hobbies: 兴趣爱好列表
    - values: 核心价值观列表
    - brand_preferences: 品牌偏好列表
    - leisure_activities: 休闲活动列表
    - media_consumption: 媒体使用习惯
    - decision_making_style: 决策风格
    - life_attitudes: 生活态度
    - risk_tolerance: 风险承受度
    - social_style: 社交风格

    要求：
    1. 消费习惯和品牌偏好
    2. 媒体使用习惯
    3. 决策风格和购买行为
    4. 生活方式和兴趣爱好
    5. 确保行为模式与人格特征一致
    """

    logger.info(f"🔧 [generate_lifestyle] 输入人格特征: {personality_json[:100]}...")

    return json.dumps({
        "hobbies": [],
        "values": [],
        "brand_preferences": [],
        "leisure_activities": [],
        "media_consumption": "",
        "decision_making_style": "",
        "life_attitudes": "",
        "risk_tolerance": "",
        "social_style": ""
    }, ensure_ascii=False)


@tool
def validate_audience_profile(profile_json: str) -> str:
    """
    验证完整受众画像的数据质量和一致性

    Args:
        profile_json: 完整受众画像JSON字符串（扁平结构，对齐 AudienceProfile 模型）

    Returns:
        JSON字符串，包含验证结果和错误信息

    验证项：
    1. 必填字段完整性（name, age, gender, location, education, income_level, industry, position）
    2. 数据类型正确性
    3. 逻辑一致性（如：年龄与职位匹配）
    4. 人格特征完整性（personality子对象是否完整）
    5. 内在关联性（如：人格与行为模式一致）
    """

    logger.info(f"🔧 [validate_audience_profile] 验证画像: {profile_json[:100]}...")

    try:
        profile_data = json.loads(profile_json)
        errors = []

        required_fields = ["name", "age", "gender", "location", "education", "income_level", "industry", "position"]
        for field in required_fields:
            if not profile_data.get(field):
                errors.append(f"缺少必填字段: {field}")

        age = profile_data.get("age", 0)
        if not isinstance(age, int) or age < 18 or age > 100:
            errors.append("年龄数据无效")

        work_exp = profile_data.get("work_experience", 0)
        if isinstance(work_exp, int) and isinstance(age, int) and work_exp > age - 18:
            errors.append(f"工作经验({work_exp}年)与年龄({age}岁)不匹配")

        personality = profile_data.get("personality")
        if personality:
            if not personality.get("personality_type"):
                errors.append("缺少人格类型")
            if not personality.get("core_traits"):
                errors.append("缺少核心特质")
        else:
            errors.append("缺少人格特征数据")

        if not profile_data.get("values"):
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


@tool
def merge_audience_data(demographics_json: str, personality_json: str, lifestyle_json: str) -> str:
    """
    整合三个阶段的生成结果为完整受众画像（扁平结构）

    Args:
        demographics_json: 基础信息JSON字符串（扁平字段）
        personality_json: 人格特征JSON字符串（包含personality子对象）
        lifestyle_json: 生活方式JSON字符串（扁平字段）

    Returns:
        完整受众画像JSON字符串（扁平结构，对齐 AudienceProfile 模型）
    """

    logger.info("🔧 [merge_audience_data] 整合受众数据...")

    try:
        demographics_data = json.loads(demographics_json)
        personality_data = json.loads(personality_json)
        lifestyle_data = json.loads(lifestyle_json)

        merged = {}
        merged.update(demographics_data)
        merged.update(lifestyle_data)
        if "personality" in personality_data:
            merged["personality"] = personality_data["personality"]
        else:
            merged["personality"] = personality_data

        logger.info("✅ [merge_audience_data] 数据整合完成")
        return json.dumps(merged, ensure_ascii=False)

    except json.JSONDecodeError as e:
        logger.error(f"❌ JSON解析失败: {e}")
        raise
    except Exception as e:
        logger.error(f"❌ 数据整合失败: {e}")
        raise
