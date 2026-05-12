from fastapi import Depends, HTTPException, status, Request, Path
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from datetime import datetime
from typing import Optional, Union, Tuple, Callable

from src.db.session import get_db
from src.models.user import User, UserSession
from src.models.team import TeamMember
from src.core.config import get_settings

settings = get_settings()
security = HTTPBearer(auto_error=False)


async def get_current_user_and_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Tuple[User, str]:
    """获取当前用户和访问令牌"""
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

    return user, token


async def get_current_user(
    user_and_token: Tuple[User, str] = Depends(get_current_user_and_token)
) -> User:
    """获取当前用户（仅用户信息）"""
    return user_and_token[0]


def require_team_role(min_role: str, team_id_param: str = "team_id"):
    """
    团队权限依赖工厂函数

    Args:
        min_role: 所需的最低角色权限
        team_id_param: 路径参数中团队 ID 的参数名，默认为 "team_id"

    Returns:
        依赖注入函数
    """
    def dependency(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ) -> Callable:
        """
        返回一个实际的权限检查函数
        调用方式: check_team_role = Depends(require_team_role("admin"))
                  team_member = check_team_role(team_id)
        """
        from src.schemas.common import TeamRole
        role_hierarchy = {
            TeamRole.OWNER: 4,
            TeamRole.ADMIN: 3,
            TeamRole.MEMBER: 2,
            TeamRole.VIEWER: 1
        }

        def check_role(team_id: int) -> TeamMember:
            team_member = db.query(TeamMember).filter(
                TeamMember.team_id == team_id,
                TeamMember.user_id == current_user.id
            ).first()

            if not team_member:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="不是团队成员"
                )

            if role_hierarchy.get(team_member.role, 0) < role_hierarchy.get(min_role, 0):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="权限不足"
                )

            return team_member

        return check_role

    return dependency


def require_team_role_direct(min_role: str):
    """
    直接从路径参数获取 team_id 的权限依赖（向后兼容）

    这种方式耦合度较高，但使用简单，适合快速开发
    """
    def dependency(
        team_id: int = Path(..., description="团队 ID"),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
    ):
        from src.schemas.common import TeamRole
        role_hierarchy = {
            TeamRole.OWNER: 4,
            TeamRole.ADMIN: 3,
            TeamRole.MEMBER: 2,
            TeamRole.VIEWER: 1
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

        if role_hierarchy.get(team_member.role, 0) < role_hierarchy.get(min_role, 0):
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
