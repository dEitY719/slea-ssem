"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.backend.api import auth, profile, questions, survey

app = FastAPI(
    title="SLEA-SSEM",
    description="AI-driven learning platform for S.LSI employees",
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

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(survey.router, prefix="/survey", tags=["survey"])
app.include_router(profile.router, prefix="/profile", tags=["profile"])
app.include_router(questions.router, prefix="/questions", tags=["questions"])


@app.get("/")
async def root() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok", "message": "SLEA-SSEM API is running"}


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
