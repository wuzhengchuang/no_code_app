from sqlalchemy import Column, Integer, BigInteger, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from src.db.session import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    nickname = Column(String(100), nullable=False)
    avatar_url = Column(String(500), nullable=True)
    status = Column(Integer, nullable=False, default=1)
    last_login_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    owned_teams = relationship("Team", back_populates="owner", foreign_keys="Team.owner_id")
    team_memberships = relationship("TeamMember", back_populates="user", foreign_keys="TeamMember.user_id")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    project_permissions = relationship("UserProjectPermission", back_populates="user", foreign_keys="UserProjectPermission.user_id")
    granted_permissions = relationship("UserProjectPermission", back_populates="granter", foreign_keys="UserProjectPermission.granted_by")
    invited_teams = relationship("TeamMember", back_populates="inviter", foreign_keys="TeamMember.invited_by")

class UserSession(Base):
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    token = Column(String(500), unique=True, nullable=False, index=True)
    refresh_token = Column(String(500), unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)
    refresh_expires_at = Column(DateTime, nullable=False)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    device_type = Column(String(20), nullable=True)
    is_revoked = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    user = relationship("User", back_populates="sessions")

class UserProjectPermission(Base):
    __tablename__ = "user_project_permissions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    project_id = Column(Integer, nullable=False, index=True)
    permission = Column(String(20), nullable=False)
    granted_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    user = relationship("User", back_populates="project_permissions", foreign_keys=[user_id])
    granter = relationship("User", back_populates="granted_permissions", foreign_keys=[granted_by])
