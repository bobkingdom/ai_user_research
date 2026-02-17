"""
工具模块测试示例
演示 ConcurrencyManager、ErrorHandler、TaskManager 的基本用法
"""

import asyncio
from src.utils import ConcurrencyManager, ErrorHandler, TaskManager, TaskStatus
from src.utils.error_handler import RateLimitError


async def test_concurrency_manager():
    """测试并发控制管理器"""
    print("\n=== 测试 ConcurrencyManager ===\n")

    # 创建并发管理器
    manager = ConcurrencyManager.for_survey()  # 问卷场景，100并发

    # 模拟任务
    async def mock_task(task_id: int):
        await asyncio.sleep(0.1)
        return f"Task {task_id} completed"

    # 批量执行
    tasks = [lambda i=i: mock_task(i) for i in range(20)]
    results = await manager.execute_batch(tasks, max_concurrency=5)
    print(f"✅ 批量执行完成: {len(results)} 个任务")

    # 错误隔离执行
    async def failing_task(task_id: int):
        if task_id % 3 == 0:
            raise ValueError(f"Task {task_id} failed")
        return f"Task {task_id} ok"

    tasks = [lambda i=i: failing_task(i) for i in range(10)]
    results = await manager.execute_batch_with_isolation(tasks, max_concurrency=3)
    success = sum(1 for r in results if r["success"])
    failed = sum(1 for r in results if not r["success"])
    print(f"✅ 隔离执行: 成功={success}, 失败={failed}")


async def test_error_handler():
    """测试错误处理器"""
    print("\n=== 测试 ErrorHandler ===\n")

    handler = ErrorHandler(max_retries=3, retry_delay=0.5, exponential_backoff=True)

    # 测试重试机制
    attempt_count = 0

    async def unstable_task():
        nonlocal attempt_count
        attempt_count += 1
        if attempt_count < 3:
            raise RateLimitError("Rate limit exceeded")
        return "Success after retries"

    result = await handler.with_retry(unstable_task)
    print(f"✅ 重试成功: {result}, 尝试次数={attempt_count}")

    # 测试装饰器
    @handler.retry_decorator(retry_on=(ValueError,), max_retries=2)
    async def decorated_task(should_fail: bool):
        if should_fail:
            raise ValueError("Task failed")
        return "Success"

    try:
        await decorated_task(should_fail=False)
        print("✅ 装饰器正常执行")
    except ValueError:
        print("❌ 装饰器执行失败")


async def test_task_manager():
    """测试任务管理器"""
    print("\n=== 测试 TaskManager ===\n")

    manager = TaskManager()

    # 创建任务
    task_params = {
        "focus_group_id": "123",
        "participant_ids": [1, 2, 3, 4, 5],
        "message": "Hello"
    }

    task1, is_new1 = await manager.get_or_create_task(
        task_key="focus_group_123",
        task_params=task_params,
        total_count=5
    )
    print(f"✅ 创建任务1: task_id={task1.task_id}, is_new={is_new1}")

    # 尝试重复创建（应返回已存在任务）
    task2, is_new2 = await manager.get_or_create_task(
        task_key="focus_group_123",
        task_params=task_params,
        total_count=5
    )
    print(f"✅ 创建任务2: task_id={task2.task_id}, is_new={is_new2}, same={task1.task_id == task2.task_id}")

    # 启动任务
    await manager.start_task(task1.task_id)

    # 更新进度
    for i in range(5):
        await manager.update_progress(
            task1.task_id,
            result={"item_id": i, "status": "ok"},
            success=True
        )
        await asyncio.sleep(0.1)

    # 完成任务
    await manager.complete_task(task1.task_id, success=True)

    # 获取任务信息
    task_info = task1.to_dict()
    print(f"✅ 任务完成: progress={task_info['progress_percentage']}%, elapsed={task_info['elapsed_seconds']:.2f}s")


async def main():
    """运行所有测试"""
    await test_concurrency_manager()
    await test_error_handler()
    await test_task_manager()
    print("\n=== 所有测试完成 ===\n")


if __name__ == "__main__":
    asyncio.run(main())
