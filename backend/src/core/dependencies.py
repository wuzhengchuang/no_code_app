from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from datetime import datetime
from typing import Optional, Union

from src.db.session import get_db
from src.models.user import User, UserSession
from src.models.team import TeamMember
from src.core.config import get_settings

settings = get_settings()
security = HTTPBearer(auto_error=False)

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise credentials_exception

    try:
        token = credentials.credentials
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        jti: str = payload.get("jti")

        if user_id is None or token_type != "access":
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    from src.utils.jwt import hash_token
    hashed_token = hash_token(token)
    
    session = db.query(UserSession).filter(
        UserSession.token == hashed_token,
        UserSession.is_revoked == 0
    ).first()

    if not session or session.expires_at < datetime.utcnow():
        raise credentials_exception

    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None or user.status != 1:
        raise credentials_exception

    return user

def require_team_role(min_role: str):
    def dependency(
        team_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ):
        role_hierarchy = {
            'owner': 4,
            'admin': 3,
            'member': 2,
            'viewer': 1
        }

        team_member = db.query(TeamMember).filter(
            TeamMember.team_id == team_id,
            TeamMember.user_id == current_user.id
        ).first()

        if not team_member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="不是团队成员"
            )

        if role_hierarchy[team_member.role] < role_hierarchy[min_role]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足"
            )

        return team_member

    return dependency

def require_project_permission(required_permission: str):
    def dependency(
        project_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ):
        permission_hierarchy = {
            'admin': 3,
            'write': 2,
            'read': 1
        }

        from src.models.user import UserProjectPermission
        project_permission = db.query(UserProjectPermission).filter(
            UserProjectPermission.project_id == project_id,
            UserProjectPermission.user_id == current_user.id
        ).first()

        if project_permission:
            if permission_hierarchy[project_permission.permission] >= permission_hierarchy[required_permission]:
                return project_permission

        from src.models.project import Project
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="项目不存在"
            )

        if project.team_id:
            team_member = db.query(TeamMember).filter(
                TeamMember.team_id == project.team_id,
                TeamMember.user_id == current_user.id
            ).first()

            if team_member:
                team_role_permissions = {
                    'owner': 'admin',
                    'admin': 'admin',
                    'member': 'write',
                    'viewer': 'read'
                }
                user_permission = team_role_permissions[team_member.role]
                if permission_hierarchy[user_permission] >= permission_hierarchy[required_permission]:
                    return True

        if project.owner_id == current_user.id:
            return True

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="项目权限不足"
        )

    return dependency

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    if current_user.status != 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用"
        )
    return current_user
