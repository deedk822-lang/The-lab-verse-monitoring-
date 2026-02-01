"""
API v1 router
"""

from fastapi import APIRouter

from .endpoints import router as endpoints_router

router = APIRouter()
router.include_router(endpoints_router)