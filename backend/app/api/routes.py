"""
Root API router.

This module aggregates routers from different submodules so main.py can mount a
single router.
"""

from fastapi import APIRouter

from app.api.admin import router as admin_router
from app.api.profile import router as profile_router
from app.api.requests import router as requests_router
from app.auth import email_auth_router

api_router = APIRouter()

# Authentication routes
api_router.include_router(email_auth_router)
# Admin routes
api_router.include_router(admin_router)
# Profile routes
api_router.include_router(profile_router)
# Help request routes
api_router.include_router(requests_router)

