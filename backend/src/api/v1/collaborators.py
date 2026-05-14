from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Path, status, Request
from sqlalchemy.orm import Session

from src.db.session import get_db
from src.core.dependencies import get_current_user
from src.models.user import User
from src.schemas.project import CollaboratorCreate, CollaboratorUpdate
from src.schemas.common import success_response
from src.services.collaborator_service import (
    add_collaborator, get_project_collaborators, get_collaborator_by_id,
    update_collaborator, remove_collaborator
)
from src.services.project_permission_service import has_project_access, can_manage_collaborators

router = APIRouter()

try:
    from src.core.rate_limit import limiter
    rate_limit_enabled = True
except ImportError:
    rate_limit_enabled = False


def optional_limiter(limit_str: str):
    if rate_limit_enabled:
        return limiter.limit(limit_str)
    return lambda func: func


@router.post("/{project_id}/collaborators", response_model=Dict[str, Any])
@optional_limiter("20 per minute")
async def add_project_collaborator(
    request: Request,
    project_id: int,
    collaborator_data: CollaboratorCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not can_manage_collaborators(db, project_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "AUTHORIZATION_FAILED", "message": "权限不足，需要管理员权限"}
        )

    if collaborator_data.user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_REQUEST", "message": "不能添加自己为协作者"}
        )

    result = add_collaborator(db, project_id, collaborator_data, current_user.id)
    if not result["success"]:
        error_code = result["error"]
        error_messages = {
            "PROJECT_NOT_FOUND": ("项目不存在", status.HTTP_404_NOT_FOUND),
            "USER_NOT_FOUND": ("用户不存在", status.HTTP_404_NOT_FOUND),
            "CANNOT_ADD_OWNER": ("不能添加项目所有者为协作者", status.HTTP_400_BAD_REQUEST),
        }
        message, code = error_messages.get(error_code, ("操作失败", status.HTTP_400_BAD_REQUEST))
        raise HTTPException(
            status_code=code,
            detail={"code": error_code, "message": message}
        )

    collaborator = result["collaborator"]

    user_info = None
    if collaborator.user:
        user_info = {
            "id": collaborator.user.id,
            "nickname": collaborator.user.nickname,
            "avatar_url": collaborator.user.avatar_url
        }

    return success_response({
        "id": collaborator.id,
        "project_id": collaborator.project_id,
        "user_id": collaborator.user_id,
        "user": user_info,
        "permission": collaborator.permission,
        "invited_by": collaborator.invited_by,
        "joined_at": collaborator.joined_at,
        "created_at": collaborator.created_at
    }, "添加成功")


@router.get("/{project_id}/collaborators", response_model=Dict[str, Any])
async def list_collaborators(
    request: Request,
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not has_project_access(db, project_id, current_user.id, "read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "AUTHORIZATION_FAILED", "message": "权限不足"}
        )

    collaborators = get_project_collaborators(db, project_id)

    items = []
    for collab in collaborators:
        user_info = None
        if collab.user:
            user_info = {
                "id": collab.user.id,
                "nickname": collab.user.nickname,
                "avatar_url": collab.user.avatar_url
            }

        items.append({
            "id": collab.id,
            "project_id": collab.project_id,
            "user_id": collab.user_id,
            "user": user_info,
            "permission": collab.permission,
            "invited_by": collab.invited_by,
            "joined_at": collab.joined_at,
            "created_at": collab.created_at
        })

    return success_response({
        "items": items,
        "total": len(items)
    }, "获取成功")


@router.put("/{project_id}/collaborators/{collaborator_id}", response_model=Dict[str, Any])
async def update_collaborator_permission(
    request: Request,
    project_id: int,
    collaborator_id: int,
    update_data: CollaboratorUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not can_manage_collaborators(db, project_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "AUTHORIZATION_FAILED", "message": "权限不足，需要管理员权限"}
        )

    collaborator = update_collaborator(db, project_id, collaborator_id, update_data)
    if not collaborator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "COLLABORATOR_NOT_FOUND", "message": "协作者不存在"}
        )

    user_info = None
    if collaborator.user:
        user_info = {
            "id": collaborator.user.id,
            "nickname": collaborator.user.nickname,
            "avatar_url": collaborator.user.avatar_url
        }

    return success_response({
        "id": collaborator.id,
        "project_id": collaborator.project_id,
        "user_id": collaborator.user_id,
        "user": user_info,
        "permission": collaborator.permission,
        "invited_by": collaborator.invited_by,
        "joined_at": collaborator.joined_at,
        "created_at": collaborator.created_at
    }, "更新成功")


@router.delete("/{project_id}/collaborators/{collaborator_id}", response_model=Dict[str, Any])
async def remove_project_collaborator(
    request: Request,
    project_id: int,
    collaborator_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not can_manage_collaborators(db, project_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "AUTHORIZATION_FAILED", "message": "权限不足，需要管理员权限"}
        )

    success = remove_collaborator(db, project_id, collaborator_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "COLLABORATOR_NOT_FOUND", "message": "协作者不存在"}
        )

    return success_response(None, "移除成功")
