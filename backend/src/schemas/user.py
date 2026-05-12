from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional

class UserBase(BaseModel):
    id: int
    email: EmailStr
    nickname: str
    avatarUrl: Optional[str] = None

class UserResponse(UserBase):
    status: int
    lastLoginAt: Optional[datetime] = None
    createdAt: datetime
    updatedAt: datetime

class UserProfileUpdate(BaseModel):
    nickname: Optional[str] = Field(None, min_length=1, max_length=100)
    avatarUrl: Optional[str] = Field(None, max_length=500)

class UserPasswordUpdate(BaseModel):
    oldPassword: str = Field(..., description="旧密码")
    newPassword: str = Field(..., min_length=8, description="新密码")

class SessionInfo(BaseModel):
    id: int
    ipAddress: Optional[str] = None
    userAgent: Optional[str] = None
    deviceType: Optional[str] = None
    createdAt: datetime
    expiresAt: datetime
    isCurrent: bool = False

from .auth import AuthResponse
AuthResponse.model_rebuild()
