import asyncio
import functools
import logging
import random
import time
from typing import Any, Callable, Optional, Tuple, Type

logger = logging.getLogger(__name__)


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable[[Exception, int], None]] = None,
):
    def decorator(func: Callable) -> Callable:
        is_async = asyncio.iscoroutinefunction(func)

        if is_async:
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs) -> Any:
                last_exception: Optional[Exception] = None
                for attempt in range(max_retries + 1):
                    try:
                        return await func(*args, **kwargs)
                    except exceptions as e:
                        last_exception = e
                        if attempt >= max_retries:
                            raise
                        delay = min(
                            base_delay * (exponential_base ** attempt),
                            max_delay,
                        )
                        if jitter:
                            delay = delay * (0.5 + random.random())
                        logger.warning(
                            "Retry %d/%d for %s after %.2fs: %s",
                            attempt + 1,
                            max_retries,
                            func.__name__,
                            delay,
                            str(e),
                        )
                        if on_retry:
                            on_retry(e, attempt + 1)
                        await asyncio.sleep(delay)
                raise last_exception

            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs) -> Any:
                last_exception: Optional[Exception] = None
                for attempt in range(max_retries + 1):
                    try:
                        return func(*args, **kwargs)
                    except exceptions as e:
                        last_exception = e
                        if attempt >= max_retries:
                            raise
                        delay = min(
                            base_delay * (exponential_base ** attempt),
                            max_delay,
                        )
                        if jitter:
                            delay = delay * (0.5 + random.random())
                        logger.warning(
                            "Retry %d/%d for %s after %.2fs: %s",
                            attempt + 1,
                            max_retries,
                            func.__name__,
                            delay,
                            str(e),
                        )
                        if on_retry:
                            on_retry(e, attempt + 1)
                        time.sleep(delay)
                raise last_exception

            return sync_wrapper

    return decorator


def retry_immediate(
    max_retries: int = 3,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable[[Exception, int], None]] = None,
):
    def decorator(func: Callable) -> Callable:
        is_async = asyncio.iscoroutinefunction(func)

        if is_async:
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs) -> Any:
                last_exception: Optional[Exception] = None
                for attempt in range(max_retries + 1):
                    try:
                        return await func(*args, **kwargs)
                    except exceptions as e:
                        last_exception = e
                        if attempt >= max_retries:
                            raise
                        logger.warning(
                            "Immediate retry %d/%d for %s: %s",
                            attempt + 1,
                            max_retries,
                            func.__name__,
                            str(e),
                        )
                        if on_retry:
                            on_retry(e, attempt + 1)
                raise last_exception

            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs) -> Any:
                last_exception: Optional[Exception] = None
                for attempt in range(max_retries + 1):
                    try:
                        return func(*args, **kwargs)
                    except exceptions as e:
                        last_exception = e
                        if attempt >= max_retries:
                            raise
                        logger.warning(
                            "Immediate retry %d/%d for %s: %s",
                            attempt + 1,
                            max_retries,
                            func.__name__,
                            str(e),
                        )
                        if on_retry:
                            on_retry(e, attempt + 1)
                raise last_exception

            return sync_wrapper

    return decorator
