from fastapi import APIRouter

from .auth import router as auth_router
from .users import router as users_router
from .teams import router as teams_router
from .projects import router as projects_router
from .snapshots import router as snapshots_router
from .shares import router as shares_router, public_router as shares_public_router
from .collaborators import router as collaborators_router

router = APIRouter()

# 认证相关路由
router.include_router(auth_router, prefix="/auth", tags=["认证"])
router.include_router(users_router, prefix="/users", tags=["用户"])
router.include_router(teams_router, prefix="/teams", tags=["团队"])

# 项目路由（包含嵌套资源）
projects_router.include_router(snapshots_router, tags=["快照"])
projects_router.include_router(shares_router, tags=["分享"])
projects_router.include_router(collaborators_router, tags=["协作者"])
router.include_router(projects_router, prefix="/projects", tags=["项目"])

# 分享公开路由（独立挂载，用于分享链接访问）
router.include_router(shares_public_router, prefix="/shares/public", tags=["分享"])
