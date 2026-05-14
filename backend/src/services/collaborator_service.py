from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_

from src.models import Project, ProjectCollaborator, User
from src.schemas import CollaboratorCreate, CollaboratorUpdate


def add_collaborator(
    db: Session,
    project_id: int,
    collaborator_data: CollaboratorCreate,
    invited_by: int
) -> Dict[str, Any]:
    """添加项目协作者
    返回: {"success": bool, "collaborator": Optional[ProjectCollaborator], "error": Optional[str]}
    """
    # 检查项目是否存在
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        return {"success": False, "collaborator": None, "error": "PROJECT_NOT_FOUND"}

    # 检查是否是项目所有者
    if project.owner_id == collaborator_data.user_id:
        return {"success": False, "collaborator": None, "error": "CANNOT_ADD_OWNER"}

    # 检查用户是否存在
    user = db.query(User).filter(User.id == collaborator_data.user_id).first()
    if not user:
        return {"success": False, "collaborator": None, "error": "USER_NOT_FOUND"}

    # 检查是否已是协作者
    existing = db.query(ProjectCollaborator).filter(
        and_(
            ProjectCollaborator.project_id == project_id,
            ProjectCollaborator.user_id == collaborator_data.user_id
        )
    ).first()
    if existing:
        # 更新权限
        existing.permission = collaborator_data.permission
        db.commit()
        db.refresh(existing)
        return {"success": True, "collaborator": existing, "error": None}

    db_collaborator = ProjectCollaborator(
        project_id=project_id,
        user_id=collaborator_data.user_id,
        permission=collaborator_data.permission,
        invited_by=invited_by,
        joined_at=datetime.utcnow()
    )

    db.add(db_collaborator)
    db.commit()
    db.refresh(db_collaborator)
    return {"success": True, "collaborator": db_collaborator, "error": None}


def get_project_collaborators(
    db: Session,
    project_id: int
) -> List[ProjectCollaborator]:
    """获取项目的所有协作者"""
    return db.query(ProjectCollaborator).filter(
        ProjectCollaborator.project_id == project_id
    ).all()


def get_collaborator_by_id(
    db: Session,
    project_id: int,
    collaborator_id: int
) -> Optional[ProjectCollaborator]:
    """获取协作者详情"""
    return db.query(ProjectCollaborator).filter(
        and_(
            ProjectCollaborator.id == collaborator_id,
            ProjectCollaborator.project_id == project_id
        )
    ).first()


def update_collaborator(
    db: Session,
    project_id: int,
    collaborator_id: int,
    update_data: CollaboratorUpdate
) -> Optional[ProjectCollaborator]:
    """更新协作者权限"""
    collaborator = get_collaborator_by_id(db, project_id, collaborator_id)
    if not collaborator:
        return None

    collaborator.permission = update_data.permission
    db.commit()
    db.refresh(collaborator)
    return collaborator


def remove_collaborator(
    db: Session,
    project_id: int,
    collaborator_id: int
) -> bool:
    """移除协作者"""
    collaborator = get_collaborator_by_id(db, project_id, collaborator_id)
    if not collaborator:
        return False

    db.delete(collaborator)
    db.commit()
    return True


def remove_collaborator_by_user_id(
    db: Session,
    project_id: int,
    user_id: int
) -> bool:
    """根据用户ID移除协作者"""
    collaborator = db.query(ProjectCollaborator).filter(
        and_(
            ProjectCollaborator.project_id == project_id,
            ProjectCollaborator.user_id == user_id
        )
    ).first()

    if not collaborator:
        return False

    db.delete(collaborator)
    db.commit()
    return True


def is_project_collaborator(
    db: Session,
    project_id: int,
    user_id: int
) -> bool:
    """检查用户是否是项目协作者"""
    return db.query(ProjectCollaborator).filter(
        and_(
            ProjectCollaborator.project_id == project_id,
            ProjectCollaborator.user_id == user_id
        )
    ).first() is not None


def get_user_collaborated_projects(
    db: Session,
    user_id: int
) -> List[ProjectCollaborator]:
    """获取用户作为协作者的所有项目"""
    return db.query(ProjectCollaborator).filter(
        ProjectCollaborator.user_id == user_id
    ).all()
