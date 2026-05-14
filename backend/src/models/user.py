from sqlalchemy import Column, BigInteger, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from src.db.session import Base


def utc_now():
    """返回当前UTC时间"""
    return datetime.utcnow()

class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    nickname = Column(String(100), nullable=False)
    avatar_url = Column(String(500), nullable=True)
    status = Column(Integer, nullable=False, default=1)
    last_login_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=utc_now)
    updated_at = Column(DateTime, nullable=False, default=utc_now, onupdate=utc_now)

    owned_teams = relationship("Team", back_populates="owner", foreign_keys="Team.owner_id")
    team_memberships = relationship("TeamMember", back_populates="user", foreign_keys="TeamMember.user_id")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    project_permissions = relationship("UserProjectPermission", back_populates="user", foreign_keys="UserProjectPermission.user_id")
    granted_permissions = relationship("UserProjectPermission", back_populates="granter", foreign_keys="UserProjectPermission.granted_by")
    invited_teams = relationship("TeamMember", back_populates="inviter", foreign_keys="TeamMember.invited_by")
    owned_projects = relationship("Project", back_populates="owner", foreign_keys="Project.owner_id")
    last_edited_projects = relationship("Project", back_populates="last_editor", foreign_keys="Project.last_edited_by")
    project_collaborators = relationship("ProjectCollaborator", back_populates="user", foreign_keys="ProjectCollaborator.user_id")
    created_snapshots = relationship("ProjectSnapshot", back_populates="creator", foreign_keys="ProjectSnapshot.created_by")
    created_shares = relationship("ProjectShare", back_populates="creator", foreign_keys="ProjectShare.created_by")
    invited_collaborators = relationship("ProjectCollaborator", back_populates="inviter", foreign_keys="ProjectCollaborator.invited_by")

class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
    token = Column(String(500), unique=True, nullable=False, index=True)
    refresh_token = Column(String(500), unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)
    refresh_expires_at = Column(DateTime, nullable=False)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    device_type = Column(String(20), nullable=True)
    is_revoked = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=utc_now)

    user = relationship("User", back_populates="sessions")

class UserProjectPermission(Base):
    __tablename__ = "user_project_permissions"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
    project_id = Column(BigInteger, nullable=False, index=True)
    permission = Column(String(20), nullable=False)
    granted_by = Column(BigInteger, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, nullable=False, default=utc_now)

    user = relationship("User", back_populates="project_permissions", foreign_keys=[user_id])
    granter = relationship("User", back_populates="granted_permissions", foreign_keys=[granted_by])
