from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional

class UserRegister(BaseModel):
    email: EmailStr = Field(..., max_length=255, description="用户邮箱")
    password: str = Field(..., min_length=8, description="密码（至少8位，包含字母和数字）")
    nickname: str = Field(..., min_length=1, max_length=100, description="用户昵称")

class UserLogin(BaseModel):
    email: EmailStr = Field(..., description="用户邮箱")
    password: str = Field(..., description="用户密码")

class TokenRefresh(BaseModel):
    refreshToken: str = Field(..., description="刷新令牌")

class TokenResponse(BaseModel):
    token: str = Field(..., description="访问令牌")
    refreshToken: str = Field(..., description="刷新令牌")
    expiresAt: datetime = Field(..., description="访问令牌过期时间")
    refreshExpiresAt: datetime = Field(..., description="刷新令牌过期时间")
    tokenType: str = Field(default="Bearer", description="令牌类型")

class AuthResponse(TokenResponse):
    user: 'UserResponse'

class LogoutRequest(BaseModel):
    refreshToken: str = Field(..., description="刷新令牌")
