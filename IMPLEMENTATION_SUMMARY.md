# 工具模块实现总结

## 实现概览

已完成 `src/utils/` 工具模块的实现，包含三个核心类和相关辅助功能。

## 实现的类和方法

### 1. ConcurrencyManager (src/utils/concurrency.py)

**核心类**：`ConcurrencyManager`

**关键方法**：
- `__init__(max_concurrency)` - 初始化并发管理器
- `execute_batch(tasks, max_concurrency, return_exceptions)` - 带限流的批量执行
- `execute_batch_with_isolation(tasks, max_concurrency)` - 带错误隔离的批量执行
- `execute_in_batches(tasks, batch_size, max_concurrency)` - 分批次执行
- `for_survey()` - 创建问卷场景管理器（100并发）
- `for_focus_group()` - 创建焦点小组场景管理器（50并发）

**配置常量**：
- `SURVEY_MAX_CONCURRENCY = 100`
- `SURVEY_BATCH_SIZE = 50`
- `FOCUS_GROUP_MAX_CONCURRENCY = 50`
- `FOCUS_GROUP_BATCH_SIZE = 20`

**代码行数**：190行

---

### 2. ErrorHandler (src/utils/error_handler.py)

**核心类**：`ErrorHandler`

**关键方法**：
- `__init__(max_retries, retry_delay, exponential_backoff)` - 初始化错误处理器
- `with_retry(func, *args, retry_on, **kwargs)` - 带重试的异步函数执行
- `retry_decorator(retry_on, max_retries, retry_delay, exponential_backoff)` - 重试装饰器
- `safe_execute(func, *args, default_value, log_error, **kwargs)` - 安全执行函数
- `_calculate_delay(attempt)` - 计算重试延迟（支持指数退避）

**异常类**：
- `RateLimitError` - API速率限制错误

**配置常量**：
- `MAX_RETRIES = 3`
- `RETRY_DELAY = 1.0`
- `EXPONENTIAL_BACKOFF = True`

**代码行数**：239行

---

### 3. TaskManager (src/utils/task_manager.py)

**核心类**：`TaskManager`（单例模式）

**关键方法**：
- `get_or_create_task(task_key, task_params, total_count)` - 获取或创建任务（防重复）
- `get_task(task_id)` - 获取任务
- `get_active_task(task_key)` - 获取活跃任务
- `start_task(task_id)` - 标记任务开始
- `update_status(task_id, status, error_message)` - 更新任务状态
- `update_progress(task_id, result, success)` - 更新任务进度
- `complete_task(task_id, success, error_message)` - 完成任务
- `_compute_fingerprint(task_params)` - 计算任务指纹（MD5）
- `_cleanup_old_tasks()` - 清理过期任务

**数据模型**：
- `Task` (dataclass)
  - 任务属性：task_id, task_key, params, fingerprint, status
  - 时间属性：created_at, started_at, completed_at
  - 进度属性：total_count, completed_count, success_count, failed_count
  - 结果属性：results, error_message
  - 计算属性：progress_percentage, elapsed_seconds
  - 方法：to_dict()

**枚举**：
- `TaskStatus` - 任务状态枚举（PENDING, PROCESSING, COMPLETED, FAILED）

**全局函数**：
- `get_task_manager()` - 获取任务管理器单例

**代码行数**：401行

---

## 文件结构

```
src/
├── __init__.py
└── utils/
    ├── __init__.py              # 模块导出
    ├── concurrency.py           # 并发控制管理器
    ├── error_handler.py         # 错误处理器
    └── task_manager.py          # 任务管理器

examples/
└── test_utils.py                # 使用示例和测试

docs/
└── utils_usage.md               # 详细使用文档
```

---

## 核心特性

### 并发控制
- ✅ 基于 `asyncio.Semaphore` 的并发限流
- ✅ 支持不同场景的预设并发数（问卷100、焦点小组50）
- ✅ 错误隔离执行（单个失败不影响整体）
- ✅ 分批次执行（支持超大规模任务）

### 错误处理
- ✅ 自动重试机制（支持自定义重试次数）
- ✅ 指数退避策略（避免API限流）
- ✅ 装饰器模式（简化代码）
- ✅ 安全执行（捕获所有异常，返回默认值）

### 任务管理
- ✅ 防重复创建（基于MD5指纹识别）
- ✅ 活跃任务索引（快速查询正在运行的任务）
- ✅ 进度跟踪（实时统计成功/失败数）
- ✅ 自动清理（过期任务5分钟后清理）
- ✅ 单例模式（全局统一管理）

---

## 技术亮点

### 1. 并发安全
- 使用 `asyncio.Lock` 防止任务创建时的竞态条件
- 活跃任务索引确保同一业务实体不会并发执行

### 2. 指纹识别
```python
# 参数排序后生成MD5，确保顺序不影响
sorted_ids = sorted(participant_ids)  # [3,1,2] -> [1,2,3]
fingerprint = md5(f"{key1}:{value1}|{key2}:{value2}").hexdigest()[:16]
```

### 3. 进度追踪
```python
# 自动计算进度百分比
@property
def progress_percentage(self) -> float:
    return round((self.completed_count / self.total_count) * 100, 2)
```

### 4. 指数退避
```python
# 避免API限流的智能重试
delay = retry_delay * (2 ** attempt)  # 1s -> 2s -> 4s -> 8s
```

---

## 参考实现

- **backhour_ai**: `services/focus_group_batch_task_manager.py`
  - 任务管理模式
  - 防重复机制
  - 进度跟踪逻辑

- **技术架构文档**: `docs/02-技术架构文档.md`
  - 第4节：并发控制策略
  - 第5节：错误处理与重试

---

## 使用示例

详见 `docs/utils_usage.md` 和 `examples/test_utils.py`

### 快速开始

```python
from src.utils import ConcurrencyManager, ErrorHandler, TaskManager

# 并发控制
manager = ConcurrencyManager.for_survey()
results = await manager.execute_batch(tasks, max_concurrency=100)

# 错误处理
handler = ErrorHandler(max_retries=3, exponential_backoff=True)
result = await handler.with_retry(api_call)

# 任务管理
task_manager = TaskManager()
task, is_new = await task_manager.get_or_create_task("key", params)
```

---

## 统计数据

| 模块 | 类数量 | 方法数量 | 代码行数 |
|-----|--------|----------|---------|
| concurrency.py | 1 | 6 | 190 |
| error_handler.py | 2 | 5 | 239 |
| task_manager.py | 3 | 10 | 401 |
| **总计** | **6** | **21** | **830** |

---

## 下一步

工具模块已完成，可以开始实现四大场景：
1. 场景一：1对1访谈（Claude Agent SDK）
2. 场景二：问卷投放（Agno Teams）
3. 场景三：焦点小组（Agno Workflows）
4. 场景四：受众生成（SmolaAgents Manager）
