"""
统一的异常处理机制

提供完整的异常类层次结构、重试装饰器和错误上下文管理。
"""

import time
import asyncio
import functools
import logging
from typing import Optional, Dict, Any, Callable, TypeVar, Union, Type, Tuple
from dataclasses import dataclass, field
from enum import Enum


# ============================================================================
# 异常类层次结构
# ============================================================================

class AIAutomationError(Exception):
    """
    基础异常类，所有自定义异常的父类。

    包含完整的上下文信息，支持异常链追踪。

    Attributes:
        message: 错误消息
        error_code: 错误代码（可选）
        context: 错误上下文信息（可选）
        original_exception: 原始异常（可选）
    """

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        original_exception: Optional[Exception] = None
    ):
        """
        初始化异常。

        Args:
            message: 错误消息
            error_code: 错误代码，用于错误分类和监控
            context: 额外的上下文信息（如请求参数、环境变量等）
            original_exception: 原始异常，用于异常链追踪
        """
        self.message = message
        self.error_code = error_code
        self.context = context or {}
        self.original_exception = original_exception

        # 构建完整的错误消息
        full_message = message
        if error_code:
            full_message = f"[{error_code}] {message}"

        super().__init__(full_message)

    def __str__(self) -> str:
        """返回友好的错误消息。"""
        parts = [self.message]

        if self.error_code:
            parts.append(f"(code: {self.error_code})")

        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            parts.append(f"[{context_str}]")

        if self.original_exception:
            parts.append(f"Caused by: {type(self.original_exception).__name__}: {self.original_exception}")

        return " ".join(parts)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式，方便日志记录和监控。"""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "error_code": self.error_code,
            "context": self.context,
            "original_error": str(self.original_exception) if self.original_exception else None,
        }


class LLMError(AIAutomationError):
    """LLM 相关的通用错误。"""
    pass


class AuthenticationError(LLMError):
    """
    认证失败错误。

    当 API key 无效、过期或缺失时抛出。
    """
    def __init__(self, message: str = "Authentication failed", **kwargs):
        super().__init__(message, error_code="AUTH_ERROR", **kwargs)


class RateLimitError(LLMError):
    """
    速率限制错误。

    当超过 API 调用速率限制时抛出。
    """
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[float] = None,
        **kwargs
    ):
        super().__init__(message, error_code="RATE_LIMIT", **kwargs)
        self.retry_after = retry_after


class NetworkError(LLMError):
    """
    网络错误。

    当网络连接失败、超时或其他网络问题时抛出。
    """
    def __init__(self, message: str = "Network error", **kwargs):
        super().__init__(message, error_code="NETWORK_ERROR", **kwargs)


class APIError(LLMError):
    """
    API 错误。

    当 API 返回错误响应时抛出（如 5xx 服务器错误）。
    """
    def __init__(
        self,
        message: str = "API error",
        status_code: Optional[int] = None,
        **kwargs
    ):
        super().__init__(message, error_code="API_ERROR", **kwargs)
        self.status_code = status_code


class ValidationError(AIAutomationError):
    """
    数据验证错误。

    当输入数据不符合预期格式或约束时抛出。
    """
    def __init__(self, message: str = "Validation failed", **kwargs):
        super().__init__(message, error_code="VALIDATION_ERROR", **kwargs)


class ToolError(AIAutomationError):
    """
    工具执行错误。

    当工具调用失败时抛出。
    """
    def __init__(self, message: str = "Tool execution failed", **kwargs):
        super().__init__(message, error_code="TOOL_ERROR", **kwargs)


class ConfigError(AIAutomationError):
    """
    配置错误。

    当配置无效或缺失时抛出。
    """
    def __init__(self, message: str = "Configuration error", **kwargs):
        super().__init__(message, error_code="CONFIG_ERROR", **kwargs)


class TimeoutError(AIAutomationError):
    """
    超时错误。

    当操作超过指定时间限制时抛出。
    """
    def __init__(self, message: str = "Operation timed out", **kwargs):
        super().__init__(message, error_code="TIMEOUT_ERROR", **kwargs)


class ResourceError(AIAutomationError):
    """
    资源错误。

    当资源不足或不可用时抛出（如内存、磁盘空间等）。
    """
    def __init__(self, message: str = "Resource error", **kwargs):
        super().__init__(message, error_code="RESOURCE_ERROR", **kwargs)


# ============================================================================
# 重试配置
# ============================================================================

class RetryStrategy(Enum):
    """重试策略枚举。"""
    EXPONENTIAL = "exponential"  # 指数退避
    LINEAR = "linear"  # 线性退避
    CONSTANT = "constant"  # 固定延迟


@dataclass
class RetryConfig:
    """
    重试配置类。

    定义重试行为的所有参数。
    """
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    exponential_base: float = 2.0
    jitter: bool = True
    jitter_max: float = 0.1
    retry_on: Tuple[Type[Exception], ...] = (LLMError, NetworkError, APIError, RateLimitError)
    dont_retry_on: Tuple[Type[Exception], ...] = (AuthenticationError, ValidationError, ConfigError)

    def calculate_delay(self, attempt: int) -> float:
        """
        计算重试延迟。

        Args:
            attempt: 当前重试次数（从 0 开始）

        Returns:
            延迟时间（秒）
        """
        if self.strategy == RetryStrategy.EXPONENTIAL:
            delay = self.base_delay * (self.exponential_base ** attempt)
        elif self.strategy == RetryStrategy.LINEAR:
            delay = self.base_delay * (attempt + 1)
        else:  # CONSTANT
            delay = self.base_delay

        # 限制最大延迟
        delay = min(delay, self.max_delay)

        # 添加抖动以避免惊群效应
        if self.jitter:
            import random
            jitter_amount = random.uniform(0, delay * self.jitter_max)
            delay += jitter_amount

        return delay

    def should_retry(self, exception: Exception) -> bool:
        """
        判断是否应该重试。

        Args:
            exception: 捕获的异常

        Returns:
            是否应该重试
        """
        # 首先检查不应该重试的异常
        if isinstance(exception, self.dont_retry_on):
            return False

        # 然后检查应该重试的异常
        if isinstance(exception, self.retry_on):
            return True

        # 默认不重试
        return False


# ============================================================================
# 重试装饰器
# ============================================================================

T = TypeVar('T')
F = TypeVar('F', bound=Callable[..., Any])


def retry(
    config: Optional[RetryConfig] = None,
    on_retry: Optional[Callable[[Exception, int, float], None]] = None,
    logger: Optional[logging.Logger] = None
) -> Callable[[F], F]:
    """
    通用重试装饰器，支持同步和异步函数。

    Args:
        config: 重试配置，如果为 None 则使用默认配置
        on_retry: 重试时的回调函数，接收 (exception, attempt, delay) 参数
        logger: 日志记录器，用于记录重试信息

    Returns:
        装饰器函数

    Examples:
        >>> @retry()
        ... def my_function():
        ...     # 可能失败的操作
        ...     pass

        >>> @retry(config=RetryConfig(max_retries=5))
        ... async def my_async_function():
        ...     # 可能失败的异步操作
        ...     pass
    """
    if config is None:
        config = RetryConfig()

    if logger is None:
        logger = logging.getLogger(__name__)

    def decorator(func: F) -> F:
        # 判断是否为异步函数
        is_async = asyncio.iscoroutinefunction(func)

        if is_async:
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                last_exception = None

                for attempt in range(config.max_retries + 1):
                    try:
                        return await func(*args, **kwargs)
                    except Exception as e:
                        last_exception = e

                        # 检查是否应该重试
                        if not config.should_retry(e):
                            logger.error(
                                f"Non-retryable error in {func.__name__}: {e}",
                                extra={"error": e, "attempt": attempt}
                            )
                            raise

                        # 如果已经是最后一次尝试，不再重试
                        if attempt >= config.max_retries:
                            break

                        # 计算延迟
                        delay = config.calculate_delay(attempt)

                        # 记录重试信息
                        logger.warning(
                            f"Retry {attempt + 1}/{config.max_retries} for {func.__name__} "
                            f"after {delay:.2f}s due to: {e}",
                            extra={
                                "error": e,
                                "attempt": attempt + 1,
                                "max_retries": config.max_retries,
                                "delay": delay
                            }
                        )

                        # 调用回调
                        if on_retry:
                            on_retry(e, attempt + 1, delay)

                        # 等待后重试
                        await asyncio.sleep(delay)

                # 所有重试都失败了
                logger.error(
                    f"All retries exhausted for {func.__name__}",
                    extra={
                        "error": last_exception,
                        "max_retries": config.max_retries
                    }
                )
                raise last_exception

            return async_wrapper  # type: ignore
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                last_exception = None

                for attempt in range(config.max_retries + 1):
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        last_exception = e

                        # 检查是否应该重试
                        if not config.should_retry(e):
                            logger.error(
                                f"Non-retryable error in {func.__name__}: {e}",
                                extra={"error": e, "attempt": attempt}
                            )
                            raise

                        # 如果已经是最后一次尝试，不再重试
                        if attempt >= config.max_retries:
                            break

                        # 计算延迟
                        delay = config.calculate_delay(attempt)

                        # 记录重试信息
                        logger.warning(
                            f"Retry {attempt + 1}/{config.max_retries} for {func.__name__} "
                            f"after {delay:.2f}s due to: {e}",
                            extra={
                                "error": e,
                                "attempt": attempt + 1,
                                "max_retries": config.max_retries,
                                "delay": delay
                            }
                        )

                        # 调用回调
                        if on_retry:
                            on_retry(e, attempt + 1, delay)

                        # 等待后重试
                        time.sleep(delay)

                # 所有重试都失败了
                logger.error(
                    f"All retries exhausted for {func.__name__}",
                    extra={
                        "error": last_exception,
                        "max_retries": config.max_retries
                    }
                )
                raise last_exception

            return sync_wrapper  # type: ignore

    return decorator


# ============================================================================
# 便捷函数
# ============================================================================

def create_error_context(**kwargs) -> Dict[str, Any]:
    """
    创建错误上下文字典。

    Args:
        **kwargs: 上下文键值对

    Returns:
        上下文字典
    """
    return {k: v for k, v in kwargs.items() if v is not None}


def wrap_exception(
    exception: Exception,
    message: Optional[str] = None,
    error_class: Type[AIAutomationError] = AIAutomationError,
    **context
) -> AIAutomationError:
    """
    将任意异常包装为统一的异常类型。

    Args:
        exception: 原始异常
        message: 自定义错误消息（可选）
        error_class: 目标异常类
        **context: 额外的上下文信息

    Returns:
        包装后的异常
    """
    if message is None:
        message = str(exception)

    return error_class(
        message=message,
        context=create_error_context(**context),
        original_exception=exception
    )
