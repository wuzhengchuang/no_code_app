from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import Dict, Any, Tuple
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.security import HTTPBasicCredentials
from fastapi import Body

from src.db.session import get_db
from src.core.dependencies import get_current_user, get_current_user_and_token
from src.models.user import User
from src.schemas.auth import UserRegister, TokenRefresh, AuthResponse, TokenResponse, LogoutRequest, UserLogin
from src.schemas.user import SessionInfo
from src.schemas.common import success_response
from src.services.auth_service import AuthService

router = APIRouter()

# 可选的速率限制装饰器
try:
    from src.core.rate_limit import limiter
    rate_limit_enabled = True
except ImportError:
    rate_limit_enabled = False
    # 创建一个空的装饰器
    def no_limit_decorator(func):
        return func


def optional_limiter(limit_str: str):
    """可选的速率限制装饰器"""
    if rate_limit_enabled:
        return limiter.limit(limit_str)
    return lambda func: func


@router.post("/register", response_model=Dict[str, Any], status_code=200)
@optional_limiter("10 per minute")
async def register(
    request: Request,
    data: UserRegister,
    db: Session = Depends(get_db)
):
    auth_service = AuthService(db)
    result = auth_service.register(data)
    return success_response(result.model_dump(), "注册成功")


@router.post("/login", response_model=Dict[str, Any])
@optional_limiter("10 per minute")
async def login(
    request: Request,
    data: UserLogin = Body(...),
    db: Session = Depends(get_db)
):
    ip_address = request.client.host if request and request.client else None
    user_agent = request.headers.get("user-agent") if request else None

    auth_service = AuthService(db)
    result = auth_service.login(data, ip_address, user_agent)
    return success_response(result.model_dump(), "登录成功")


@router.post("/refresh", response_model=Dict[str, Any])
@optional_limiter("30 per minute")
async def refresh(
    request: Request,
    data: TokenRefresh,
    db: Session = Depends(get_db)
):
    auth_service = AuthService(db)
    result = auth_service.refresh_token(data.refreshToken)
    return success_response(result.model_dump(), "刷新成功")

@router.post("/logout", response_model=Dict[str, Any])
async def logout(
    request: Request,
    data: LogoutRequest,
    user_and_token: Tuple[User, str] = Depends(get_current_user_and_token),
    db: Session = Depends(get_db)
):
    current_user, token = user_and_token
    auth_service = AuthService(db)
    auth_service.logout(token, data.refreshToken)
    return success_response(None, "登出成功")

@router.get("/sessions", response_model=Dict[str, Any])
async def get_sessions(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    auth_service = AuthService(db)
    sessions = auth_service.get_sessions(current_user.id)

    session_list = []
    for session in sessions:
        session_list.append(SessionInfo(
            id=session.id,
            ipAddress=session.ip_address,
            userAgent=session.user_agent,
            deviceType=session.device_type,
            createdAt=session.created_at,
            expiresAt=session.expires_at,
            isCurrent=False
        ))

    return success_response(session_list, "获取成功")

@router.delete("/sessions/{session_id}", response_model=Dict[str, Any])
async def revoke_session(
    request: Request,
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    auth_service = AuthService(db)
    auth_service.revoke_session(current_user.id, session_id)
    return success_response(None, "撤销成功")
