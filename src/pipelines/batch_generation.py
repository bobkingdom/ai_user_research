"""
批量受众生成管理器
支持大规模受众生成，包含并发控制、错误处理、进度追踪
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from src.pipelines.audience_generation_pipeline import AudienceGenerationPipeline
from src.core.models import AudienceSegment, GenerationTask, GenerationStatus, AudienceProfile
from src.utils.error_handler import ErrorHandler
import uuid

logger = logging.getLogger(__name__)


class BatchAudienceGenerator:
    """
    批量受众生成管理器

    功能：
    1. 批量生成多个受众画像
    2. 并发控制（避免API限流）
    3. 错误处理和重试机制
    4. 实时进度追踪
    5. 失败隔离（单个失败不影响整体）
    """

    def __init__(
        self,
        model_id: str = "anthropic/claude-3-5-sonnet-20241022",
        max_concurrency: int = 5,
        retry_config: Optional[Dict[str, Any]] = None
    ):
        """
        初始化批量生成管理器

        Args:
            model_id: 使用的模型ID
            max_concurrency: 最大并发数（控制API调用速率）
            retry_config: 重试配置，包含 max_retries, retry_delay, exponential_backoff
        """
        self.model_id = model_id
        self.max_concurrency = max_concurrency

        # 初始化错误处理器
        retry_config = retry_config or {}
        self.error_handler = ErrorHandler(
            max_retries=retry_config.get("max_retries", 3),
            retry_delay=retry_config.get("retry_delay", 1.0),
            exponential_backoff=retry_config.get("exponential_backoff", True)
        )

        # 创建生成流水线（每个任务会创建独立实例）
        self.pipeline_class = AudienceGenerationPipeline

        logger.info(
            f"🔧 初始化批量受众生成管理器: "
            f"model={model_id}, max_concurrency={max_concurrency}"
        )

    async def generate_batch(
        self,
        segment: AudienceSegment,
        progress_callback: Optional[callable] = None
    ) -> GenerationTask:
        """
        批量生成受众画像

        Args:
            segment: 受众分群定义（包含目标数量和描述）
            progress_callback: 进度回调函数 callback(current, total, profile)

        Returns:
            GenerationTask: 包含生成结果和状态的任务对象
        """
        task_id = str(uuid.uuid4())
        task = GenerationTask(
            task_id=task_id,
            segment=segment,
            status=GenerationStatus.PENDING,
            generated_profiles=[],
            error_message=None,
            started_at=None,
            completed_at=None
        )

        logger.info(
            f"🚀 开始批量生成任务: task_id={task_id}, "
            f"segment={segment.name}, target_count={segment.target_count}"
        )

        # 更新任务状态
        task.status = GenerationStatus.PROCESSING
        task.started_at = datetime.now()

        try:
            # 创建生成任务列表
            generation_tasks = []
            for i in range(segment.target_count):
                # 为每个受众添加编号
                description = f"{segment.description} (编号: {i+1}/{segment.target_count})"
                name = f"{segment.name}_{i+1}"

                generation_tasks.append({
                    "index": i,
                    "description": description,
                    "name": name
                })

            logger.info(f"📋 创建了 {len(generation_tasks)} 个生成任务")

            # 使用信号量控制并发
            semaphore = asyncio.Semaphore(self.max_concurrency)

            async def generate_single_with_limit(task_info: Dict[str, Any]) -> Dict[str, Any]:
                """带并发限制的单个受众生成"""
                async with semaphore:
                    return await self._generate_single_audience(
                        task_info=task_info,
                        progress_callback=progress_callback,
                        total_count=segment.target_count
                    )

            # 并发执行所有生成任务
            logger.info(f"🔄 开始并发生成，最大并发数: {self.max_concurrency}")
            results = await asyncio.gather(
                *[generate_single_with_limit(t) for t in generation_tasks],
                return_exceptions=True
            )

            # 处理结果
            successful_count = 0
            failed_count = 0

            for result in results:
                if isinstance(result, Exception):
                    # 异常情况
                    logger.error(f"❌ 生成任务异常: {str(result)}")
                    failed_count += 1
                elif result.get("success"):
                    # 成功生成
                    profile = result.get("profile")
                    if profile:
                        task.generated_profiles.append(profile)
                        successful_count += 1
                else:
                    # 生成失败
                    logger.warning(f"⚠️ 生成失败: {result.get('error_message')}")
                    failed_count += 1

            # 更新任务状态
            task.completed_at = datetime.now()

            if successful_count == segment.target_count:
                task.status = GenerationStatus.COMPLETED
                logger.info(
                    f"✅ 批量生成任务完成: task_id={task_id}, "
                    f"成功={successful_count}, 失败={failed_count}"
                )
            elif successful_count > 0:
                task.status = GenerationStatus.COMPLETED
                task.error_message = f"部分生成失败: {failed_count}/{segment.target_count} 个失败"
                logger.warning(
                    f"⚠️ 批量生成任务部分完成: task_id={task_id}, "
                    f"成功={successful_count}, 失败={failed_count}"
                )
            else:
                task.status = GenerationStatus.FAILED
                task.error_message = "所有生成任务均失败"
                logger.error(f"❌ 批量生成任务失败: task_id={task_id}")

            return task

        except Exception as e:
            logger.error(f"❌ 批量生成任务异常: {str(e)}", exc_info=True)
            task.status = GenerationStatus.FAILED
            task.error_message = str(e)
            task.completed_at = datetime.now()
            return task

    async def _generate_single_audience(
        self,
        task_info: Dict[str, Any],
        progress_callback: Optional[callable] = None,
        total_count: int = 0
    ) -> Dict[str, Any]:
        """
        生成单个受众画像（带重试）

        Args:
            task_info: 任务信息，包含 description, name, index
            progress_callback: 进度回调函数
            total_count: 总任务数（用于进度计算）

        Returns:
            Dict[str, Any]: 生成结果
            {
                "success": bool,
                "profile": AudienceProfile or None,
                "error_message": str or None
            }
        """
        description = task_info["description"]
        name = task_info["name"]
        index = task_info["index"]

        logger.debug(f"📝 开始生成受众 [{index+1}/{total_count}]: {name}")

        async def generate_task():
            """实际生成任务（用于重试包装）"""
            # 为每个任务创建独立的Pipeline实例（避免状态污染）
            pipeline = self.pipeline_class(model_id=self.model_id)
            return await pipeline.generate_audience_profile(
                description=description,
                name=name
            )

        try:
            # 使用错误处理器执行（带重试）
            result = await self.error_handler.with_retry(
                generate_task,
                retry_on=(Exception,)  # 所有异常都重试
            )

            # 调用进度回调
            if progress_callback and result.get("success"):
                profile = result.get("profile")
                try:
                    progress_callback(index + 1, total_count, profile)
                except Exception as e:
                    logger.warning(f"⚠️ 进度回调失败: {str(e)}")

            if result.get("success"):
                logger.debug(f"✅ 受众生成成功 [{index+1}/{total_count}]: {name}")
            else:
                logger.warning(
                    f"⚠️ 受众生成失败 [{index+1}/{total_count}]: {name}, "
                    f"错误: {result.get('error_message')}"
                )

            return result

        except Exception as e:
            logger.error(
                f"❌ 受众生成异常 [{index+1}/{total_count}]: {name}, 错误: {str(e)}",
                exc_info=True
            )
            return {
                "success": False,
                "profile": None,
                "error_message": str(e)
            }

    async def generate_multiple_segments(
        self,
        segments: List[AudienceSegment],
        progress_callback: Optional[callable] = None
    ) -> List[GenerationTask]:
        """
        生成多个受众分群

        Args:
            segments: 受众分群列表
            progress_callback: 进度回调函数

        Returns:
            List[GenerationTask]: 所有任务的结果列表
        """
        logger.info(f"🚀 开始生成 {len(segments)} 个受众分群")

        tasks = []
        for segment in segments:
            task = await self.generate_batch(
                segment=segment,
                progress_callback=progress_callback
            )
            tasks.append(task)

        logger.info(
            f"✅ 多分群生成完成: 总计 {len(tasks)} 个任务, "
            f"成功 {sum(1 for t in tasks if t.status == GenerationStatus.COMPLETED)} 个"
        )

        return tasks


# ==================== 辅助函数 ====================


def create_segment_from_description(
    name: str,
    description: str,
    target_count: int,
    portrait: Optional[Dict[str, Any]] = None
) -> AudienceSegment:
    """
    从描述创建受众分群

    Args:
        name: 分群名称
        description: 受众描述
        target_count: 目标生成数量
        portrait: 可选的画像数据JSON

    Returns:
        AudienceSegment: 受众分群对象
    """
    segment_id = str(uuid.uuid4())
    return AudienceSegment(
        segment_id=segment_id,
        name=name,
        description=description,
        target_count=target_count,
        portrait=portrait
    )


def print_generation_summary(task: GenerationTask) -> None:
    """
    打印生成任务摘要

    Args:
        task: 生成任务对象
    """
    print("\n" + "=" * 60)
    print(f"📊 受众生成任务摘要")
    print("=" * 60)
    print(f"任务ID: {task.task_id}")
    print(f"分群名称: {task.segment.name}")
    print(f"目标数量: {task.segment.target_count}")
    print(f"实际生成: {len(task.generated_profiles)}")
    print(f"任务状态: {task.status.value}")
    print(f"进度: {task.progress_percentage:.1f}%")

    if task.started_at and task.completed_at:
        duration = (task.completed_at - task.started_at).total_seconds()
        print(f"执行耗时: {duration:.2f}秒")

    if task.error_message:
        print(f"错误信息: {task.error_message}")

    print("=" * 60)

    # 打印前3个生成的受众样例
    if task.generated_profiles:
        print("\n📝 生成受众样例（前3个）:")
        for i, profile in enumerate(task.generated_profiles[:3]):
            print(f"\n[{i+1}] {profile.name}")
            print(f"  - 年龄: {profile.age}")
            print(f"  - 职位: {profile.position}")
            print(f"  - 人格类型: {profile.personality.personality_type if profile.personality else 'N/A'}")
        print()
