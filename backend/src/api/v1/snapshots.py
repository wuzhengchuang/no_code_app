from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from sqlalchemy.orm import Session

from src.db.session import get_db
from src.core.dependencies import get_current_user
from src.models.user import User
from src.schemas.project import SnapshotCreate, SnapshotRestoreRequest
from src.schemas.common import success_response
from src.services.snapshot_service import (
    create_snapshot, get_project_snapshots, get_snapshot_by_id,
    restore_snapshot, delete_snapshot
)
from src.services.project_permission_service import (
    has_project_access, can_create_snapshot
)

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


@router.post("/{project_id}/snapshots", response_model=Dict[str, Any])
@optional_limiter("20 per minute")
async def create_new_snapshot(
    request: Request,
    project_id: int,
    snapshot_data: SnapshotCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from src.services.project_service import get_project_by_id
    
    project = get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "PROJECT_NOT_FOUND", "message": "项目不存在"}
        )

    if not can_create_snapshot(db, project_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "AUTHORIZATION_FAILED", "message": "权限不足，需要写入权限"}
        )

    snapshot = create_snapshot(db, project_id, snapshot_data, current_user.id)

    creator_info = None
    if snapshot.creator:
        creator_info = {
            "id": snapshot.creator.id,
            "nickname": snapshot.creator.nickname
        }

    return success_response({
        "id": snapshot.id,
        "project_id": snapshot.project_id,
        "version_name": snapshot.version_name,
        "description": snapshot.description,
        "project_version": snapshot.project_version,
        "created_by": snapshot.created_by,
        "created_by_user": creator_info,
        "created_at": snapshot.created_at
    }, "创建成功")


@router.get("/{project_id}/snapshots", response_model=Dict[str, Any])
async def list_snapshots(
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

    snapshots, total = get_project_snapshots(db, project_id, page, page_size)

    items = []
    for snapshot in snapshots:
        creator_info = None
        if snapshot.creator:
            creator_info = {
                "id": snapshot.creator.id,
                "nickname": snapshot.creator.nickname
            }

        items.append({
            "id": snapshot.id,
            "project_id": snapshot.project_id,
            "version_name": snapshot.version_name,
            "description": snapshot.description,
            "project_version": snapshot.project_version,
            "created_by": snapshot.created_by,
            "created_by_user": creator_info,
            "created_at": snapshot.created_at
        })

    return success_response({
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size
    }, "获取成功")


@router.get("/{project_id}/snapshots/{snapshot_id}", response_model=Dict[str, Any])
async def get_snapshot(
    request: Request,
    project_id: int,
    snapshot_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not has_project_access(db, project_id, current_user.id, "read"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "AUTHORIZATION_FAILED", "message": "权限不足"}
        )

    snapshot = get_snapshot_by_id(db, project_id, snapshot_id)
    if not snapshot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "SNAPSHOT_NOT_FOUND", "message": "快照不存在"}
        )

    creator_info = None
    if snapshot.creator:
        creator_info = {
            "id": snapshot.creator.id,
            "nickname": snapshot.creator.nickname
        }

    return success_response({
        "id": snapshot.id,
        "project_id": snapshot.project_id,
        "version_name": snapshot.version_name,
        "description": snapshot.description,
        "snapshot_data": snapshot.snapshot_data,
        "project_version": snapshot.project_version,
        "created_by": snapshot.created_by,
        "created_by_user": creator_info,
        "created_at": snapshot.created_at
    }, "获取成功")


@router.post("/{project_id}/snapshots/{snapshot_id}/restore", response_model=Dict[str, Any])
async def restore_project_snapshot(
    request: Request,
    project_id: int,
    snapshot_id: int,
    restore_data: SnapshotRestoreRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not has_project_access(db, project_id, current_user.id, "write"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "AUTHORIZATION_FAILED", "message": "权限不足，需要写入权限"}
        )

    result = restore_snapshot(db, project_id, snapshot_id, restore_data, current_user.id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "SNAPSHOT_NOT_FOUND", "message": "快照不存在"}
        )

    return success_response(result, "恢复成功")


@router.delete("/{project_id}/snapshots/{snapshot_id}", response_model=Dict[str, Any])
async def delete_project_snapshot(
    request: Request,
    project_id: int,
    snapshot_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not has_project_access(db, project_id, current_user.id, "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "AUTHORIZATION_FAILED", "message": "权限不足，需要管理员权限"}
        )

    success = delete_snapshot(db, project_id, snapshot_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "SNAPSHOT_NOT_FOUND", "message": "快照不存在"}
        )

    return success_response(None, "删除成功")
