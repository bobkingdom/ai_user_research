"""
并发控制管理器
提供带限流的批量任务执行能力
"""

import asyncio
from typing import List, Callable, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ConcurrencyManager:
    """
    并发控制管理器

    功能：
    1. 基于 asyncio.Semaphore 的并发限流
    2. 支持不同场景的并发配置
    3. 批量任务执行与错误隔离
    """

    # 场景二：问卷投放并发配置
    SURVEY_MAX_CONCURRENCY = 100
    SURVEY_BATCH_SIZE = 50

    # 场景三：焦点小组并发配置
    FOCUS_GROUP_MAX_CONCURRENCY = 50
    FOCUS_GROUP_BATCH_SIZE = 20

    def __init__(self, max_concurrency: Optional[int] = None):
        """
        初始化并发管理器

        Args:
            max_concurrency: 最大并发数，如果未指定则使用默认值
        """
        self.max_concurrency = max_concurrency or self.SURVEY_MAX_CONCURRENCY
        self._semaphore = asyncio.Semaphore(self.max_concurrency)
        logger.info(f"ConcurrencyManager 初始化: max_concurrency={self.max_concurrency}")

    async def execute_batch(
        self,
        tasks: List[Callable],
        max_concurrency: Optional[int] = None,
        return_exceptions: bool = False
    ) -> List[Any]:
        """
        带限流的批量执行

        Args:
            tasks: 异步任务函数列表
            max_concurrency: 最大并发数（覆盖实例配置）
            return_exceptions: 是否返回异常而不是抛出

        Returns:
            任务执行结果列表
        """
        # 如果指定了新的并发数，创建新的信号量
        if max_concurrency and max_concurrency != self.max_concurrency:
            semaphore = asyncio.Semaphore(max_concurrency)
            logger.info(f"使用自定义并发数: {max_concurrency}")
        else:
            semaphore = self._semaphore

        async def limited_task(task: Callable) -> Any:
            """带限流的任务执行"""
            async with semaphore:
                return await task()

        logger.info(f"开始批量执行: total_tasks={len(tasks)}, max_concurrency={max_concurrency or self.max_concurrency}")

        # 执行所有任务
        results = await asyncio.gather(
            *[limited_task(task) for task in tasks],
            return_exceptions=return_exceptions
        )

        # 统计执行结果
        success_count = sum(1 for r in results if not isinstance(r, Exception))
        failed_count = len(results) - success_count

        logger.info(
            f"批量执行完成: total={len(results)}, success={success_count}, failed={failed_count}"
        )

        return results

    async def execute_batch_with_isolation(
        self,
        tasks: List[Callable],
        max_concurrency: Optional[int] = None
    ) -> List[dict]:
        """
        带错误隔离的批量执行
        单个任务失败不影响整体，返回统一格式的结果

        Args:
            tasks: 异步任务函数列表
            max_concurrency: 最大并发数

        Returns:
            结果列表，每个元素格式: {"success": bool, "data": Any, "error": str}
        """
        semaphore = asyncio.Semaphore(max_concurrency or self.max_concurrency)

        async def isolated_task(task: Callable) -> dict:
            """带错误隔离的任务执行"""
            async with semaphore:
                try:
                    result = await task()
                    return {"success": True, "data": result, "error": None}
                except Exception as e:
                    logger.warning(f"任务执行失败: {str(e)}")
                    return {"success": False, "data": None, "error": str(e)}

        logger.info(
            f"开始隔离批量执行: total_tasks={len(tasks)}, "
            f"max_concurrency={max_concurrency or self.max_concurrency}"
        )

        results = await asyncio.gather(*[isolated_task(task) for task in tasks])

        # 统计结果
        success_count = sum(1 for r in results if r["success"])
        failed_count = len(results) - success_count

        logger.info(
            f"隔离批量执行完成: total={len(results)}, "
            f"success={success_count}, failed={failed_count}"
        )

        return results

    async def execute_in_batches(
        self,
        tasks: List[Callable],
        batch_size: Optional[int] = None,
        max_concurrency: Optional[int] = None
    ) -> List[Any]:
        """
        分批次执行任务
        适用于超大规模任务场景

        Args:
            tasks: 异步任务函数列表
            batch_size: 每批次任务数量
            max_concurrency: 每批次内的最大并发数

        Returns:
            所有任务的执行结果
        """
        batch_size = batch_size or self.SURVEY_BATCH_SIZE
        max_concurrency = max_concurrency or self.max_concurrency

        logger.info(
            f"开始分批执行: total_tasks={len(tasks)}, "
            f"batch_size={batch_size}, max_concurrency={max_concurrency}"
        )

        all_results = []

        # 分批执行
        for i in range(0, len(tasks), batch_size):
            batch = tasks[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (len(tasks) + batch_size - 1) // batch_size

            logger.info(f"执行批次 {batch_num}/{total_batches}: {len(batch)} 个任务")

            batch_results = await self.execute_batch(
                batch,
                max_concurrency=max_concurrency,
                return_exceptions=True
            )
            all_results.extend(batch_results)

        logger.info(f"分批执行完成: 共处理 {len(all_results)} 个任务")

        return all_results

    @classmethod
    def for_survey(cls) -> "ConcurrencyManager":
        """创建问卷场景的并发管理器"""
        return cls(max_concurrency=cls.SURVEY_MAX_CONCURRENCY)

    @classmethod
    def for_focus_group(cls) -> "ConcurrencyManager":
        """创建焦点小组场景的并发管理器"""
        return cls(max_concurrency=cls.FOCUS_GROUP_MAX_CONCURRENCY)
