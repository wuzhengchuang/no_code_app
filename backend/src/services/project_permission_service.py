from typing import Optional
from sqlalchemy.orm import Session
from src.models import Project, ProjectCollaborator, TeamMember, UserProjectPermission


class ProjectPermission:
    NONE = "none"
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"
    OWNER = "owner"


def get_user_project_permission(db: Session, project_id: int, user_id: int) -> str:
    """
    获取用户对项目的权限级别
    权限优先级: owner > admin > write > read > none
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        return ProjectPermission.NONE

    # 1. 检查是否是项目所有者
    if project.owner_id == user_id:
        return ProjectPermission.OWNER

    # 2. 检查项目协作者权限
    collaborator = db.query(ProjectCollaborator).filter(
        ProjectCollaborator.project_id == project_id,
        ProjectCollaborator.user_id == user_id
    ).first()
    if collaborator:
        return collaborator.permission

    # 3. 检查用户项目权限表
    user_perm = db.query(UserProjectPermission).filter(
        UserProjectPermission.user_id == user_id,
        UserProjectPermission.project_id == project_id
    ).first()
    if user_perm:
        return user_perm.permission

    # 4. 检查团队权限
    if project.team_id:
        team_member = db.query(TeamMember).filter(
            TeamMember.team_id == project.team_id,
            TeamMember.user_id == user_id
        ).first()
        if team_member:
            # 团队所有者拥有admin权限
            if team_member.role == "owner":
                return ProjectPermission.ADMIN
            # 团队管理员拥有write权限
            elif team_member.role == "admin":
                return ProjectPermission.WRITE
            # 普通成员拥有read权限
            elif team_member.role == "member":
                return ProjectPermission.READ

    return ProjectPermission.NONE


def has_project_access(db: Session, project_id: int, user_id: int, min_permission: str = ProjectPermission.READ) -> bool:
    """
    检查用户是否有访问项目的权限
    """
    permission = get_user_project_permission(db, project_id, user_id)

    permission_levels = {
        ProjectPermission.NONE: 0,
        ProjectPermission.READ: 1,
        ProjectPermission.WRITE: 2,
        ProjectPermission.ADMIN: 3,
        ProjectPermission.OWNER: 4,
    }

    user_level = permission_levels.get(permission, 0)
    required_level = permission_levels.get(min_permission, 0)

    return user_level >= required_level


def is_project_owner(db: Session, project_id: int, user_id: int) -> bool:
    """
    检查用户是否是项目所有者
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        return False
    return project.owner_id == user_id


def get_project_members(db: Session, project_id: int) -> list:
    """
    获取项目的所有成员（包括所有者、协作者、团队成员）
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        return []

    members = []

    # 添加所有者
    members.append({
        "user_id": project.owner_id,
        "permission": ProjectPermission.OWNER,
        "type": "owner"
    })

    # 添加协作者
    collaborators = db.query(ProjectCollaborator).filter(
        ProjectCollaborator.project_id == project_id
    ).all()
    for collab in collaborators:
        members.append({
            "user_id": collab.user_id,
            "permission": collab.permission,
            "type": "collaborator",
            "invited_by": collab.invited_by,
            "joined_at": collab.joined_at
        })

    # 添加团队成员
    if project.team_id:
        team_members = db.query(TeamMember).filter(
            TeamMember.team_id == project.team_id
        ).all()
        for member in team_members:
            # 跳过所有者（已在上面添加）
            if member.user_id == project.owner_id:
                continue

            if member.role == "owner":
                perm = ProjectPermission.ADMIN
            elif member.role == "admin":
                perm = ProjectPermission.WRITE
            else:
                perm = ProjectPermission.READ

            members.append({
                "user_id": member.user_id,
                "permission": perm,
                "type": "team_member",
                "team_role": member.role
            })

    return members


def can_manage_collaborators(db: Session, project_id: int, user_id: int) -> bool:
    """
    检查用户是否可以管理项目协作者
    只有 owner 和 admin 可以管理协作者
    """
    permission = get_user_project_permission(db, project_id, user_id)
    return permission in [ProjectPermission.OWNER, ProjectPermission.ADMIN]


def can_create_share(db: Session, project_id: int, user_id: int) -> bool:
    """
    检查用户是否可以创建项目分享
    只有 owner 和 admin 可以创建分享
    """
    permission = get_user_project_permission(db, project_id, user_id)
    return permission in [ProjectPermission.OWNER, ProjectPermission.ADMIN]


def can_create_snapshot(db: Session, project_id: int, user_id: int) -> bool:
    """
    检查用户是否可以创建快照
    需要 write 及以上权限
    """
    permission = get_user_project_permission(db, project_id, user_id)
    return permission in [ProjectPermission.OWNER, ProjectPermission.ADMIN, ProjectPermission.WRITE]
