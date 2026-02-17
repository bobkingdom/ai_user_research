# 工具模块使用指南

## 概述

工具模块提供三个核心组件：
- **ConcurrencyManager**: 并发控制管理器
- **ErrorHandler**: 错误处理和重试机制
- **TaskManager**: 任务管理和防重复

## 1. ConcurrencyManager - 并发控制

### 基本用法

```python
from src.utils import ConcurrencyManager

# 创建并发管理器（自定义并发数）
manager = ConcurrencyManager(max_concurrency=50)

# 或使用预设场景
survey_manager = ConcurrencyManager.for_survey()        # 100并发
focus_manager = ConcurrencyManager.for_focus_group()   # 50并发

# 批量执行任务
async def my_task(item_id):
    # 处理逻辑
    return f"Processed {item_id}"

tasks = [lambda i=i: my_task(i) for i in range(100)]
results = await manager.execute_batch(tasks, max_concurrency=20)
```

### 错误隔离执行

```python
# 单个失败不影响整体
results = await manager.execute_batch_with_isolation(tasks)

for result in results:
    if result["success"]:
        print(f"成功: {result['data']}")
    else:
        print(f"失败: {result['error']}")
```

### 分批执行

```python
# 适用于超大规模任务
results = await manager.execute_in_batches(
    tasks,
    batch_size=50,       # 每批50个
    max_concurrency=20   # 批内20并发
)
```

### 关键参数

| 参数 | 说明 | 默认值 |
|-----|------|--------|
| `max_concurrency` | 最大并发数 | 100 |
| `batch_size` | 批次大小 | 50 |
| `return_exceptions` | 是否返回异常而不抛出 | False |

---

## 2. ErrorHandler - 错误处理

### 基本用法

```python
from src.utils import ErrorHandler
from src.utils.error_handler import RateLimitError

# 创建错误处理器
handler = ErrorHandler(
    max_retries=3,
    retry_delay=1.0,
    exponential_backoff=True
)

# 带重试的执行
async def api_call():
    # 可能失败的API调用
    ...

result = await handler.with_retry(
    api_call,
    retry_on=(RateLimitError, TimeoutError)
)
```

### 重试装饰器

```python
@handler.retry_decorator(
    retry_on=(RateLimitError,),
    max_retries=5,
    retry_delay=2.0,
    exponential_backoff=True
)
async def unstable_api_call():
    # 不稳定的API调用
    ...
```

### 安全执行

```python
# 捕获所有异常，返回默认值
result = await handler.safe_execute(
    risky_function,
    default_value=None,
    log_error=True
)
```

### 重试策略

| 策略 | 说明 | 计算公式 |
|-----|------|---------|
| 固定延迟 | 每次重试固定间隔 | `retry_delay` |
| 指数退避 | 延迟时间指数增长 | `retry_delay * (2 ** attempt)` |

**示例**（retry_delay=1.0, max_retries=3）：
- 固定延迟：1s, 1s, 1s
- 指数退避：1s, 2s, 4s

---

## 3. TaskManager - 任务管理

### 基本用法

```python
from src.utils import TaskManager, TaskStatus, get_task_manager

# 获取单例（推荐）
manager = get_task_manager()

# 创建任务（防重复）
task, is_new = await manager.get_or_create_task(
    task_key="focus_group_123",
    task_params={
        "focus_group_id": "123",
        "participant_ids": [1, 2, 3],
        "message": "Hello"
    },
    total_count=3
)

if not is_new:
    print(f"任务已存在: {task.task_id}")
```

### 任务生命周期

```python
# 1. 启动任务
await manager.start_task(task.task_id)

# 2. 更新进度
for item in items:
    # 处理逻辑
    result = await process_item(item)

    await manager.update_progress(
        task.task_id,
        result={"item_id": item.id, "data": result},
        success=True
    )

# 3. 完成任务
await manager.complete_task(
    task.task_id,
    success=True,
    error_message=None
)
```

### 查询任务

```python
# 按 task_id 查询
task = manager.get_task("task_abc123")

# 查询活跃任务
active_task = manager.get_active_task("focus_group_123")

# 获取任务信息
task_info = task.to_dict()
print(f"进度: {task_info['progress_percentage']}%")
print(f"耗时: {task_info['elapsed_seconds']}s")
```

### 任务指纹防重复

TaskManager 通过 MD5 指纹识别重复请求：

```python
# 相同参数生成相同指纹
params1 = {"focus_group_id": "123", "ids": [1, 2, 3], "msg": "Hi"}
params2 = {"focus_group_id": "123", "ids": [3, 2, 1], "msg": "Hi"}  # 列表顺序不影响
# fingerprint1 == fingerprint2 ✅

params3 = {"focus_group_id": "123", "ids": [1, 2, 3], "msg": "Hello"}
# fingerprint3 != fingerprint1 ✅（msg 不同）
```

### Task 数据模型

| 字段 | 类型 | 说明 |
|-----|------|------|
| `task_id` | str | 任务唯一标识 |
| `task_key` | str | 业务键（如 focus_group_id） |
| `status` | TaskStatus | 任务状态 |
| `total_count` | int | 总任务数 |
| `completed_count` | int | 已完成数 |
| `success_count` | int | 成功数 |
| `failed_count` | int | 失败数 |
| `progress_percentage` | float | 进度百分比 |
| `elapsed_seconds` | float | 已执行时间 |
| `results` | List[dict] | 任务结果列表 |

---

## 组合使用示例

### 问卷批量投放

```python
from src.utils import ConcurrencyManager, ErrorHandler, TaskManager

async def deploy_survey(survey_id, audience_ids):
    # 初始化
    concurrency = ConcurrencyManager.for_survey()
    error_handler = ErrorHandler(max_retries=3)
    task_manager = TaskManager()

    # 创建任务
    task, is_new = await task_manager.get_or_create_task(
        task_key=f"survey_{survey_id}",
        task_params={"survey_id": survey_id, "audience_ids": audience_ids},
        total_count=len(audience_ids)
    )

    if not is_new:
        return {"task_id": task.task_id, "is_new": False}

    # 启动任务
    await task_manager.start_task(task.task_id)

    # 定义单个受众的投放逻辑
    async def deploy_to_audience(audience_id):
        async def _deploy():
            # 实际投放逻辑
            return await send_survey(survey_id, audience_id)

        # 带重试执行
        result = await error_handler.with_retry(_deploy)

        # 更新进度
        await task_manager.update_progress(
            task.task_id,
            result={"audience_id": audience_id, "status": "ok"},
            success=True
        )

        return result

    # 批量并发执行
    tasks = [lambda aid=aid: deploy_to_audience(aid) for aid in audience_ids]
    await concurrency.execute_batch(tasks, max_concurrency=100)

    # 完成任务
    await task_manager.complete_task(task.task_id, success=True)

    return {"task_id": task.task_id, "is_new": True}
```

### 焦点小组批量生成

```python
async def batch_generate_responses(focus_group_id, participant_ids, host_message):
    concurrency = ConcurrencyManager.for_focus_group()
    error_handler = ErrorHandler(max_retries=3, exponential_backoff=True)
    task_manager = TaskManager()

    # 创建任务（防重复）
    task, is_new = await task_manager.get_or_create_task(
        task_key=f"fg_{focus_group_id}",
        task_params={
            "focus_group_id": focus_group_id,
            "participant_ids": participant_ids,
            "host_message": host_message
        },
        total_count=len(participant_ids)
    )

    if not is_new:
        # 任务已存在，直接返回
        return task.to_dict()

    await task_manager.start_task(task.task_id)

    # 定义单个参与者的回复生成
    async def generate_response(participant_id):
        try:
            async def _generate():
                return await ai_generate_response(participant_id, host_message)

            result = await error_handler.with_retry(_generate)

            await task_manager.update_progress(
                task.task_id,
                result={"participant_id": participant_id, "content": result},
                success=True
            )
        except Exception as e:
            await task_manager.update_progress(
                task.task_id,
                result={"participant_id": participant_id, "error": str(e)},
                success=False
            )

    # 批量执行（错误隔离）
    tasks = [lambda pid=pid: generate_response(pid) for pid in participant_ids]
    await concurrency.execute_batch_with_isolation(tasks, max_concurrency=50)

    await task_manager.complete_task(task.task_id, success=True)

    return task.to_dict()
```

---

## 运行测试

```bash
# 运行示例测试
cd /Users/anoxia/workspaces/Tests/siry_ai_research
python examples/test_utils.py
```

## 参考文档

- [技术架构文档](../docs/02-技术架构文档.md) - 第4节（并发架构）、第5节（错误处理）
- [backhour_ai 实现参考](../../backhour_ai/services/focus_group_batch_task_manager.py)
