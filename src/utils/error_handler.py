"""
错误处理器
提供统一的重试机制和错误处理
"""

import asyncio
from typing import Callable, Any, Optional, Type, Tuple
import logging
from functools import wraps

logger = logging.getLogger(__name__)


class RateLimitError(Exception):
    """API 速率限制错误"""
    pass


class ErrorHandler:
    """
    统一错误处理器

    功能：
    1. 带重试的任务执行
    2. 指数退避策略
    3. 自定义异常处理
    """

    # 重试配置
    MAX_RETRIES = 3
    RETRY_DELAY = 1.0
    EXPONENTIAL_BACKOFF = True

    def __init__(
        self,
        max_retries: Optional[int] = None,
        retry_delay: Optional[float] = None,
        exponential_backoff: Optional[bool] = None
    ):
        """
        初始化错误处理器

        Args:
            max_retries: 最大重试次数
            retry_delay: 基础重试延迟（秒）
            exponential_backoff: 是否使用指数退避
        """
        self.max_retries = max_retries if max_retries is not None else self.MAX_RETRIES
        self.retry_delay = retry_delay if retry_delay is not None else self.RETRY_DELAY
        self.exponential_backoff = (
            exponential_backoff if exponential_backoff is not None else self.EXPONENTIAL_BACKOFF
        )

        logger.info(
            f"ErrorHandler 初始化: max_retries={self.max_retries}, "
            f"retry_delay={self.retry_delay}s, exponential_backoff={self.exponential_backoff}"
        )

    def _calculate_delay(self, attempt: int) -> float:
        """
        计算重试延迟

        Args:
            attempt: 当前重试次数（从0开始）

        Returns:
            延迟时间（秒）
        """
        if self.exponential_backoff:
            return self.retry_delay * (2 ** attempt)
        return self.retry_delay

    async def with_retry(
        self,
        func: Callable,
        *args,
        retry_on: Optional[Tuple[Type[Exception], ...]] = None,
        **kwargs
    ) -> Any:
        """
        带重试的异步函数执行

        Args:
            func: 要执行的异步函数
            *args: 函数位置参数
            retry_on: 需要重试的异常类型元组，默认为 (RateLimitError, TimeoutError)
            **kwargs: 函数关键字参数

        Returns:
            函数执行结果

        Raises:
            最后一次执行的异常
        """
        retry_on = retry_on or (RateLimitError, TimeoutError)
        last_exception = None

        for attempt in range(self.max_retries):
            try:
                result = await func(*args, **kwargs)

                # 如果不是第一次尝试，记录恢复日志
                if attempt > 0:
                    logger.info(f"✅ 重试成功: func={func.__name__}, attempt={attempt + 1}")

                return result

            except retry_on as e:
                last_exception = e

                # 如果还有重试机会
                if attempt < self.max_retries - 1:
                    delay = self._calculate_delay(attempt)
                    logger.warning(
                        f"⚠️ 执行失败，准备重试: func={func.__name__}, "
                        f"attempt={attempt + 1}/{self.max_retries}, "
                        f"error={type(e).__name__}: {str(e)}, "
                        f"retry_after={delay}s"
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"❌ 重试次数用尽: func={func.__name__}, "
                        f"max_retries={self.max_retries}, "
                        f"error={type(e).__name__}: {str(e)}"
                    )

            except Exception as e:
                # 非重试类型的异常直接抛出
                logger.error(
                    f"❌ 执行失败（不可重试）: func={func.__name__}, "
                    f"error={type(e).__name__}: {str(e)}"
                )
                raise

        # 所有重试都失败，抛出最后一个异常
        raise last_exception

    def retry_decorator(
        self,
        retry_on: Optional[Tuple[Type[Exception], ...]] = None,
        max_retries: Optional[int] = None,
        retry_delay: Optional[float] = None,
        exponential_backoff: Optional[bool] = None
    ):
        """
        重试装饰器

        Args:
            retry_on: 需要重试的异常类型元组
            max_retries: 最大重试次数（覆盖实例配置）
            retry_delay: 重试延迟（覆盖实例配置）
            exponential_backoff: 是否指数退避（覆盖实例配置）

        Example:
            @error_handler.retry_decorator(retry_on=(RateLimitError,), max_retries=5)
            async def my_api_call():
                ...
        """
        retry_on = retry_on or (RateLimitError, TimeoutError)
        _max_retries = max_retries if max_retries is not None else self.max_retries
        _retry_delay = retry_delay if retry_delay is not None else self.retry_delay
        _exponential_backoff = (
            exponential_backoff if exponential_backoff is not None else self.exponential_backoff
        )

        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                last_exception = None

                for attempt in range(_max_retries):
                    try:
                        result = await func(*args, **kwargs)
                        if attempt > 0:
                            logger.info(f"✅ 重试成功: {func.__name__}, attempt={attempt + 1}")
                        return result

                    except retry_on as e:
                        last_exception = e

                        if attempt < _max_retries - 1:
                            if _exponential_backoff:
                                delay = _retry_delay * (2 ** attempt)
                            else:
                                delay = _retry_delay

                            logger.warning(
                                f"⚠️ {func.__name__} 失败，重试中: "
                                f"attempt={attempt + 1}/{_max_retries}, "
                                f"error={type(e).__name__}, delay={delay}s"
                            )
                            await asyncio.sleep(delay)
                        else:
                            logger.error(
                                f"❌ {func.__name__} 重试次数用尽: "
                                f"max_retries={_max_retries}"
                            )

                    except Exception as e:
                        logger.error(f"❌ {func.__name__} 失败（不可重试）: {type(e).__name__}")
                        raise

                raise last_exception

            return wrapper
        return decorator

    async def safe_execute(
        self,
        func: Callable,
        *args,
        default_value: Any = None,
        log_error: bool = True,
        **kwargs
    ) -> Any:
        """
        安全执行函数，捕获所有异常并返回默认值

        Args:
            func: 要执行的异步函数
            *args: 函数位置参数
            default_value: 发生异常时的默认返回值
            log_error: 是否记录错误日志
            **kwargs: 函数关键字参数

        Returns:
            函数执行结果或默认值
        """
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            if log_error:
                logger.error(
                    f"❌ 安全执行失败: func={func.__name__}, "
                    f"error={type(e).__name__}: {str(e)}, "
                    f"returning default_value={default_value}"
                )
            return default_value
