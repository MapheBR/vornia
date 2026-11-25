"""API v1 router."""

from fastapi import APIRouter

from vornia.api.v1.auth import router as auth_router
from vornia.api.v1.employees import router as employees_router
from vornia.api.v1.journeys import router as journeys_router
from vornia.api.v1.settings import router as settings_router
from vornia.api.v1.sync import router as sync_router

router = APIRouter()
router.include_router(auth_router, prefix="/auth")
router.include_router(employees_router)
router.include_router(settings_router)
router.include_router(sync_router)
router.include_router(journeys_router)
