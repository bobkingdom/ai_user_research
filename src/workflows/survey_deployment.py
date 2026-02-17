"""
问卷批量投放工作流 - 基于 Agno Teams
支持100-500并发的问卷批量投放，使用Agno Teams实现
"""

import logging
import asyncio
import uuid
from typing import List, Optional
from datetime import datetime

from agno import Team
from src.core.models import SurveyDefinition, AudienceProfile, SurveyResponse, DeploymentResult
from src.agents.survey_agent import SurveyAgent
from src.utils.concurrency import ConcurrencyManager
from src.utils.task_manager import TaskManager

logger = logging.getLogger(__name__)


class SurveyDeployment:
    """
    问卷批量投放编排器
    
    架构：
    - 使用 Agno Teams 管理多个 SurveyAgent
    - 使用 ConcurrencyManager 控制并发
    - 使用 TaskManager 防止重复任务
    - 支持 100-500 并发规模
    """
    
    def __init__(
        self,
        max_concurrency: Optional[int] = None,
        model_id: str = "claude-3-5-sonnet-20241022"
    ):
        """
        初始化问卷投放编排器
        
        Args:
            max_concurrency: 最大并发数，默认使用 ConcurrencyManager.SURVEY_MAX_CONCURRENCY
            model_id: 使用的模型ID
        """
        self.concurrency_manager = ConcurrencyManager.for_survey()
        if max_concurrency:
            self.concurrency_manager.max_concurrency = max_concurrency
            
        self.task_manager = TaskManager()
        self.model_id = model_id
        
        logger.info(
            f"SurveyDeployment 初始化: max_concurrency={self.concurrency_manager.max_concurrency}, "
            f"model={model_id}"
        )
    
    async def deploy(
        self,
        survey: SurveyDefinition,
        audience_list: List[AudienceProfile],
        task_id: Optional[str] = None
    ) -> DeploymentResult:
        """
        批量投放问卷
        
        流程：
        1. 创建任务（防重复）
        2. 为每个受众创建 SurveyAgent
        3. 使用 ConcurrencyManager 控制并发执行
        4. 聚合结果并返回
        
        Args:
            survey: 问卷定义
            audience_list: 目标受众列表
            task_id: 可选的任务ID（用于任务追踪）
            
        Returns:
            DeploymentResult: 包含所有回答和统计信息
        """
        start_time = datetime.now()
        
        # 生成任务ID（如果未提供）
        if not task_id:
            task_id = str(uuid.uuid4())
        
        logger.info(
            f"🚀 开始问卷批量投放 - Task: {task_id}, Survey: {survey.survey_id}, "
            f"Audiences: {len(audience_list)}"
        )
        
        # Step 1: 创建任务（防重复）
        task_params = {
            "survey_id": survey.survey_id,
            "audience_ids": [aud.user_id for aud in audience_list],
            "task_type": "survey_deployment"
        }
        
        existing_task, is_new = await self.task_manager.get_or_create_task(
            task_key=task_id,
            task_params=task_params
        )
        
        if not is_new:
            logger.warning(f"任务 {task_id} 已存在，返回已存在的任务")
            return DeploymentResult(
                task_id=task_id,
                survey_id=survey.survey_id,
                total_audiences=len(audience_list),
                successful_responses=0,
                failed_responses=0,
                is_existing_task=True
            )
        
        # Step 2: 为每个受众创建 SurveyAgent 和对应的任务
        logger.info(f"📝 创建 {len(audience_list)} 个 SurveyAgent")
        
        # 创建异步任务列表
        async_tasks = []
        response_ids = []
        
        for audience in audience_list:
            # 生成 response_id
            response_id = f"{survey.survey_id}_{audience.user_id}_{uuid.uuid4().hex[:8]}"
            response_ids.append(response_id)
            
            # 创建 SurveyAgent
            agent = SurveyAgent(
                audience_profile=audience,
                model_id=self.model_id
            )
            
            # 创建异步任务（包装为 lambda）
            async def answer_task(agent=agent, response_id=response_id):
                return await agent.answer_survey(survey, response_id)
            
            async_tasks.append(answer_task)
        
        # Step 3: 使用 ConcurrencyManager 并发执行
        logger.info(
            f"⚡ 开始并发执行 - max_concurrency={self.concurrency_manager.max_concurrency}"
        )
        
        try:
            # 使用带错误隔离的批量执行
            results = await self.concurrency_manager.execute_batch_with_isolation(
                tasks=async_tasks,
                max_concurrency=self.concurrency_manager.max_concurrency
            )
            
            # Step 4: 聚合结果
            successful_responses = []
            failed_responses = []
            errors = []
            
            for i, result in enumerate(results):
                if result["success"]:
                    survey_response = result["data"]
                    successful_responses.append(survey_response)
                else:
                    failed_responses.append(audience_list[i])
                    errors.append({
                        "audience_id": audience_list[i].user_id,
                        "audience_name": audience_list[i].name,
                        "error": result["error"]
                    })
            
            # 计算执行时间
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # 创建投放结果
            deployment_result = DeploymentResult(
                task_id=task_id,
                survey_id=survey.survey_id,
                total_audiences=len(audience_list),
                successful_responses=len(successful_responses),
                failed_responses=len(failed_responses),
                responses=successful_responses,
                errors=errors,
                execution_time_seconds=execution_time,
                is_existing_task=False
            )
            
            # 更新任务状态
            await self.task_manager.update_task_status(
                task_key=task_id,
                status="completed",
                result=deployment_result.to_dict()
            )
            
            logger.info(
                f"✅ 问卷投放完成 - Task: {task_id}, "
                f"成功: {len(successful_responses)}/{len(audience_list)}, "
                f"耗时: {execution_time:.2f}秒, "
                f"成功率: {deployment_result.success_rate:.1f}%"
            )
            
            return deployment_result
            
        except Exception as e:
            logger.error(f"❌ 问卷投放失败 - Task: {task_id}, Error: {str(e)}")
            
            # 更新任务状态为失败
            await self.task_manager.update_task_status(
                task_key=task_id,
                status="failed",
                result={"error": str(e)}
            )
            
            # 返回失败结果
            return DeploymentResult(
                task_id=task_id,
                survey_id=survey.survey_id,
                total_audiences=len(audience_list),
                successful_responses=0,
                failed_responses=len(audience_list),
                errors=[{"error": str(e)}],
                execution_time_seconds=(datetime.now() - start_time).total_seconds(),
                is_existing_task=False
            )
    
    async def get_task_status(self, task_id: str) -> Optional[dict]:
        """
        获取任务执行状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务状态信息，如果任务不存在返回 None
        """
        task = await self.task_manager.get_task(task_id)
        if not task:
            return None
        
        return {
            "task_id": task_id,
            "status": task.status,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "result": task.result
        }
