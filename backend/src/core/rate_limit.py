from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, status
from fastapi.responses import JSONResponse
from src.schemas.common import ErrorCode


# 创建速率限制器，基于客户端 IP 地址
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per minute"],
    storage_uri="memory://",
    enabled=True
)


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """
    速率限制超出处理器
    """
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "success": False,
            "error": {
                "code": ErrorCode.RATE_LIMIT_EXCEEDED.value,
                "message": "请求过于频繁，请稍后再试",
                "details": {
                    "retry_after": "60 seconds"
                }
            }
        }
    )
