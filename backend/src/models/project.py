from sqlalchemy import Column, BigInteger, String, Text, DateTime, ForeignKey, Boolean, Index, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import JSON
from datetime import datetime
from src.db.session import Base


def utc_now():
    """返回当前UTC时间"""
    return datetime.utcnow()

ID_TYPE = BigInteger


class Project(Base):
    __tablename__ = "projects"

    id = Column(ID_TYPE, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    thumbnail_url = Column(String(500), nullable=True)
    owner_id = Column(ID_TYPE, ForeignKey("users.id"), nullable=False, index=True)
    team_id = Column(ID_TYPE, ForeignKey("teams.id"), nullable=True, index=True)
    template_type = Column(String(20), nullable=False, default="blank")
    template_id = Column(ID_TYPE, nullable=True)
    target_platforms = Column(JSON, nullable=False, default=list)
    status = Column(String(20), nullable=False, default="draft")
    config = Column(JSON, nullable=True)
    project_data = Column(JSON, nullable=True)
    version = Column(Integer, nullable=False, default=1)
    last_edited_by = Column(ID_TYPE, ForeignKey("users.id"), nullable=True)
    last_edited_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=utc_now)
    updated_at = Column(DateTime, nullable=False, default=utc_now, onupdate=utc_now)

    owner = relationship("User", foreign_keys=[owner_id], back_populates="owned_projects")
    team = relationship("Team", back_populates="projects")
    last_editor = relationship("User", foreign_keys=[last_edited_by])
    pages = relationship("Page", back_populates="project", cascade="all, delete-orphan")
    snapshots = relationship("ProjectSnapshot", back_populates="project", cascade="all, delete-orphan")
    shares = relationship("ProjectShare", back_populates="project", cascade="all, delete-orphan")
    collaborators = relationship("ProjectCollaborator", back_populates="project", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_projects_status", "status"),
        Index("idx_projects_created_at", "created_at"),
        {"mysql_engine": "InnoDB"},
    )


class Page(Base):
    __tablename__ = "pages"

    id = Column(ID_TYPE, primary_key=True, autoincrement=True)
    project_id = Column(ID_TYPE, ForeignKey("projects.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    path = Column(String(200), nullable=False)
    is_home = Column(Boolean, nullable=False, default=False)
    layout_config = Column(JSON, nullable=True)
    components = Column(JSON, nullable=True)
    sort_order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=utc_now)
    updated_at = Column(DateTime, nullable=False, default=utc_now, onupdate=utc_now)

    project = relationship("Project", back_populates="pages")
    states = relationship("PageState", back_populates="page", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_pages_project_path", "project_id", "path", unique=True),
        {"mysql_engine": "InnoDB"},
    )


class PageState(Base):
    __tablename__ = "page_states"

    id = Column(ID_TYPE, primary_key=True, autoincrement=True)
    page_id = Column(ID_TYPE, ForeignKey("pages.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    data_type = Column(String(20), nullable=False)
    default_value = Column(JSON, nullable=True)
    description = Column(Text, nullable=True)

    page = relationship("Page", back_populates="states")

    __table_args__ = ({"mysql_engine": "InnoDB"},)


class ProjectSnapshot(Base):
    __tablename__ = "project_snapshots"

    id = Column(ID_TYPE, primary_key=True, autoincrement=True)
    project_id = Column(ID_TYPE, ForeignKey("projects.id"), nullable=False, index=True)
    version_name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    snapshot_data = Column(JSON, nullable=False)
    project_version = Column(Integer, nullable=False)
    created_by = Column(ID_TYPE, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=utc_now)

    project = relationship("Project", back_populates="snapshots")
    creator = relationship("User", foreign_keys=[created_by])

    __table_args__ = (
        Index("idx_snapshots_created_at", "created_at"),
        {"mysql_engine": "InnoDB"},
    )


class ProjectShare(Base):
    __tablename__ = "project_shares"

    id = Column(ID_TYPE, primary_key=True, autoincrement=True)
    project_id = Column(ID_TYPE, ForeignKey("projects.id"), nullable=False, index=True)
    share_token = Column(String(100), unique=True, nullable=False, index=True)
    permission = Column(String(20), nullable=False, default="view")
    expires_at = Column(DateTime, nullable=True, index=True)
    is_password_protected = Column(Boolean, nullable=False, default=False)
    password_hash = Column(String(255), nullable=True)
    view_count = Column(Integer, nullable=False, default=0)
    copy_count = Column(Integer, nullable=False, default=0)
    max_views = Column(Integer, nullable=True)
    max_copies = Column(Integer, nullable=True)
    created_by = Column(ID_TYPE, ForeignKey("users.id"), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=utc_now)
    updated_at = Column(DateTime, nullable=False, default=utc_now, onupdate=utc_now)

    project = relationship("Project", back_populates="shares")
    creator = relationship("User", foreign_keys=[created_by])

    __table_args__ = ({"mysql_engine": "InnoDB"},)


class ProjectCollaborator(Base):
    __tablename__ = "project_collaborators"

    id = Column(ID_TYPE, primary_key=True, autoincrement=True)
    project_id = Column(ID_TYPE, ForeignKey("projects.id"), nullable=False, index=True)
    user_id = Column(ID_TYPE, ForeignKey("users.id"), nullable=False, index=True)
    permission = Column(String(20), nullable=False, default="write")
    invited_by = Column(ID_TYPE, ForeignKey("users.id"), nullable=True)
    joined_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=utc_now)
    updated_at = Column(DateTime, nullable=False, default=utc_now, onupdate=utc_now)

    project = relationship("Project", back_populates="collaborators")
    user = relationship("User", foreign_keys=[user_id], back_populates="project_collaborators")
    inviter = relationship("User", foreign_keys=[invited_by])

    __table_args__ = (
        Index("idx_collaborators_project_user", "project_id", "user_id", unique=True),
        {"mysql_engine": "InnoDB"},
    )


class ProjectTemplate(Base):
    __tablename__ = "project_templates"

    id = Column(ID_TYPE, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    thumbnail_url = Column(String(500), nullable=True)
    category = Column(String(50), nullable=True, index=True)
    template_data = Column(JSON, nullable=False)
    target_platforms = Column(JSON, nullable=False)
    is_public = Column(Boolean, nullable=False, default=False, index=True)
    created_by = Column(ID_TYPE, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, nullable=False, default=utc_now)
    updated_at = Column(DateTime, nullable=False, default=utc_now, onupdate=utc_now)

    creator = relationship("User", foreign_keys=[created_by])

    __table_args__ = ({"mysql_engine": "InnoDB"},)
