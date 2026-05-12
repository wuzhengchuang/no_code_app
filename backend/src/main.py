from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from src.api import router as api_router
from src.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title="无代码平台 API",
    description="无代码应用开发平台的后端API服务",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# 可选：添加速率限制器
try:
    from slowapi.errors import RateLimitExceeded
    from src.core.middleware import RequestLogMiddleware
    from src.core.rate_limit import limiter, rate_limit_exceeded_handler

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
    app.add_middleware(RequestLogMiddleware)
except ImportError:
    # 如果没有安装 slowapi，跳过速率限制功能
    pass

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")

@app.get("/", tags=["健康检查"])
async def health_check():
    return {"status": "healthy", "message": "无代码平台 API 服务运行正常"}

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="无代码平台 API",
        version="1.0.0",
        description="无代码应用开发平台的后端API服务",
        routes=app.routes,
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.DEBUG
    )
