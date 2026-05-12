from fastapi import APIRouter

from .auth import router as auth_router
from .users import router as users_router
from .teams import router as teams_router

router = APIRouter()

router.include_router(auth_router, prefix="/auth", tags=["认证"])
router.include_router(users_router, prefix="/users", tags=["用户"])
router.include_router(teams_router, prefix="/teams", tags=["团队"])
