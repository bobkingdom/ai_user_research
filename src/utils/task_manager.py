"""
任务管理器
提供防重复、进度跟踪的任务管理能力
"""

import asyncio
import uuid
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Task:
    """
    任务数据模型

    Attributes:
        task_id: 任务唯一标识
        task_key: 任务业务键（如 focus_group_id）
        params: 任务参数
        fingerprint: 任务指纹（用于防重复）
        status: 任务状态
        created_at: 创建时间
        started_at: 开始时间
        completed_at: 完成时间
        total_count: 总任务数
        completed_count: 已完成数
        success_count: 成功数
        failed_count: 失败数
        results: 任务结果列表
        error_message: 错误信息
    """
    task_id: str
    task_key: str
    params: Dict[str, Any]
    fingerprint: str
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_count: int = 0
    completed_count: int = 0
    success_count: int = 0
    failed_count: int = 0
    results: List[Dict[str, Any]] = field(default_factory=list)
    error_message: Optional[str] = None

    @property
    def progress_percentage(self) -> float:
        """计算进度百分比"""
        if self.total_count == 0:
            return 0.0
        return round((self.completed_count / self.total_count) * 100, 2)

    @property
    def elapsed_seconds(self) -> Optional[float]:
        """计算已执行时间（秒）"""
        if not self.started_at:
            return None
        end_time = self.completed_at or datetime.now()
        return (end_time - self.started_at).total_seconds()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "task_key": self.task_key,
            "status": self.status.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "total_count": self.total_count,
            "completed_count": self.completed_count,
            "success_count": self.success_count,
            "failed_count": self.failed_count,
            "progress_percentage": self.progress_percentage,
            "elapsed_seconds": self.elapsed_seconds,
            "error_message": self.error_message,
            "results": self.results
        }


class TaskManager:
    """
    任务管理器

    功能：
    1. 防重复任务创建（基于指纹识别）
    2. 任务状态管理和进度跟踪
    3. 活跃任务索引（支持按业务键快速查询）
    4. 自动清理过期任务
    """

    _instance: Optional['TaskManager'] = None

    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        # 任务存储：task_id -> Task
        self.tasks: Dict[str, Task] = {}

        # 活跃任务索引：task_key -> task_id
        # 用于快速检查某个业务实体（如 focus_group_id）是否有正在运行的任务
        self.active_tasks: Dict[str, str] = {}

        # 锁，防止并发创建任务时的竞态条件
        self._lock = asyncio.Lock()

        # 任务清理配置
        self._task_retention = 300  # 已完成任务保留5分钟

        self._initialized = True
        logger.info("TaskManager 初始化完成")

    def _compute_fingerprint(self, task_params: Dict[str, Any]) -> str:
        """
        计算任务指纹（MD5哈希）

        Args:
            task_params: 任务参数

        Returns:
            16字符的MD5哈希值
        """
        # 提取关键参数并排序（确保顺序一致）
        fingerprint_parts = []
        for key in sorted(task_params.keys()):
            value = task_params[key]
            # 如果是列表，先排序
            if isinstance(value, list):
                value = sorted(value) if all(isinstance(x, (str, int)) for x in value) else value
            fingerprint_parts.append(f"{key}:{value}")

        fingerprint_str = "|".join(fingerprint_parts)
        return hashlib.md5(fingerprint_str.encode()).hexdigest()[:16]

    async def get_or_create_task(
        self,
        task_key: str,
        task_params: Dict[str, Any],
        total_count: Optional[int] = None
    ) -> tuple[Task, bool]:
        """
        获取或创建任务（防重复）

        Args:
            task_key: 任务业务键（如 "focus_group_123"）
            task_params: 任务参数（用于计算指纹）
            total_count: 总任务数（可选）

        Returns:
            (task, is_new) - 任务对象和是否为新创建
        """
        async with self._lock:
            # 计算任务指纹
            fingerprint = self._compute_fingerprint(task_params)

            # 检查是否有活跃任务
            existing_task_id = self.active_tasks.get(task_key)
            if existing_task_id:
                existing_task = self.tasks.get(existing_task_id)
                if existing_task and existing_task.status in [TaskStatus.PENDING, TaskStatus.PROCESSING]:
                    # 检查指纹是否相同
                    if existing_task.fingerprint == fingerprint:
                        logger.warning(
                            f"🔄 检测到重复任务: task_key={task_key}, "
                            f"existing_task_id={existing_task_id}, fingerprint={fingerprint}"
                        )
                        return existing_task, False
                    else:
                        # 不同的请求，但有任务在运行
                        logger.warning(
                            f"⚠️ task_key={task_key} 有任务运行中 ({existing_task_id})，"
                            f"但收到不同的请求（fingerprint不同）"
                        )
                        # 仍然返回现有任务，避免同时运行多个任务
                        return existing_task, False

            # 创建新任务
            task_id = f"task_{uuid.uuid4().hex[:12]}"
            task = Task(
                task_id=task_id,
                task_key=task_key,
                params=task_params,
                fingerprint=fingerprint,
                total_count=total_count or 0
            )

            self.tasks[task_id] = task
            self.active_tasks[task_key] = task_id

            logger.info(
                f"✅ 创建新任务: task_id={task_id}, task_key={task_key}, "
                f"fingerprint={fingerprint}, total_count={total_count}"
            )

            return task, True

    def get_task(self, task_id: str) -> Optional[Task]:
        """
        获取任务

        Args:
            task_id: 任务ID

        Returns:
            任务对象或 None
        """
        return self.tasks.get(task_id)

    def get_active_task(self, task_key: str) -> Optional[Task]:
        """
        获取指定业务键的活跃任务

        Args:
            task_key: 任务业务键

        Returns:
            活跃任务对象或 None
        """
        task_id = self.active_tasks.get(task_key)
        if task_id:
            task = self.tasks.get(task_id)
            if task and task.status in [TaskStatus.PENDING, TaskStatus.PROCESSING]:
                return task
        return None

    async def start_task(self, task_id: str) -> bool:
        """
        标记任务开始

        Args:
            task_id: 任务ID

        Returns:
            是否成功
        """
        task = self.tasks.get(task_id)
        if task and task.status == TaskStatus.PENDING:
            task.status = TaskStatus.PROCESSING
            task.started_at = datetime.now()
            logger.info(f"🚀 任务开始执行: task_id={task_id}")
            return True
        return False

    async def update_status(
        self,
        task_id: str,
        status: TaskStatus,
        error_message: Optional[str] = None
    ) -> bool:
        """
        更新任务状态

        Args:
            task_id: 任务ID
            status: 新状态
            error_message: 错误信息（可选）

        Returns:
            是否成功
        """
        task = self.tasks.get(task_id)
        if not task:
            return False

        task.status = status
        if error_message:
            task.error_message = error_message

        # 如果是完成状态，记录完成时间
        if status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
            task.completed_at = datetime.now()

            # 从活跃任务索引中移除
            if self.active_tasks.get(task.task_key) == task_id:
                del self.active_tasks[task.task_key]

            logger.info(
                f"✅ 任务完成: task_id={task_id}, status={status.value}, "
                f"elapsed={task.elapsed_seconds:.2f}s"
            )

            # 触发清理
            asyncio.create_task(self._cleanup_old_tasks())

        return True

    async def update_progress(
        self,
        task_id: str,
        result: Optional[Dict[str, Any]] = None,
        success: bool = True
    ) -> bool:
        """
        更新任务进度

        Args:
            task_id: 任务ID
            result: 单个任务结果（可选）
            success: 是否成功

        Returns:
            是否成功
        """
        task = self.tasks.get(task_id)
        if not task:
            return False

        task.completed_count += 1

        if success:
            task.success_count += 1
        else:
            task.failed_count += 1

        if result:
            task.results.append(result)

        # 定期记录进度
        if task.completed_count % 5 == 0 or task.completed_count == task.total_count:
            logger.info(
                f"📊 任务进度: task_id={task_id}, "
                f"{task.completed_count}/{task.total_count} ({task.progress_percentage}%)"
            )

        return True

    async def complete_task(
        self,
        task_id: str,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> bool:
        """
        完成任务

        Args:
            task_id: 任务ID
            success: 是否成功
            error_message: 错误信息（可选）

        Returns:
            是否成功
        """
        status = TaskStatus.COMPLETED if success else TaskStatus.FAILED
        return await self.update_status(task_id, status, error_message)

    async def _cleanup_old_tasks(self):
        """清理旧任务"""
        now = datetime.now()
        tasks_to_remove = []

        for task_id, task in self.tasks.items():
            # 只清理已完成的任务
            if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                if task.completed_at:
                    age = (now - task.completed_at).total_seconds()
                    if age > self._task_retention:
                        tasks_to_remove.append(task_id)

        for task_id in tasks_to_remove:
            del self.tasks[task_id]
            logger.debug(f"🧹 清理旧任务: task_id={task_id}")

        if tasks_to_remove:
            logger.info(f"🧹 清理了 {len(tasks_to_remove)} 个旧任务")


# 全局单例
_task_manager: Optional[TaskManager] = None


def get_task_manager() -> TaskManager:
    """获取任务管理器单例"""
    global _task_manager
    if _task_manager is None:
        _task_manager = TaskManager()
    return _task_manager
