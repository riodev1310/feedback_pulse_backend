from fastapi import APIRouter

from .auth import router as auth_router
from .routes import router as analysis_router

router = APIRouter()
router.include_router(auth_router)
router.include_router(analysis_router)

__all__ = ["router"]
