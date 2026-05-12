import time
import logging
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable

logger = logging.getLogger(__name__)


class RequestLogMiddleware(BaseHTTPMiddleware):
    """
    请求日志中间件 - 记录所有请求和响应时间
    """
    async def dispatch(self, request: Request, call_next: Callable):
        start_time = time.time()
        client_host = request.client.host if request.client else "unknown"

        try:
            response = await call_next(request)
            process_time = (time.time() - start_time) * 1000
            response.headers["X-Process-Time"] = f"{process_time:.2f}ms"

            logger.info(
                f"[{response.status_code}] {request.method} {request.url.path} "
                f"- {client_host} - {process_time:.2f}ms"
            )

            return response

        except Exception as e:
            process_time = (time.time() - start_time) * 1000
            logger.error(
                f"[500] {request.method} {request.url.path} "
                f"- {client_host} - {process_time:.2f}ms - Error: {str(e)}"
            )

            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "success": False,
                    "error": {
                        "code": "INTERNAL_ERROR",
                        "message": "服务器内部错误"
                    }
                }
            )
