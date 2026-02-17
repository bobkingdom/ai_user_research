"""
受众生成流水线 - 基于 SmolaAgents Manager + Managed Agents 模式
实现三步流水线：基础信息生成 → 人格特征生成 → 行为模式生成
"""

import logging
import json
from typing import Dict, Any, Optional
from smolagents import ToolCallingAgent
from src.agents.generation_agents import create_all_generation_agents
from src.core.models import AudienceProfile
import uuid

logger = logging.getLogger(__name__)


class AudienceGenerationPipeline:
    """
    受众画像生成流水线

    架构：
    - Manager Agent：协调整个生成流程
    - Managed Agents：专业Agent负责各阶段生成
      - demographics_generator: 基础信息生成
      - personality_generator: 人格特征生成
      - lifestyle_generator: 生活方式生成
      - profile_validator: 数据验证
      - data_merger: 数据整合

    流程：
    1. 描述 → demographics_generator → 基础信息JSON
    2. 基础信息JSON → personality_generator → 人格特征JSON
    3. 人格特征JSON → lifestyle_generator → 生活方式JSON
    4. 三部分JSON → data_merger → 完整画像JSON
    5. 完整画像JSON → profile_validator → 验证结果
    """

    def __init__(
        self,
        model_id: str = "anthropic/claude-3-5-sonnet-20241022",
        max_steps: int = 15
    ):
        """
        初始化受众生成流水线

        Args:
            model_id: 使用的模型ID（对Manager和所有Managed Agents统一）
            max_steps: Manager Agent的最大执行步数
        """
        self.model_id = model_id
        self.max_steps = max_steps

        # 创建所有专业 Agents
        logger.info(f"🔧 初始化受众生成流水线，使用模型: {model_id}")
        self.managed_agents = create_all_generation_agents(model_id)

        # 创建 Manager Agent
        self.manager_agent = self._create_manager_agent()

        logger.info("✅ 受众生成流水线初始化完成")

    def _create_manager_agent(self) -> ToolCallingAgent:
        """
        创建 Manager Agent

        Manager Agent 负责：
        1. 解析用户输入的受众描述
        2. 按顺序调用专业 Agent 完成三步流水线
        3. 整合和验证最终结果
        4. 返回完整受众画像

        Returns:
            ToolCallingAgent: 配置好的Manager代理
        """
        system_prompt = """你是受众画像生成流程管理者。

你的任务是根据用户提供的受众描述，通过调用专业Agent生成完整的受众画像。

## 工作流程

严格按以下顺序执行：

### 步骤1: 生成基础信息
- 调用 `demographics_generator` Agent
- 输入：受众描述文本
- 输出：包含 demographics 和 professional 的JSON字符串

### 步骤2: 生成人格特征
- 调用 `personality_generator` Agent
- 输入：步骤1的基础信息JSON字符串
- 输出：包含 personality 的JSON字符串

### 步骤3: 生成生活方式
- 调用 `lifestyle_generator` Agent
- 输入：步骤2的人格特征JSON字符串（包含基础信息和人格特征）
- 输出：包含 lifestyle 的JSON字符串

### 步骤4: 整合数据
- 调用 `data_merger` Agent
- 输入：步骤1的基础信息JSON、步骤2的人格特征JSON、步骤3的生活方式JSON
- 输出：完整的受众画像JSON字符串

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

返回完整的受众画像JSON字符串，包含：
- demographics: 人口统计信息
- professional: 职业信息
- personality: 人格特征
- lifestyle: 生活方式

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
        """
        生成完整受众画像

        Args:
            description: 受众描述文本，例如 "35岁左右的互联网产品经理，在一线城市工作"
            name: 受众姓名（可选，如果不提供会自动生成）

        Returns:
            Dict[str, Any]: 完整受众画像数据，包含：
            {
                "success": bool,
                "profile": AudienceProfile or None,
                "validation_errors": list,
                "error_message": str or None
            }
        """
        logger.info(f"🚀 开始生成受众画像: {description[:50]}...")

        try:
            # 构建任务提示词
            task_prompt = f"""请根据以下描述生成完整的受众画像：

{description}

请严格按照流程执行：
1. 生成基础信息（demographics + professional）
2. 生成人格特征（personality）
3. 生成生活方式（lifestyle）
4. 整合数据
5. 验证数据质量

最后返回完整的受众画像JSON。"""

            # 调用 Manager Agent 执行流水线
            logger.info("📞 调用 Manager Agent 执行生成流水线...")
            result = self.manager_agent.run(task_prompt)

            # 解析结果
            logger.debug(f"Manager Agent 返回结果: {str(result)[:200]}...")

            # 尝试解析为JSON
            try:
                # 提取JSON字符串
                result_str = str(result)

                # 移除可能的markdown代码块
                if "```json" in result_str:
                    result_str = result_str.split("```json")[1].split("```")[0]
                elif "```" in result_str:
                    result_str = result_str.split("```")[1].split("```")[0]

                result_str = result_str.strip()
                profile_data = json.loads(result_str)

                # 验证数据完整性
                required_fields = ["demographics", "professional", "personality", "lifestyle"]
                missing_fields = [f for f in required_fields if f not in profile_data]

                if missing_fields:
                    logger.warning(f"⚠️ 生成的画像缺少字段: {missing_fields}")
                    return {
                        "success": False,
                        "profile": None,
                        "validation_errors": [f"缺少必填字段: {', '.join(missing_fields)}"],
                        "error_message": "数据不完整"
                    }

                # 创建 AudienceProfile 对象
                user_id = str(uuid.uuid4())
                audience_name = name or f"受众_{user_id[:8]}"

                audience_profile = AudienceProfile(
                    user_id=user_id,
                    name=audience_name,
                    demographics=profile_data.get("demographics", {}),
                    professional=profile_data.get("professional", {}),
                    personality=profile_data.get("personality", {}),
                    lifestyle=profile_data.get("lifestyle", {})
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
        """
        同步版本的受众生成（用于非异步环境）

        Args:
            description: 受众描述文本
            name: 受众姓名（可选）

        Returns:
            Dict[str, Any]: 受众画像生成结果
        """
        # 由于 smolagents 的 run 方法是同步的，这里直接调用
        return await self.generate_audience_profile(description, name)
