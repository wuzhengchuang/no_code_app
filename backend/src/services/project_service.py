import json
import secrets
import string
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc, asc

from src.models import (
    Project, Page, ProjectSnapshot, ProjectShare, ProjectCollaborator,
    ProjectTemplate, User, Team, TeamMember
)
from src.schemas import (
    ProjectCreate, ProjectUpdate, ProjectDataUpdate, ProjectCopyRequest,
    ProjectImport
)
from src.services.project_permission_service import (
    get_user_project_permission, has_project_access, is_project_owner,
    ProjectPermission
)


def generate_share_token(length: int = 8) -> str:
    """生成分享令牌"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def create_project(db: Session, project_data: ProjectCreate, user_id: int) -> Project:
    """创建新项目"""
    # 验证模板
    template_data = None
    if project_data.template_type == "from_template" and project_data.template_id:
        template = db.query(ProjectTemplate).filter(
            ProjectTemplate.id == project_data.template_id,
            ProjectTemplate.is_public == True
        ).first()
        if template:
            template_data = template.template_data

    # 创建项目
    db_project = Project(
        name=project_data.name,
        description=project_data.description,
        owner_id=user_id,
        team_id=project_data.team_id,
        template_type=project_data.template_type,
        template_id=project_data.template_id,
        target_platforms=project_data.target_platforms,
        status="draft",
        config={},
        project_data=template_data if template_data else {
            "pages": [],
            "apis": [],
            "dataModels": [],
            "eventBindings": [],
            "globalStates": []
        },
        version=1,
        last_edited_by=user_id,
        last_edited_at=datetime.utcnow()
    )

    db.add(db_project)
    db.commit()
    db.refresh(db_project)

    return db_project


def get_project_by_id(db: Session, project_id: int) -> Optional[Project]:
    """根据ID获取项目"""
    return db.query(Project).filter(Project.id == project_id).first()


def get_user_projects(
    db: Session,
    user_id: int,
    status: Optional[str] = None,
    team_id: Optional[int] = None,
    page: int = 1,
    page_size: int = 20,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    keyword: Optional[str] = None
) -> tuple[List[Project], int]:
    """获取用户的项目列表"""
    query = db.query(Project).filter(
        or_(
            Project.owner_id == user_id,
            Project.team_id.in_(
                db.query(TeamMember.team_id).filter(TeamMember.user_id == user_id)
            ),
            Project.id.in_(
                db.query(ProjectCollaborator.project_id).filter(
                    ProjectCollaborator.user_id == user_id
                )
            )
        )
    )

    # 应用筛选条件
    if status:
        query = query.filter(Project.status == status)

    if team_id:
        query = query.filter(Project.team_id == team_id)

    if keyword:
        query = query.filter(
            or_(
                Project.name.ilike(f"%{keyword}%"),
                Project.description.ilike(f"%{keyword}%")
            )
        )

    # 计算总数
    total = query.count()

    # 排序
    sort_column = getattr(Project, sort_by, Project.created_at)
    if sort_order == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))

    # 分页
    offset = (page - 1) * page_size
    projects = query.offset(offset).limit(page_size).all()

    return projects, total


def update_project(
    db: Session,
    project_id: int,
    project_update: ProjectUpdate,
    user_id: int
) -> Optional[Project]:
    """更新项目基本信息"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        return None

    # 更新字段
    update_data = project_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)

    # 更新最后编辑信息
    project.last_edited_by = user_id
    project.last_edited_at = datetime.utcnow()

    db.commit()
    db.refresh(project)
    return project


def update_project_data(
    db: Session,
    project_id: int,
    data_update: ProjectDataUpdate,
    user_id: int
) -> Optional[Project]:
    """更新项目完整数据（带乐观锁）"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        return None

    # 乐观锁检查
    if project.version != data_update.version:
        raise ValueError("VERSION_CONFLICT")

    # 更新数据
    project.project_data = data_update.project_data
    project.version += 1
    project.last_edited_by = user_id
    project.last_edited_at = datetime.utcnow()

    db.commit()
    db.refresh(project)
    return project


def delete_project(db: Session, project_id: int) -> bool:
    """删除项目"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        return False

    db.delete(project)
    db.commit()
    return True


def duplicate_project(
    db: Session,
    project_id: int,
    copy_request: ProjectCopyRequest,
    user_id: int
) -> Optional[Project]:
    """复制项目"""
    source_project = db.query(Project).filter(Project.id == project_id).first()
    if not source_project:
        return None

    try:
        # 创建新项目
        db_project = Project(
            name=copy_request.name,
            description=source_project.description,
            thumbnail_url=source_project.thumbnail_url,
            owner_id=user_id,
            team_id=copy_request.team_id,
            template_type="blank",
            target_platforms=source_project.target_platforms,
            status="draft",
            config=source_project.config,
            project_data=source_project.project_data,
            version=1,
            last_edited_by=user_id,
            last_edited_at=datetime.utcnow()
        )

        db.add(db_project)
        db.flush()
        db.refresh(db_project)

        # 复制页面
        source_pages = db.query(Page).filter(Page.project_id == project_id).all()
        for source_page in source_pages:
            new_page = Page(
                project_id=db_project.id,
                name=source_page.name,
                path=source_page.path,
                is_home=source_page.is_home,
                layout_config=source_page.layout_config,
                components=source_page.components,
                sort_order=source_page.sort_order
            )
            db.add(new_page)

        db.commit()
        db.refresh(db_project)
        return db_project
    except Exception:
        db.rollback()
        raise


def export_project(db: Session, project_id: int) -> Optional[Dict[str, Any]]:
    """导出项目数据"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        return None

    # 获取页面数据
    pages = db.query(Page).filter(Page.project_id == project_id).all()
    pages_data = []
    for page in pages:
        pages_data.append({
            "name": page.name,
            "path": page.path,
            "is_home": page.is_home,
            "layout_config": page.layout_config,
            "components": page.components,
            "sort_order": page.sort_order
        })

    export_data = {
        "name": project.name,
        "description": project.description,
        "target_platforms": project.target_platforms,
        "config": project.config,
        "project_data": project.project_data,
        "pages": pages_data,
        "version": project.version,
        "exported_at": datetime.utcnow().isoformat()
    }

    return export_data


def import_project(
    db: Session,
    import_data: ProjectImport,
    user_id: int
) -> Project:
    """导入项目"""
    db_project = Project(
        name=import_data.name,
        description=import_data.description,
        owner_id=user_id,
        team_id=import_data.team_id,
        template_type="blank",
        target_platforms=import_data.target_platforms,
        status="draft",
        config=import_data.config or {},
        project_data=import_data.project_data or {
            "pages": [],
            "apis": [],
            "dataModels": [],
            "eventBindings": [],
            "globalStates": []
        },
        version=1,
        last_edited_by=user_id,
        last_edited_at=datetime.utcnow()
    )

    db.add(db_project)
    db.commit()
    db.refresh(db_project)

    # 导入页面
    if import_data.project_data and "pages" in import_data.project_data:
        for page_data in import_data.project_data["pages"]:
            new_page = Page(
                project_id=db_project.id,
                name=page_data.get("name", "未命名页面"),
                path=page_data.get("path", "/pages/index"),
                is_home=page_data.get("is_home", False),
                layout_config=page_data.get("layout_config"),
                components=page_data.get("components"),
                sort_order=page_data.get("sort_order", 0)
            )
            db.add(new_page)

    db.commit()
    return db_project


def get_public_templates(
    db: Session,
    category: Optional[str] = None,
    page: int = 1,
    page_size: int = 20
) -> tuple[List[ProjectTemplate], int]:
    """获取公开模板列表"""
    query = db.query(ProjectTemplate).filter(ProjectTemplate.is_public == True)

    if category:
        query = query.filter(ProjectTemplate.category == category)

    total = query.count()

    offset = (page - 1) * page_size
    templates = query.offset(offset).limit(page_size).all()

    return templates, total
