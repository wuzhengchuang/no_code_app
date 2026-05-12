from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any

from src.db.session import get_db
from src.core.dependencies import get_current_user
from src.models.user import User
from src.schemas.user import UserResponse, UserProfileUpdate, UserPasswordUpdate
from src.services.user_service import UserService

router = APIRouter()

@router.get("/me", response_model=Dict[str, Any])
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_service = UserService(db)
    user = user_service.get_user_by_id(current_user.id)
    result = user_service.get_user_response(user)
    return {
        "success": True,
        "data": result.model_dump(),
        "message": "获取成功"
    }

@router.get("/profile", response_model=Dict[str, Any])
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_service = UserService(db)
    user = user_service.get_user_by_id(current_user.id)
    result = user_service.get_user_response(user)
    return {
        "success": True,
        "data": result.model_dump(),
        "message": "获取成功"
    }

@router.put("/me", response_model=Dict[str, Any])
async def update_current_user_info(
    data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_service = UserService(db)
    result = user_service.update_profile(current_user.id, data)
    return {
        "success": True,
        "data": result.model_dump(),
        "message": "更新成功"
    }

@router.put("/profile", response_model=Dict[str, Any])
async def update_profile(
    data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_service = UserService(db)
    result = user_service.update_profile(current_user.id, data)
    return {
        "success": True,
        "data": result.model_dump(),
        "message": "更新成功"
    }

@router.get("/{user_id}", response_model=Dict[str, Any])
async def get_user_by_id(
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
    return {
        "success": True,
        "data": result.model_dump(),
        "message": "获取成功"
    }

@router.put("/password", response_model=Dict[str, Any])
async def update_password(
    data: UserPasswordUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_service = UserService(db)
    user_service.update_password(current_user.id, data)
    return {
        "success": True,
        "data": None,
        "message": "密码修改成功"
    }
