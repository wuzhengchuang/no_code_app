from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from sqlalchemy.orm import Session

from src.db.session import get_db
from src.core.dependencies import get_current_user
from src.models.user import User
from src.schemas.project import (
    ProjectCreate, ProjectUpdate, ProjectDataUpdate, ProjectCopyRequest,
    ProjectImport
)
from src.schemas.common import success_response
from src.services.project_service import (
    create_project, get_project_by_id, get_user_projects,
    update_project, update_project_data, delete_project,
    duplicate_project, export_project, import_project, get_public_templates
)
from src.services.project_permission_service import (
    has_project_access, is_project_owner, ProjectPermission
)

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


@router.post("", response_model=Dict[str, Any])
@optional_limiter("20 per minute")
async def create(
    request: Request,
    project_data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = create_project(db, project_data, current_user.id)
    return success_response({
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "thumbnail_url": project.thumbnail_url,
        "owner_id": project.owner_id,
        "team_id": project.team_id,
        "template_type": project.template_type,
        "target_platforms": project.target_platforms,
        "status": project.status,
        "version": project.version,
        "created_at": project.created_at,
        "updated_at": project.updated_at
    }, "创建成功")


@router.get("", response_model=Dict[str, Any])
async def list(
    request: Request,
    status: Optional[str] = Query(None, description="项目状态: draft/active/archived"),
    team_id: Optional[int] = Query(None, description="团队ID"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    sort_by: str = Query("created_at", description="排序字段"),
    sort_order: str = Query("desc", description="排序方向: asc/desc"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    projects, total = get_user_projects(
        db, current_user.id, status, team_id,
        page, page_size, sort_by, sort_order, keyword
    )

    items = []
    for project in projects:
        owner_info = None
        if project.owner:
            owner_info = {
                "id": project.owner.id,
                "nickname": project.owner.nickname,
                "avatar_url": project.owner.avatar_url
            }

        items.append({
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "thumbnail_url": project.thumbnail_url,
            "owner_id": project.owner_id,
            "owner": owner_info,
            "team_id": project.team_id,
            "target_platforms": project.target_platforms,
            "status": project.status,
            "last_edited_by": project.last_edited_by,
            "last_edited_at": project.last_edited_at,
            "created_at": project.created_at,
            "updated_at": project.updated_at
        })

    return success_response({
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size
    }, "获取成功")


@router.get("/templates", response_model=Dict[str, Any])
async def list_templates(
    request: Request,
    category: Optional[str] = Query(None, description="模板分类"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    templates, total = get_public_templates(db, category, page, page_size)

    items = []
    for template in templates:
        items.append({
            "id": template.id,
            "name": template.name,
            "description": template.description,
            "thumbnail_url": template.thumbnail_url,
            "category": template.category,
            "target_platforms": template.target_platforms,
            "is_public": template.is_public,
            "created_by": template.created_by,
            "created_at": template.created_at
        })

    return success_response({
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size
    }, "获取成功")


@router.get("/{project_id}", response_model=Dict[str, Any])
async def get(
    request: Request,
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "PROJECT_NOT_FOUND", "message": "项目不存在"}
        )

    if not has_project_access(db, project_id, current_user.id, ProjectPermission.READ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "AUTHORIZATION_FAILED", "message": "权限不足"}
        )

    owner_info = None
    if project.owner:
        owner_info = {
            "id": project.owner.id,
            "nickname": project.owner.nickname,
            "avatar_url": project.owner.avatar_url
        }

    collaborators = []
    for collab in project.collaborators:
        if collab.user:
            collaborators.append({
                "id": collab.id,
                "user_id": collab.user_id,
                "user": {
                    "id": collab.user.id,
                    "nickname": collab.user.nickname,
                    "avatar_url": collab.user.avatar_url
                },
                "permission": collab.permission,
                "invited_by": collab.invited_by,
                "joined_at": collab.joined_at
            })

    return success_response({
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "thumbnail_url": project.thumbnail_url,
        "owner_id": project.owner_id,
        "owner": owner_info,
        "team_id": project.team_id,
        "template_type": project.template_type,
        "target_platforms": project.target_platforms,
        "status": project.status,
        "config": project.config,
        "project_data": project.project_data,
        "version": project.version,
        "last_edited_by": project.last_edited_by,
        "last_edited_at": project.last_edited_at,
        "created_at": project.created_at,
        "updated_at": project.updated_at,
        "collaborators": collaborators
    }, "获取成功")


@router.put("/{project_id}", response_model=Dict[str, Any])
async def update(
    request: Request,
    project_id: int,
    project_update: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "PROJECT_NOT_FOUND", "message": "项目不存在"}
        )

    if not has_project_access(db, project_id, current_user.id, ProjectPermission.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "AUTHORIZATION_FAILED", "message": "权限不足"}
        )

    project = update_project(db, project_id, project_update, current_user.id)

    return success_response({
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "thumbnail_url": project.thumbnail_url,
        "target_platforms": project.target_platforms,
        "status": project.status,
        "version": project.version,
        "updated_at": project.updated_at
    }, "更新成功")


@router.put("/{project_id}/data", response_model=Dict[str, Any])
async def update_data(
    request: Request,
    project_id: int,
    data_update: ProjectDataUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not has_project_access(db, project_id, current_user.id, ProjectPermission.WRITE):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "AUTHORIZATION_FAILED", "message": "权限不足"}
        )

    try:
        project = update_project_data(db, project_id, data_update, current_user.id)
    except ValueError as e:
        if str(e) == "VERSION_CONFLICT":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": "VERSION_CONFLICT", "message": "版本冲突，数据已被其他用户修改"}
            )
        raise

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "PROJECT_NOT_FOUND", "message": "项目不存在"}
        )

    return success_response({
        "id": project.id,
        "version": project.version,
        "updated_at": project.updated_at
    }, "更新成功")


@router.delete("/{project_id}", response_model=Dict[str, Any])
async def delete(
    request: Request,
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "PROJECT_NOT_FOUND", "message": "项目不存在"}
        )

    if not is_project_owner(db, project_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "AUTHORIZATION_FAILED", "message": "只有项目所有者可以删除项目"}
        )

    delete_project(db, project_id)

    return success_response(None, "删除成功")


@router.post("/{project_id}/copy", response_model=Dict[str, Any])
@optional_limiter("10 per minute")
async def copy(
    request: Request,
    project_id: int,
    copy_request: ProjectCopyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "PROJECT_NOT_FOUND", "message": "项目不存在"}
        )

    if not has_project_access(db, project_id, current_user.id, ProjectPermission.READ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "AUTHORIZATION_FAILED", "message": "权限不足"}
        )

    new_project = duplicate_project(db, project_id, copy_request, current_user.id)

    return success_response({
        "id": new_project.id,
        "name": new_project.name,
        "status": new_project.status,
        "created_at": new_project.created_at
    }, "复制成功")


@router.post("/{project_id}/export", response_model=Dict[str, Any])
async def export(
    request: Request,
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "PROJECT_NOT_FOUND", "message": "项目不存在"}
        )

    if not has_project_access(db, project_id, current_user.id, ProjectPermission.READ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "AUTHORIZATION_FAILED", "message": "权限不足"}
        )

    export_data = export_project(db, project_id)

    return success_response(export_data, "导出成功")


@router.post("/import", response_model=Dict[str, Any])
@optional_limiter("10 per minute")
async def import_project_endpoint(
    request: Request,
    import_data: ProjectImport,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = import_project(db, import_data, current_user.id)

    return success_response({
        "id": project.id,
        "name": project.name,
        "status": project.status,
        "created_at": project.created_at
    }, "导入成功")
