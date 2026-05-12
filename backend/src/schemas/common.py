from pydantic import BaseModel
from typing import Optional, Any

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
