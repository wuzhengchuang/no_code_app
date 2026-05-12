from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional, List
from .user import UserBase

class TeamCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="团队名称")
    description: Optional[str] = Field(None, max_length=500, description="团队描述")

class TeamUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)

class TeamResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    ownerId: int
    createdAt: datetime
    updatedAt: datetime

class TeamListResponse(TeamResponse):
    role: str
    memberCount: int

class TeamMemberAdd(BaseModel):
    email: EmailStr = Field(..., description="成员邮箱")
    role: str = Field(default="member", description="角色：owner/admin/member/viewer")

class TeamMemberUpdate(BaseModel):
    role: str = Field(..., description="新角色")

class TeamMemberResponse(BaseModel):
    id: int
    userId: int
    user: UserBase
    role: str
    invitedBy: Optional[int] = None
    joinedAt: Optional[datetime] = None

class TeamOwnershipTransfer(BaseModel):
    newOwnerId: int = Field(..., description="新所有者的用户ID")

class TeamMemberListResponse(BaseModel):
    members: List[TeamMemberResponse]
    total: int
