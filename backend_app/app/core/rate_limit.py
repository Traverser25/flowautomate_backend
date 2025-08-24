# app/core/rate_limit.py
import asyncio
from fastapi import HTTPException, Request
from functools import wraps
from time import time
from app.core.config import get_settings

settings = get_settings()

# store request timestamps per user (username or IP)
_request_logs = {}

def rate_limiter():
    """
    Decorator to limit requests per user/IP.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request: Request = kwargs.get("request")
            # Use token username if available, else IP
            key = getattr(request.state, "username", request.client.host if request else "anon")
            now = time()
            window = settings.RATE_LIMIT_WINDOW_SEC
            max_requests = settings.RATE_LIMIT_MAX

            timestamps = _request_logs.get(key, [])
            # remove expired timestamps
            timestamps = [t for t in timestamps if t > now - window]
            if len(timestamps) >= max_requests:
                raise HTTPException(status_code=429, detail="Rate limit exceeded")
            timestamps.append(now)
            _request_logs[key] = timestamps
            return await func(*args, **kwargs)
        return wrapper
    return decorator
