from enum import Enum
from pydantic import BaseModel
from typing import Optional, Any, Generic, TypeVar

T = TypeVar('T')

class TeamRole(str, Enum):
    """团队角色枚举"""
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"

class ResponseStatus(str, Enum):
    """响应状态枚举"""
    SUCCESS = "success"
    ERROR = "error"

class ErrorCode(str, Enum):
    """错误码枚举"""
    VALIDATION_ERROR = "VALIDATION_ERROR"
    AUTHENTICATION_FAILED = "AUTHENTICATION_FAILED"
    AUTHORIZATION_FAILED = "AUTHORIZATION_FAILED"
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    RESOURCE_CONFLICT = "RESOURCE_CONFLICT"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"

class SuccessResponse(BaseModel):
    success: bool = True
    data: Any = None
    message: str = "操作成功"

class ErrorResponse(BaseModel):
    success: bool = False
    error: dict = {
        "code": "ERROR_CODE",
        "message": "错误描述",
        "details": {}
    }
