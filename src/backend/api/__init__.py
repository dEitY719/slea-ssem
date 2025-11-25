"""Backend API routers and modules."""

# Import submodules to make them available for:
# from src.backend.api import auth, profile, questions, survey
from . import auth, profile, questions, survey
from .auth import router as auth_router
from .profile import router as profile_router
from .questions import router as questions_router
from .survey import router as survey_router

__all__ = [
    "auth",
    "profile",
    "questions",
    "survey",
    "auth_router",
    "profile_router",
    "survey_router",
    "questions_router",
]
