"""Backend API routers."""

from src.backend.api.auth import router as auth_router
from src.backend.api.profile import router as profile_router

__all__ = ["auth_router", "profile_router"]
