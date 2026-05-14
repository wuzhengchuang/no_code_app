from sqlalchemy import Column, BigInteger, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

def utc_now():
    """返回当前UTC时间"""
    return datetime.utcnow()
from src.db.session import Base

class Team(Base):
    __tablename__ = "teams"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500), nullable=True)
    owner_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=utc_now)
    updated_at = Column(DateTime, nullable=False, default=utc_now, onupdate=utc_now)

    owner = relationship("User", back_populates="owned_teams", foreign_keys=[owner_id])
    members = relationship("TeamMember", back_populates="team", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="team")

class TeamMember(Base):
    __tablename__ = "team_members"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    team_id = Column(BigInteger, ForeignKey("teams.id"), nullable=False, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
    role = Column(String(20), nullable=False, default="member")
    invited_by = Column(BigInteger, ForeignKey("users.id"), nullable=True)
    joined_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=utc_now)
    updated_at = Column(DateTime, nullable=False, default=utc_now, onupdate=utc_now)

    team = relationship("Team", back_populates="members")
    user = relationship("User", back_populates="team_memberships", foreign_keys=[user_id])
    inviter = relationship("User", back_populates="invited_teams", foreign_keys=[invited_by])

    __table_args__ = (
        {'mysql_engine': 'InnoDB'},
    )
