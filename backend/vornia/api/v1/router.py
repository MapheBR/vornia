"""API v1 router."""

from fastapi import APIRouter

from vornia.api.v1.auth import router as auth_router
from vornia.api.v1.employees import router as employees_router

router = APIRouter()
router.include_router(auth_router, prefix="/auth")
router.include_router(employees_router)
