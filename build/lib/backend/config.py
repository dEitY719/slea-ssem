"""Backend configuration settings."""

import os


class Settings:
    """
    Application settings.

    Attributes:
        JWT_ALGORITHM: JWT signing algorithm
        JWT_SECRET_KEY: Secret key for JWT signing
        JWT_EXPIRATION_HOURS: JWT token expiration time in hours

    """

    JWT_ALGORITHM: str = "HS256"
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    JWT_EXPIRATION_HOURS: int = 24


settings = Settings()
