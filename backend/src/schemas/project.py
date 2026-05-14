from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator


class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    target_platforms: List[str] = Field(..., min_items=1, max_items=6)


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    template_type: str = Field(default="blank")
    template_id: Optional[int] = None
    target_platforms: List[str] = Field(..., min_items=1, max_items=6)
    team_id: Optional[int] = None

    @validator("template_type")
    def validate_template_type(cls, v):
        if v not in ["blank", "from_template"]:
            raise ValueError("template_type must be 'blank' or 'from_template'")
        return v

    @validator("target_platforms")
    def validate_platforms(cls, v):
        valid_platforms = [
            "wechat_miniapp",
            "alipay_miniapp",
            "h5",
            "react_native",
            "flutter",
            "uni_app",
            "ios",
            "android",
        ]
        for platform in v:
            if platform not in valid_platforms:
                raise ValueError(f"Invalid platform: {platform}")
        return v


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    thumbnail_url: Optional[str] = Field(None, max_length=500)
    target_platforms: Optional[List[str]] = None
    status: Optional[str] = None

    @validator("status")
    def validate_status(cls, v):
        if v is not None and v not in ["draft", "active", "archived"]:
            raise ValueError("status must be 'draft', 'active', or 'archived'")
        return v

    @validator("target_platforms")
    def validate_platforms(cls, v):
        if v is None:
            return v
        valid_platforms = [
            "wechat_miniapp",
            "alipay_miniapp",
            "h5",
            "react_native",
            "flutter",
            "uni_app",
            "ios",
            "android",
        ]
        for platform in v:
            if platform not in valid_platforms:
                raise ValueError(f"Invalid platform: {platform}")
        return v


class ProjectDataUpdate(BaseModel):
    version: int = Field(..., ge=1)
    project_data: Dict[str, Any]


class ProjectCopyRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    team_id: Optional[int] = None


class ProjectListItem(BaseModel):
    id: int
    name: str
    description: Optional[str]
    thumbnail_url: Optional[str]
    owner_id: int
    owner: Optional[Dict[str, Any]]
    team_id: Optional[int]
    target_platforms: List[str]
    status: str
    last_edited_by: Optional[int]
    last_edited_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProjectResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    thumbnail_url: Optional[str]
    owner_id: int
    owner: Optional[Dict[str, Any]]
    team_id: Optional[int]
    template_type: str
    target_platforms: List[str]
    status: str
    config: Optional[Dict[str, Any]]
    project_data: Optional[Dict[str, Any]]
    version: int
    last_edited_by: Optional[int]
    last_edited_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    collaborators: Optional[List[Dict[str, Any]]] = []

    class Config:
        from_attributes = True


class ProjectListResponse(BaseModel):
    items: List[ProjectListItem]
    total: int
    page: int
    page_size: int


class ProjectExport(BaseModel):
    id: int
    name: str
    description: Optional[str]
    target_platforms: List[str]
    config: Optional[Dict[str, Any]]
    project_data: Optional[Dict[str, Any]]
    version: int
    exported_at: datetime

    class Config:
        from_attributes = True


class ProjectImport(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    target_platforms: List[str] = Field(..., min_items=1, max_items=6)
    config: Optional[Dict[str, Any]] = None
    project_data: Optional[Dict[str, Any]] = None
    team_id: Optional[int] = None


class SnapshotCreate(BaseModel):
    version_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)


class SnapshotResponse(BaseModel):
    id: int
    project_id: int
    version_name: str
    description: Optional[str]
    project_version: int
    created_by: int
    created_by_user: Optional[Dict[str, Any]]
    created_at: datetime

    class Config:
        from_attributes = True


class SnapshotDetailResponse(SnapshotResponse):
    snapshot_data: Dict[str, Any]


class SnapshotListResponse(BaseModel):
    items: List[SnapshotResponse]
    total: int
    page: int
    page_size: int


class SnapshotRestoreRequest(BaseModel):
    create_backup: bool = True


class SnapshotRestoreResponse(BaseModel):
    project_id: int
    new_version: int
    backup_snapshot_id: Optional[int]


class ShareCreate(BaseModel):
    permission: str = Field(default="view")
    expires_at: Optional[datetime] = None
    password: Optional[str] = Field(None, min_length=4, max_length=50)
    max_views: Optional[int] = Field(None, ge=1)
    max_copies: Optional[int] = Field(None, ge=1)

    @validator("permission")
    def validate_permission(cls, v):
        if v not in ["view", "copy", "fork"]:
            raise ValueError("permission must be 'view', 'copy', or 'fork'")
        return v


class ShareResponse(BaseModel):
    id: int
    project_id: int
    share_token: str
    permission: str
    expires_at: Optional[datetime]
    is_password_protected: bool
    view_count: int
    copy_count: int
    max_views: Optional[int]
    max_copies: Optional[int]
    is_active: bool
    created_by: int
    created_at: datetime

    class Config:
        from_attributes = True


class ShareListResponse(BaseModel):
    items: List[ShareResponse]
    total: int
    page: int
    page_size: int


class ShareAccessRequest(BaseModel):
    password: Optional[str] = None


class ShareAccessResponse(BaseModel):
    project_id: int
    permission: str
    project_name: str
    project_data: Optional[Dict[str, Any]]


class ShareCopyRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    team_id: Optional[int] = None


class TemplateResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    thumbnail_url: Optional[str]
    category: Optional[str]
    target_platforms: List[str]
    is_public: bool
    created_by: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class TemplateListResponse(BaseModel):
    items: List[TemplateResponse]
    total: int
    page: int
    page_size: int


class CollaboratorCreate(BaseModel):
    user_id: int
    permission: str = Field(default="write")

    @validator("permission")
    def validate_permission(cls, v):
        if v not in ["read", "write", "admin"]:
            raise ValueError("permission must be 'read', 'write', or 'admin'")
        return v


class CollaboratorResponse(BaseModel):
    id: int
    project_id: int
    user_id: int
    user: Optional[Dict[str, Any]]
    permission: str
    invited_by: Optional[int]
    joined_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class CollaboratorUpdate(BaseModel):
    permission: str

    @validator("permission")
    def validate_permission(cls, v):
        if v not in ["read", "write", "admin"]:
            raise ValueError("permission must be 'read', 'write', or 'admin'")
        return v


class CollaboratorListResponse(BaseModel):
    items: List[CollaboratorResponse]
    total: int
