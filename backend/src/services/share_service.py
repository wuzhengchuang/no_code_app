import secrets
import string
from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc

from src.models import Project, ProjectShare
from src.schemas import ShareCreate, ShareCopyRequest
from src.utils.security import get_password_hash, verify_password


def generate_share_token(length: int = 8) -> str:
    """生成分享令牌"""
    alphabet = string.ascii_letters + string.digits
    while True:
        token = ''.join(secrets.choice(alphabet) for _ in range(length))
        # 确保不包含容易混淆的字符
        token = token.replace('0', 'X').replace('O', 'Y').replace('l', 'Z')
        return token


def create_share(
    db: Session,
    project_id: int,
    share_data: ShareCreate,
    user_id: int
) -> Optional[ProjectShare]:
    """创建项目分享"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        return None

    # 生成唯一分享令牌
    share_token = generate_share_token()
    while db.query(ProjectShare).filter(ProjectShare.share_token == share_token).first():
        share_token = generate_share_token()

    # 处理密码
    password_hash = None
    is_password_protected = False
    if share_data.password:
        password_hash = get_password_hash(share_data.password)
        is_password_protected = True

    db_share = ProjectShare(
        project_id=project_id,
        share_token=share_token,
        permission=share_data.permission,
        expires_at=share_data.expires_at,
        is_password_protected=is_password_protected,
        password_hash=password_hash,
        max_views=share_data.max_views,
        max_copies=share_data.max_copies,
        created_by=user_id,
        is_active=True
    )

    db.add(db_share)
    db.commit()
    db.refresh(db_share)
    return db_share


def get_project_shares(
    db: Session,
    project_id: int,
    page: int = 1,
    page_size: int = 20
) -> tuple[List[ProjectShare], int]:
    """获取项目的分享列表"""
    query = db.query(ProjectShare).filter(
        ProjectShare.project_id == project_id
    ).order_by(desc(ProjectShare.created_at))

    total = query.count()

    offset = (page - 1) * page_size
    shares = query.offset(offset).limit(page_size).all()

    return shares, total


def get_share_by_token(db: Session, share_token: str) -> Optional[ProjectShare]:
    """根据令牌获取分享"""
    return db.query(ProjectShare).filter(
        ProjectShare.share_token == share_token
    ).first()


def delete_share(
    db: Session,
    project_id: int,
    share_id: int
) -> bool:
    """删除分享"""
    share = db.query(ProjectShare).filter(
        ProjectShare.id == share_id,
        ProjectShare.project_id == project_id
    ).first()

    if not share:
        return False

    db.delete(share)
    db.commit()
    return True


def validate_share_access(
    db: Session,
    share_token: str,
    password: Optional[str] = None
) -> Optional[dict]:
    """
    验证分享访问权限
    返回: {"valid": bool, "share": ProjectShare, "error": str}
    """
    share = get_share_by_token(db, share_token)

    if not share:
        return {"valid": False, "share": None, "error": "SHARE_NOT_FOUND"}

    if not share.is_active:
        return {"valid": False, "share": share, "error": "SHARE_NOT_ACTIVE"}

    # 检查是否过期
    if share.expires_at and share.expires_at < datetime.utcnow():
        return {"valid": False, "share": share, "error": "SHARE_EXPIRED"}

    # 检查查看次数限制
    if share.max_views and share.view_count >= share.max_views:
        return {"valid": False, "share": share, "error": "SHARE_LIMIT_EXCEEDED"}

    # 验证密码
    if share.is_password_protected:
        if not password:
            return {"valid": False, "share": share, "error": "SHARE_PASSWORD_REQUIRED"}
        if not verify_password(password, share.password_hash):
            return {"valid": False, "share": share, "error": "SHARE_PASSWORD_INVALID"}

    return {"valid": True, "share": share, "error": None}


def access_share(
    db: Session,
    share_token: str,
    password: Optional[str] = None
) -> Optional[dict]:
    """访问分享的项目"""
    validation = validate_share_access(db, share_token, password)

    if not validation["valid"]:
        return None

    share = validation["share"]
    project = db.query(Project).filter(Project.id == share.project_id).first()

    if not project:
        return None

    # 原子操作增加查看次数
    db.query(ProjectShare).filter(ProjectShare.id == share.id).update(
        {"view_count": ProjectShare.view_count + 1}
    )
    db.commit()
    db.refresh(share)

    return {
        "project_id": project.id,
        "permission": share.permission,
        "project_name": project.name,
        "project_data": project.project_data if share.permission in ["copy", "fork"] else None
    }


def copy_shared_project(
    db: Session,
    share_token: str,
    copy_request: ShareCopyRequest,
    user_id: int,
    password: Optional[str] = None
) -> Optional[Project]:
    """复制分享的项目"""
    validation = validate_share_access(db, share_token, password)

    if not validation["valid"]:
        return None

    share = validation["share"]

    # 检查权限
    if share.permission not in ["copy", "fork"]:
        return None

    # 检查复制次数限制
    if share.max_copies and share.copy_count >= share.max_copies:
        return None

    project = db.query(Project).filter(Project.id == share.project_id).first()
    if not project:
        return None

    # 创建新项目
    from src.models import Project as ProjectModel, Page

    new_project = ProjectModel(
        name=copy_request.name,
        description=project.description,
        thumbnail_url=project.thumbnail_url,
        owner_id=user_id,
        team_id=copy_request.team_id,
        template_type="blank",
        target_platforms=project.target_platforms,
        status="draft",
        config=project.config,
        project_data=project.project_data,
        version=1,
        last_edited_by=user_id,
        last_edited_at=datetime.utcnow()
    )

    db.add(new_project)
    db.commit()
    db.refresh(new_project)

    try:
        # 复制页面
        pages = db.query(Page).filter(Page.project_id == project.id).all()
        for source_page in pages:
            new_page = Page(
                project_id=new_project.id,
                name=source_page.name,
                path=source_page.path,
                is_home=source_page.is_home,
                layout_config=source_page.layout_config,
                components=source_page.components,
                sort_order=source_page.sort_order
            )
            db.add(new_page)

        # 原子操作增加复制次数
        db.query(ProjectShare).filter(ProjectShare.id == share.id).update(
            {"copy_count": ProjectShare.copy_count + 1}
        )
        db.commit()
    except Exception:
        db.rollback()
        raise

    return new_project


def deactivate_expired_shares(db: Session) -> int:
    """停用所有过期的分享，返回停用的数量"""
    expired_shares = db.query(ProjectShare).filter(
        ProjectShare.is_active == True,
        ProjectShare.expires_at < datetime.utcnow()
    ).all()

    count = 0
    for share in expired_shares:
        share.is_active = False
        count += 1

    if count > 0:
        db.commit()

    return count
