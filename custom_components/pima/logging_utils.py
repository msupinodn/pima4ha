import asyncio
import functools
import inspect
import logging
import time
from typing import Any, Callable, Mapping, MutableMapping, Optional


SENSITIVE_PARAM_NAMES = {
    "password",
    "passwd",
    "pwd",
    "token",
    "secret",
    "code",
    "alarm_code",
    "api_key",
}


def _scrub_value(value: Any) -> Any:
    if isinstance(value, (bytes, bytearray)):
        length = len(value)
        # Avoid logging raw binary (truncate and show length only)
        return f"<bytes len={length}>"
    if isinstance(value, (dict, list, tuple, set)):
        # Fall back to repr but keep it short
        short = repr(value)
        return short if len(short) <= 300 else short[:297] + "..."
    short = repr(value)
    return short if len(short) <= 300 else short[:297] + "..."


def _format_args(bound: Mapping[str, Any]) -> str:
    parts = []
    for name, value in bound.items():
        if name in SENSITIVE_PARAM_NAMES:
            parts.append(f"{name}=<redacted>")
        else:
            parts.append(f"{name}={_scrub_value(value)}")
    return ", ".join(parts)


def log_calls(logger: Optional[logging.Logger] = None) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Decorator to log function entry, exit, duration, and exceptions.
    Works with both sync and async functions.
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        log = logger or logging.getLogger(func.__module__)
        signature = inspect.signature(func)
        is_coro = asyncio.iscoroutinefunction(func)

        if is_coro:
            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                start_time = time.perf_counter()
                try:
                    bound = signature.bind_partial(*args, **kwargs)
                    bound.apply_defaults()
                    formatted_args = _format_args(bound.arguments)
                    log.debug("→ %s(%s)", func.__qualname__, formatted_args)
                except Exception:
                    # Never fail due to logging issues
                    pass

                try:
                    result = await func(*args, **kwargs)
                    try:
                        duration_ms = (time.perf_counter() - start_time) * 1000.0
                        result_repr = _scrub_value(result)
                        log.debug("← %s returned %s in %.1f ms", func.__qualname__, result_repr, duration_ms)
                    except Exception:
                        pass
                    return result
                except Exception:
                    log.exception("✖ %s raised an exception", func.__qualname__)
                    raise

            return async_wrapper

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.perf_counter()
            try:
                bound = signature.bind_partial(*args, **kwargs)
                bound.apply_defaults()
                formatted_args = _format_args(bound.arguments)
                log.debug("→ %s(%s)", func.__qualname__, formatted_args)
            except Exception:
                pass

            try:
                result = func(*args, **kwargs)
                try:
                    duration_ms = (time.perf_counter() - start_time) * 1000.0
                    result_repr = _scrub_value(result)
                    log.debug("← %s returned %s in %.1f ms", func.__qualname__, result_repr, duration_ms)
                except Exception:
                    pass
                return result
            except Exception:
                log.exception("✖ %s raised an exception", func.__qualname__)
                raise

        return sync_wrapper

    return decorator


