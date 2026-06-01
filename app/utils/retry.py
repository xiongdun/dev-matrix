"""重试工具模块。

提供 retry_with_backoff 装饰器，实现指数退避重试机制。

主要函数/装饰器：
    - retry_with_backoff: 指数退避重试装饰器。

使用示例：
    ```python
    from app.utils.retry import retry_with_backoff

    @retry_with_backoff(max_retries=3, base_delay=1.0)
    async def fetch_data():
        return await http_client.get("/api/data")
    ```
"""

import asyncio
import logging
import random
from collections.abc import Callable
from functools import wraps

logger = logging.getLogger(__name__)


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
    on_retry: Callable[[Exception, int, float], None] | None = None,
):
    """指数退避重试装饰器。

    在指定异常发生时自动重试，每次重试延迟时间按指数增长，
    并添加随机抖动避免惊群效应。

    Args:
        max_retries: 最大重试次数，默认 3。
        base_delay: 基础延迟时间（秒），默认 1.0。
        max_delay: 最大延迟时间（秒），默认 60.0。
        exceptions: 需要重试的异常类型元组。
        on_retry: 重试回调函数，接收异常、重试次数和延迟时间。

    Returns:
        Callable: 装饰器函数。

    Example:
        ```python
        @retry_with_backoff(
            max_retries=3,
            base_delay=1.0,
            exceptions=(httpx.HTTPStatusError, httpx.ConnectError),
        )
        async def fetch_data():
            return await http_client.get("/api/data")
        ```
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as exc:
                    if attempt >= max_retries:
                        logger.error(
                            "Function '%s' failed after %d retries: %s",
                            func.__name__,
                            max_retries,
                            exc,
                        )
                        raise
                    # 计算指数退避延迟，添加随机抖动
                    delay = min(base_delay * (2**attempt), max_delay)
                    jitter = random.uniform(0, delay * 0.1)
                    sleep_time = delay + jitter
                    logger.warning(
                        "Function '%s' failed (attempt %d/%d): %s. Retrying in %.2fs...",
                        func.__name__,
                        attempt + 1,
                        max_retries,
                        exc,
                        sleep_time,
                    )
                    if on_retry:
                        on_retry(exc, attempt + 1, sleep_time)
                    await asyncio.sleep(sleep_time)
            # 不可达，但保留作为安全网
            return None

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    if attempt >= max_retries:
                        logger.error(
                            "Function '%s' failed after %d retries: %s",
                            func.__name__,
                            max_retries,
                            exc,
                        )
                        raise
                    # 计算指数退避延迟，添加随机抖动
                    delay = min(base_delay * (2**attempt), max_delay)
                    jitter = random.uniform(0, delay * 0.1)
                    sleep_time = delay + jitter
                    logger.warning(
                        "Function '%s' failed (attempt %d/%d): %s. Retrying in %.2fs...",
                        func.__name__,
                        attempt + 1,
                        max_retries,
                        exc,
                        sleep_time,
                    )
                    if on_retry:
                        on_retry(exc, attempt + 1, sleep_time)
                    # 同步函数使用 time.sleep
                    import time

                    time.sleep(sleep_time)
            # 不可达，但保留作为安全网
            return None

        # 根据函数类型返回对应包装器
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator
