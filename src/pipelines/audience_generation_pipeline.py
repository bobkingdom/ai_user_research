"""
受众生成流水线 - 基于 SmolaAgents Manager + Managed Agents 模式
实现流水线：基础信息生成 → 人格特征生成 → 行为模式生成
输出结构与 src/core/models.py 的 AudienceProfile（扁平结构）对齐
"""

import logging
import json
from typing import Dict, Any, Optional
from smolagents import ToolCallingAgent
from src.core.config import ai_config
from src.agents.generation_agents import create_all_generation_agents
from src.core.models import AudienceProfile, Personality
import uuid

logger = logging.getLogger(__name__)


class AudienceGenerationPipeline:
    """
    受众画像生成流水线

    架构：
    - Manager Agent：协调整个生成流程
    - Managed Agents：专业Agent负责各阶段生成
      - demographics_generator: 基础信息生成（扁平字段）
      - personality_generator: 人格特征生成（21字段 Personality）
      - lifestyle_generator: 生活方式生成（扁平字段）
      - profile_validator: 数据验证
      - data_merger: 数据整合

    流程：
    1. 描述 → demographics_generator → 扁平基础信息JSON
    2. 基础信息JSON → personality_generator → personality子对象JSON
    3. personality JSON → lifestyle_generator → 扁平生活方式JSON
    4. 三部分JSON → data_merger → 完整扁平画像JSON
    5. 完整画像JSON → profile_validator → 验证结果
    """

    def __init__(
        self,
        model_id: Optional[str] = None,
        max_steps: int = 15
    ):
        self.model_id = model_id or ai_config.default_smolagents_model
        self.max_steps = max_steps

        logger.info(f"🔧 初始化受众生成流水线，使用模型: {self.model_id}")
        self.managed_agents = create_all_generation_agents(self.model_id)

        self.manager_agent = self._create_manager_agent()

        logger.info("✅ 受众生成流水线初始化完成")

    def _create_manager_agent(self) -> ToolCallingAgent:
        system_prompt = """你是受众画像生成流程管理者。

你的任务是根据用户提供的受众描述，通过调用专业Agent生成完整的受众画像。

## 输出结构说明

最终输出是扁平结构的JSON，包含以下字段：
- 基础字段：name, age, gender, location, education, marital_status, income_level
- 职业字段：industry, position, company_size, work_experience, career_goals
- 生活方式字段：hobbies, values, brand_preferences, leisure_activities, media_consumption, decision_making_style, life_attitudes, risk_tolerance, social_style
- personality 子对象：包含21个字段的完整人格特征

## 工作流程

严格按以下顺序执行：

### 步骤1: 生成基础信息
- 调用 `demographics_generator` Agent
- 输入：受众描述文本
- 输出：扁平的基础信息JSON（name, age, gender, location, education, marital_status, income_level, industry, position, company_size, work_experience, career_goals）

### 步骤2: 生成人格特征
- 调用 `personality_generator` Agent
- 输入：步骤1的基础信息JSON字符串
- 输出：包含 personality 子对象的JSON字符串（21个字段）

### 步骤3: 生成生活方式
- 调用 `lifestyle_generator` Agent
- 输入：步骤1和步骤2的JSON字符串
- 输出：扁平的生活方式JSON（hobbies, values, brand_preferences, leisure_activities, media_consumption, decision_making_style, life_attitudes, risk_tolerance, social_style）

### 步骤4: 整合数据
- 调用 `data_merger` Agent
- 输入：步骤1的基础信息JSON、步骤2的人格特征JSON、步骤3的生活方式JSON
- 输出：完整的扁平受众画像JSON字符串

### 步骤5: 验证数据
- 调用 `profile_validator` Agent
- 输入：步骤4的完整画像JSON字符串
- 输出：验证结果JSON（包含 valid 布尔值和 errors 列表）

## 重要原则

1. **严格顺序执行**：必须按步骤1→2→3→4→5的顺序执行，不可跳过或调换
2. **数据传递**：每一步的输出是下一步的输入
3. **错误处理**：如果某一步失败，记录错误并停止流程
4. **验证必须**：生成完成后必须调用 validator 验证数据质量

## 最终输出

返回完整的扁平结构受众画像JSON字符串。

如果验证失败，报告验证错误。"""

        manager = ToolCallingAgent(
            tools=[],
            managed_agents=list(self.managed_agents.values()),
            model=self.model_id,
            system_prompt=system_prompt,
            max_steps=self.max_steps
        )

        logger.debug("创建 Manager Agent，负责协调受众生成流程")
        return manager

    async def generate_audience_profile(
        self,
        description: str,
        name: Optional[str] = None
    ) -> Dict[str, Any]:
        logger.info(f"🚀 开始生成受众画像: {description[:50]}...")

        try:
            task_prompt = f"""请根据以下描述生成完整的受众画像：

{description}

请严格按照流程执行：
1. 生成基础信息（扁平字段：name, age, gender, location, education, marital_status, income_level, industry, position, company_size, work_experience, career_goals）
2. 生成人格特征（personality 子对象，包含21个字段）
3. 生成生活方式（扁平字段：hobbies, values, brand_preferences, leisure_activities, media_consumption, decision_making_style, life_attitudes, risk_tolerance, social_style）
4. 整合数据
5. 验证数据质量

最后返回完整的受众画像JSON。"""

            logger.info("📞 调用 Manager Agent 执行生成流水线...")
            result = self.manager_agent.run(task_prompt)

            logger.debug(f"Manager Agent 返回结果: {str(result)[:200]}...")

            try:
                result_str = str(result)

                if "```json" in result_str:
                    result_str = result_str.split("```json")[1].split("```")[0]
                elif "```" in result_str:
                    result_str = result_str.split("```")[1].split("```")[0]

                result_str = result_str.strip()
                profile_data = json.loads(result_str)

                required_fields = ["name", "age", "gender", "location", "industry", "position"]
                missing_fields = [f for f in required_fields if f not in profile_data]

                if missing_fields:
                    logger.warning(f"⚠️ 生成的画像缺少字段: {missing_fields}")
                    return {
                        "success": False,
                        "profile": None,
                        "validation_errors": [f"缺少必填字段: {', '.join(missing_fields)}"],
                        "error_message": "数据不完整"
                    }

                user_id = str(uuid.uuid4())
                audience_name = name or profile_data.get("name", f"受众_{user_id[:8]}")

                personality_data = profile_data.pop("personality", None)
                personality = None
                if personality_data and isinstance(personality_data, dict):
                    personality = Personality(**personality_data)

                audience_profile = AudienceProfile(
                    user_id=user_id,
                    name=audience_name,
                    age=profile_data.get("age", 30),
                    gender=profile_data.get("gender", ""),
                    location=profile_data.get("location", ""),
                    education=profile_data.get("education", ""),
                    marital_status=profile_data.get("marital_status", ""),
                    income_level=profile_data.get("income_level", ""),
                    industry=profile_data.get("industry", ""),
                    position=profile_data.get("position", ""),
                    company_size=profile_data.get("company_size", ""),
                    work_experience=profile_data.get("work_experience", 0),
                    career_goals=profile_data.get("career_goals", ""),
                    hobbies=profile_data.get("hobbies", []),
                    brand_preferences=profile_data.get("brand_preferences", []),
                    leisure_activities=profile_data.get("leisure_activities", []),
                    media_consumption=profile_data.get("media_consumption", ""),
                    values=profile_data.get("values", []),
                    life_attitudes=profile_data.get("life_attitudes", ""),
                    decision_making_style=profile_data.get("decision_making_style", ""),
                    risk_tolerance=profile_data.get("risk_tolerance", ""),
                    social_style=profile_data.get("social_style", ""),
                    personality=personality,
                )

                logger.info(f"✅ 受众画像生成成功: {audience_name}")

                return {
                    "success": True,
                    "profile": audience_profile,
                    "validation_errors": [],
                    "error_message": None
                }

            except json.JSONDecodeError as e:
                logger.error(f"❌ JSON解析失败: {e}, 原始结果: {str(result)[:500]}")
                return {
                    "success": False,
                    "profile": None,
                    "validation_errors": [],
                    "error_message": f"JSON解析失败: {str(e)}"
                }

        except Exception as e:
            logger.error(f"❌ 受众画像生成失败: {str(e)}", exc_info=True)
            return {
                "success": False,
                "profile": None,
                "validation_errors": [],
                "error_message": str(e)
            }

    async def generate_audience_profile_sync(
        self,
        description: str,
        name: Optional[str] = None
    ) -> Dict[str, Any]:
        return await self.generate_audience_profile(description, name)
