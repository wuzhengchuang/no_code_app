from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status, Request, Body
from sqlalchemy.orm import Session

from src.db.session import get_db
from src.core.dependencies import get_current_user, get_optional_current_user
from src.models.user import User
from src.schemas.project import ShareCreate, ShareCopyRequest, ShareAccessRequest
from src.schemas.common import success_response
from src.services.share_service import (
    create_share, get_project_shares, get_share_by_token,
    delete_share, validate_share_access, access_share, copy_shared_project
)
from src.services.project_permission_service import has_project_access, can_create_share

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


@router.post("/{project_id}/shares", response_model=Dict[str, Any])
@optional_limiter("20 per minute")
async def create_new_share(
    request: Request,
    project_id: int,
    share_data: ShareCreate = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not can_create_share(db, project_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "AUTHORIZATION_FAILED", "message": "权限不足，需要管理员权限"}
        )

    share = create_share(db, project_id, share_data, current_user.id)
    if not share:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "PROJECT_NOT_FOUND", "message": "项目不存在"}
        )

    return success_response({
        "id": share.id,
        "project_id": share.project_id,
        "share_token": share.share_token,
        "permission": share.permission,
        "expires_at": share.expires_at,
        "is_password_protected": share.is_password_protected,
        "view_count": share.view_count,
        "copy_count": share.copy_count,
        "max_views": share.max_views,
        "max_copies": share.max_copies,
        "is_active": share.is_active,
        "created_by": share.created_by,
        "created_at": share.created_at
    }, "创建成功")


@router.get("/{project_id}/shares", response_model=Dict[str, Any])
async def list_shares(
    request: Request,
    project_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not has_project_access(db, project_id, current_user.id, "read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "AUTHORIZATION_FAILED", "message": "权限不足"}
        )

    shares, total = get_project_shares(db, project_id, page, page_size)

    items = []
    for share in shares:
        items.append({
            "id": share.id,
            "project_id": share.project_id,
            "share_token": share.share_token,
            "permission": share.permission,
            "expires_at": share.expires_at,
            "is_password_protected": share.is_password_protected,
            "view_count": share.view_count,
            "copy_count": share.copy_count,
            "max_views": share.max_views,
            "max_copies": share.max_copies,
            "is_active": share.is_active,
            "created_by": share.created_by,
            "created_at": share.created_at
        })

    return success_response({
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size
    }, "获取成功")


@router.delete("/{project_id}/shares/{share_id}", response_model=Dict[str, Any])
async def delete_project_share(
    request: Request,
    project_id: int,
    share_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not can_create_share(db, project_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "AUTHORIZATION_FAILED", "message": "权限不足，需要管理员权限"}
        )

    success = delete_share(db, project_id, share_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "SHARE_NOT_FOUND", "message": "分享不存在"}
        )

    return success_response(None, "删除成功")


public_router = APIRouter()


@public_router.get("/shared/{share_token}", response_model=Dict[str, Any])
async def access_shared_project(
    request: Request,
    share_token: str,
    password: Optional[str] = None,
    db: Session = Depends(get_db)
):
    result = access_share(db, share_token, password)

    if not result:
        validation = validate_share_access(db, share_token, password)

        error_code = validation.get("error", "SHARE_NOT_FOUND")
        error_messages = {
            "SHARE_NOT_FOUND": "分享不存在",
            "SHARE_NOT_ACTIVE": "分享已失效",
            "SHARE_EXPIRED": "分享已过期",
            "SHARE_LIMIT_EXCEEDED": "分享次数已达上限",
            "SHARE_PASSWORD_REQUIRED": "需要访问密码",
            "SHARE_PASSWORD_INVALID": "访问密码错误"
        }

        status_code = status.HTTP_404_NOT_FOUND
        if error_code == "SHARE_PASSWORD_REQUIRED":
            status_code = status.HTTP_401_UNAUTHORIZED
        elif error_code == "SHARE_PASSWORD_INVALID":
            status_code = status.HTTP_403_FORBIDDEN

        raise HTTPException(
            status_code=status_code,
            detail={
                "code": error_code,
                "message": error_messages.get(error_code, "访问失败")
            }
        )

    return success_response(result, "获取成功")


@public_router.post("/shared/{share_token}/copy", response_model=Dict[str, Any])
async def copy_from_share(
    request: Request,
    share_token: str,
    copy_request: ShareCopyRequest,
    password: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    new_project = copy_shared_project(db, share_token, copy_request, current_user.id, password)

    if not new_project:
        validation = validate_share_access(db, share_token, password)

        if not validation["valid"]:
            error_code = validation.get("error", "SHARE_NOT_FOUND")
            error_messages = {
                "SHARE_NOT_FOUND": "分享不存在",
                "SHARE_NOT_ACTIVE": "分享已失效",
                "SHARE_EXPIRED": "分享已过期",
                "SHARE_LIMIT_EXCEEDED": "分享次数已达上限",
                "SHARE_PASSWORD_REQUIRED": "需要访问密码",
                "SHARE_PASSWORD_INVALID": "访问密码错误"
            }

            status_code = status.HTTP_404_NOT_FOUND
            if error_code == "SHARE_PASSWORD_REQUIRED":
                status_code = status.HTTP_401_UNAUTHORIZED
            elif error_code == "SHARE_PASSWORD_INVALID":
                status_code = status.HTTP_403_FORBIDDEN

            raise HTTPException(
                status_code=status_code,
                detail={
                    "code": error_code,
                    "message": error_messages.get(error_code, "访问失败")
                }
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "SHARE_PERMISSION_DENIED",
                    "message": "该分享不允许复制"
                }
            )

    return success_response({
        "id": new_project.id,
        "name": new_project.name,
        "status": new_project.status,
        "created_at": new_project.created_at
    }, "复制成功")
