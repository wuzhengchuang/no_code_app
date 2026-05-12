from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import Dict, Any

from src.db.session import get_db
from src.core.dependencies import get_current_user
from src.models.user import User
from src.schemas.user import UserResponse, UserProfileUpdate, UserPasswordUpdate
from src.schemas.common import success_response
from src.services.user_service import UserService

router = APIRouter()

# 可选的速率限制装饰器
try:
    from src.core.rate_limit import limiter
    rate_limit_enabled = True
except ImportError:
    rate_limit_enabled = False


def optional_limiter(limit_str: str):
    """可选的速率限制装饰器"""
    if rate_limit_enabled:
        return limiter.limit(limit_str)
    return lambda func: func


@router.get("/me", response_model=Dict[str, Any])
async def get_current_user_info(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_service = UserService(db)
    user = user_service.get_user_by_id(current_user.id)
    result = user_service.get_user_response(user)
    return success_response(result.model_dump(), "获取成功")


@router.get("/profile", response_model=Dict[str, Any])
async def get_profile(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_service = UserService(db)
    user = user_service.get_user_by_id(current_user.id)
    result = user_service.get_user_response(user)
    return success_response(result.model_dump(), "获取成功")


@router.put("/me", response_model=Dict[str, Any])
async def update_current_user_info(
    request: Request,
    data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_service = UserService(db)
    result = user_service.update_profile(current_user.id, data)
    return success_response(result.model_dump(), "更新成功")


@router.put("/profile", response_model=Dict[str, Any])
async def update_profile(
    request: Request,
    data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_service = UserService(db)
    result = user_service.update_profile(current_user.id, data)
    return success_response(result.model_dump(), "更新成功")


@router.get("/{user_id}", response_model=Dict[str, Any])
async def get_user_by_id(
    request: Request,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_service = UserService(db)
    user = user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    result = user_service.get_user_response(user)
    return success_response(result.model_dump(), "获取成功")


@router.put("/password", response_model=Dict[str, Any])
@optional_limiter("5 per minute")
async def update_password(
    request: Request,
    data: UserPasswordUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_service = UserService(db)
    user_service.update_password(current_user.id, data)
    return success_response(None, "密码修改成功")
