"""FastAPI application entry point."""

import os
from pathlib import Path

from dotenv import load_dotenv

# MUST load environment variables BEFORE importing anything that uses them
env_file = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_file)

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.responses import FileResponse  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402

from src.backend.api import auth, profile, questions, survey  # noqa: E402
from src.backend.database import init_db  # noqa: E402

app = FastAPI(
    title="SLEA-SSEM",
    description="AI-driven learning platform for employees",
    version="1.0.0",
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event() -> None:
    """Initialize database on startup."""
    init_db()


# API endpoints - defined first for priority matching
@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}


# Include API routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(survey.router, prefix="/survey", tags=["survey"])
app.include_router(profile.router, prefix="/profile", tags=["profile"])
app.include_router(questions.router, prefix="/questions", tags=["questions"])


# Static files setup - only if frontend is built
STATIC_DIR = Path(__file__).parent / "static"

if STATIC_DIR.exists() and (STATIC_DIR / "index.html").exists():
    # Mount static assets (CSS, JS, images)
    app.mount("/assets", StaticFiles(directory=str(STATIC_DIR / "assets")), name="assets")

    # SPA fallback - serve index.html for all non-API routes (must be last)
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str) -> FileResponse:
        """
        Serve React SPA for routes not matched by API endpoints.
        Enables client-side routing with React Router.

        Note: This must be defined AFTER all API routes to avoid conflicts.
        API routes (/, /health, /auth/*, /profile/*, etc.) are matched first.
        """
        return FileResponse(STATIC_DIR / "index.html")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
