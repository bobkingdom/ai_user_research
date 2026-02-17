"""
焦点小组批量管理器
支持100-200个并发焦点小组的批量执行
"""

import logging
import asyncio
import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass, field

from src.core.models import (
    FocusGroupDefinition,
    FocusGroupSession,
    FocusGroupStatus,
    FocusGroupParticipant,
    AudienceProfile,
    ParticipantRole
)
from src.workflows.focus_group_workflow import FocusGroupWorkflow, SingleRoundFocusGroup
from src.utils.concurrency import ConcurrencyManager
from src.utils.task_manager import TaskManager, TaskStatus

logger = logging.getLogger(__name__)


@dataclass
class BatchFocusGroupResult:
    """
    批量焦点小组执行结果

    Attributes:
        batch_id: 批次ID
        total_groups: 总焦点小组数
        successful_groups: 成功完成的数量
        failed_groups: 失败的数量
        sessions: 所有会话结果
        errors: 错误列表
        execution_time_seconds: 执行耗时
    """
    batch_id: str
    total_groups: int
    successful_groups: int
    failed_groups: int
    sessions: List[FocusGroupSession] = field(default_factory=list)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    execution_time_seconds: Optional[float] = None
    is_existing_batch: bool = False

    @property
    def success_rate(self) -> float:
        """计算成功率"""
        if self.total_groups == 0:
            return 0.0
        return (self.successful_groups / self.total_groups) * 100

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "batch_id": self.batch_id,
            "total_groups": self.total_groups,
            "successful_groups": self.successful_groups,
            "failed_groups": self.failed_groups,
            "success_rate": self.success_rate,
            "sessions": [s.to_dict() for s in self.sessions],
            "errors": self.errors,
            "execution_time_seconds": self.execution_time_seconds,
            "is_existing_batch": self.is_existing_batch
        }


class BatchFocusGroupManager:
    """
    焦点小组批量管理器

    功能：
    1. 支持100-200个并发焦点小组
    2. 批量执行与结果聚合
    3. 任务防重复与进度追踪
    4. 错误隔离（单个失败不影响整体）

    使用场景：
    - 同一主题下，多个不同受众组合的焦点小组
    - A/B测试不同问题框架
    - 大规模市场研究
    """

    # 默认配置
    DEFAULT_MAX_CONCURRENT_GROUPS = 50  # 同时运行的最大焦点小组数
    DEFAULT_MAX_PARTICIPANTS_PER_GROUP = 20  # 每个小组最大参与者数

    def __init__(
        self,
        max_concurrent_groups: Optional[int] = None,
        max_participants_per_group: Optional[int] = None,
        model_id: str = "claude-3-5-sonnet-20241022"
    ):
        """
        初始化批量管理器

        Args:
            max_concurrent_groups: 最大并发焦点小组数
            max_participants_per_group: 每个小组最大参与者数（控制每组内的并发）
            model_id: 使用的模型ID
        """
        self.max_concurrent_groups = max_concurrent_groups or self.DEFAULT_MAX_CONCURRENT_GROUPS
        self.max_participants_per_group = max_participants_per_group or self.DEFAULT_MAX_PARTICIPANTS_PER_GROUP
        self.model_id = model_id

        # 使用 ConcurrencyManager 控制焦点小组级别的并发
        self.concurrency_manager = ConcurrencyManager(max_concurrency=self.max_concurrent_groups)

        # 任务管理
        self.task_manager = TaskManager()

        logger.info(
            f"BatchFocusGroupManager 初始化: "
            f"max_concurrent_groups={self.max_concurrent_groups}, "
            f"max_participants_per_group={self.max_participants_per_group}, "
            f"model={model_id}"
        )

    async def run_batch(
        self,
        definitions: List[FocusGroupDefinition],
        batch_id: Optional[str] = None
    ) -> BatchFocusGroupResult:
        """
        批量执行多个焦点小组

        Args:
            definitions: 焦点小组定义列表
            batch_id: 可选的批次ID

        Returns:
            BatchFocusGroupResult: 批量执行结果
        """
        start_time = datetime.now()

        if not batch_id:
            batch_id = f"batch_{uuid.uuid4().hex[:12]}"

        logger.info(
            f"🚀 开始批量焦点小组 - Batch: {batch_id}, "
            f"Groups: {len(definitions)}, Max Concurrent: {self.max_concurrent_groups}"
        )

        # 创建任务（防重复）
        task_params = {
            "batch_id": batch_id,
            "group_ids": [d.focus_group_id for d in definitions],
            "task_type": "batch_focus_group"
        }

        existing_task, is_new = await self.task_manager.get_or_create_task(
            task_key=batch_id,
            task_params=task_params,
            total_count=len(definitions)
        )

        if not is_new:
            logger.warning(f"批量任务 {batch_id} 已存在，返回当前状态")
            return BatchFocusGroupResult(
                batch_id=batch_id,
                total_groups=len(definitions),
                successful_groups=0,
                failed_groups=0,
                is_existing_batch=True
            )

        try:
            # 开始任务
            await self.task_manager.start_task(existing_task.task_id)

            # 创建焦点小组执行任务
            async_tasks = []
            for definition in definitions:
                async def run_group(defn=definition):
                    # 每个焦点小组使用独立的 FocusGroupWorkflow
                    workflow = FocusGroupWorkflow(
                        max_concurrency=self.max_participants_per_group,
                        model_id=self.model_id
                    )
                    session = await workflow.run_focus_group(definition=defn)

                    # 更新进度
                    success = session.status == FocusGroupStatus.COMPLETED
                    await self.task_manager.update_progress(
                        task_id=existing_task.task_id,
                        result={
                            "focus_group_id": defn.focus_group_id,
                            "status": session.status.value
                        },
                        success=success
                    )

                    return session

                async_tasks.append(run_group)

            # 使用错误隔离的批量执行
            results = await self.concurrency_manager.execute_batch_with_isolation(
                tasks=async_tasks,
                max_concurrency=self.max_concurrent_groups
            )

            # 聚合结果
            sessions = []
            errors = []
            successful_count = 0
            failed_count = 0

            for i, result in enumerate(results):
                if result["success"]:
                    session = result["data"]
                    sessions.append(session)
                    if session.status == FocusGroupStatus.COMPLETED:
                        successful_count += 1
                    else:
                        failed_count += 1
                        errors.append({
                            "focus_group_id": definitions[i].focus_group_id,
                            "error": session.error_message or "Unknown error"
                        })
                else:
                    failed_count += 1
                    errors.append({
                        "focus_group_id": definitions[i].focus_group_id,
                        "error": result["error"]
                    })

            # 完成任务
            execution_time = (datetime.now() - start_time).total_seconds()
            await self.task_manager.complete_task(existing_task.task_id, success=True)

            # 创建结果
            batch_result = BatchFocusGroupResult(
                batch_id=batch_id,
                total_groups=len(definitions),
                successful_groups=successful_count,
                failed_groups=failed_count,
                sessions=sessions,
                errors=errors,
                execution_time_seconds=execution_time,
                is_existing_batch=False
            )

            logger.info(
                f"✅ 批量焦点小组完成 - Batch: {batch_id}, "
                f"成功: {successful_count}/{len(definitions)}, "
                f"成功率: {batch_result.success_rate:.1f}%, "
                f"耗时: {execution_time:.2f}s"
            )

            return batch_result

        except Exception as e:
            logger.error(f"❌ 批量焦点小组失败 - Batch: {batch_id}, Error: {str(e)}")

            await self.task_manager.complete_task(
                existing_task.task_id,
                success=False,
                error_message=str(e)
            )

            return BatchFocusGroupResult(
                batch_id=batch_id,
                total_groups=len(definitions),
                successful_groups=0,
                failed_groups=len(definitions),
                errors=[{"error": str(e)}],
                execution_time_seconds=(datetime.now() - start_time).total_seconds(),
                is_existing_batch=False
            )

    async def run_single_question_batch(
        self,
        question: str,
        audience_groups: List[List[AudienceProfile]],
        topic: str = "Focus Group Discussion",
        background: str = "",
        batch_id: Optional[str] = None
    ) -> BatchFocusGroupResult:
        """
        批量执行单轮焦点小组（简化接口）

        用于向多组受众提出相同问题的场景

        Args:
            question: 要提出的问题
            audience_groups: 受众组列表，每组是一个受众画像列表
            topic: 讨论主题
            background: 背景信息
            batch_id: 可选的批次ID

        Returns:
            BatchFocusGroupResult: 批量执行结果
        """
        start_time = datetime.now()

        if not batch_id:
            batch_id = f"single_q_{uuid.uuid4().hex[:12]}"

        logger.info(
            f"🚀 开始单轮批量焦点小组 - Batch: {batch_id}, "
            f"Groups: {len(audience_groups)}, Question: {question[:50]}..."
        )

        # 创建焦点小组定义
        definitions = []
        for i, audience_profiles in enumerate(audience_groups):
            # 创建参与者列表
            participants = [
                FocusGroupParticipant(
                    participant_id=str(uuid.uuid4()),
                    audience_profile=profile,
                    role=ParticipantRole.PARTICIPANT
                )
                for profile in audience_profiles
            ]

            # 创建焦点小组定义
            definition = FocusGroupDefinition(
                focus_group_id=str(uuid.uuid4()),
                title=f"{topic} - Group {i + 1}",
                topic=topic,
                background=background,
                research_objectives=[],
                participants=participants,
                questions=[{"type": "general", "question": question}],
                max_rounds=1
            )
            definitions.append(definition)

        # 使用主批量执行方法
        return await self.run_batch(definitions, batch_id)

    async def run_parallel_response_collection(
        self,
        question: str,
        audience_profiles: List[AudienceProfile],
        topic: str = "Focus Group Discussion",
        background: str = ""
    ) -> List[Dict[str, Any]]:
        """
        并行收集大量受众对单个问题的回答

        这是最简单的使用模式：
        - 单个问题
        - 多个受众
        - 不分组
        - 高并发

        适用于100-200人规模的快速问答收集

        Args:
            question: 问题
            audience_profiles: 受众画像列表（100-200个）
            topic: 主题
            background: 背景

        Returns:
            List[Dict]: 每个受众的回答 [{audience_id, name, response, ...}]
        """
        logger.info(
            f"⚡ 并行收集回答: {len(audience_profiles)} 受众, "
            f"问题: {question[:50]}..."
        )

        # 使用 SingleRoundFocusGroup
        single_round = SingleRoundFocusGroup(
            max_concurrency=ConcurrencyManager.FOCUS_GROUP_MAX_CONCURRENCY,
            model_id=self.model_id
        )

        # 收集回答
        messages = await single_round.ask_question(
            question=question,
            audience_profiles=audience_profiles,
            topic=topic,
            background=background
        )

        # 格式化结果
        results = []
        for msg in messages:
            results.append({
                "participant_id": msg.participant_id,
                "audience_name": msg.metadata.get("audience_name"),
                "response": msg.content,
                "response_time_seconds": msg.metadata.get("response_time_seconds"),
                "timestamp": msg.timestamp.isoformat() if msg.timestamp else None
            })

        logger.info(f"✅ 并行收集完成: 收到 {len(results)}/{len(audience_profiles)} 回答")

        return results

    async def get_batch_status(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """
        获取批次执行状态

        Args:
            batch_id: 批次ID

        Returns:
            批次状态信息
        """
        task = self.task_manager.get_active_task(batch_id)
        if task:
            return task.to_dict()

        # 尝试从已完成任务中查找
        task = self.task_manager.get_task(batch_id)
        if task:
            return task.to_dict()

        return None


class FocusGroupFactory:
    """
    焦点小组工厂类

    提供便捷的焦点小组创建方法
    """

    @staticmethod
    def create_definition(
        topic: str,
        audience_profiles: List[AudienceProfile],
        questions: Optional[List[str]] = None,
        background: str = "",
        research_objectives: Optional[List[str]] = None,
        max_rounds: Optional[int] = None
    ) -> FocusGroupDefinition:
        """
        创建焦点小组定义

        Args:
            topic: 讨论主题
            audience_profiles: 参与者受众画像列表
            questions: 预设问题列表（可选）
            background: 背景信息
            research_objectives: 研究目标列表
            max_rounds: 最大讨论轮数

        Returns:
            FocusGroupDefinition: 焦点小组定义
        """
        # 创建参与者
        participants = [
            FocusGroupParticipant(
                participant_id=str(uuid.uuid4()),
                audience_profile=profile,
                role=ParticipantRole.PARTICIPANT
            )
            for profile in audience_profiles
        ]

        # 格式化问题
        formatted_questions = []
        if questions:
            for q in questions:
                formatted_questions.append({
                    "type": "general",
                    "question": q
                })

        # 确定轮数
        if max_rounds is None:
            max_rounds = len(formatted_questions) if formatted_questions else 3

        return FocusGroupDefinition(
            focus_group_id=str(uuid.uuid4()),
            title=f"焦点小组: {topic}",
            topic=topic,
            background=background,
            research_objectives=research_objectives or [],
            participants=participants,
            questions=formatted_questions,
            max_rounds=max_rounds
        )

    @staticmethod
    def create_multiple_definitions(
        topic: str,
        audience_groups: List[List[AudienceProfile]],
        questions: Optional[List[str]] = None,
        background: str = "",
        research_objectives: Optional[List[str]] = None,
        max_rounds: Optional[int] = None
    ) -> List[FocusGroupDefinition]:
        """
        创建多个焦点小组定义

        Args:
            topic: 讨论主题（所有小组共享）
            audience_groups: 多组受众画像
            questions: 预设问题列表
            background: 背景信息
            research_objectives: 研究目标
            max_rounds: 最大轮数

        Returns:
            List[FocusGroupDefinition]: 焦点小组定义列表
        """
        definitions = []
        for i, profiles in enumerate(audience_groups):
            definition = FocusGroupFactory.create_definition(
                topic=f"{topic} - Group {i + 1}",
                audience_profiles=profiles,
                questions=questions,
                background=background,
                research_objectives=research_objectives,
                max_rounds=max_rounds
            )
            definitions.append(definition)

        return definitions
