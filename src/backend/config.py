"""Backend configuration settings."""

import os


class Settings:
    """
    Application settings.

    Attributes:
        JWT_ALGORITHM: JWT signing algorithm
        JWT_SECRET_KEY: Secret key for JWT signing
        JWT_EXPIRATION_HOURS: JWT token expiration time in hours
        OIDC_CLIENT_ID: Azure AD application (client) ID
        OIDC_CLIENT_SECRET: Azure AD client secret
        OIDC_TENANT_ID: Azure AD tenant ID
        OIDC_TOKEN_ENDPOINT: Azure AD token endpoint URL
        OIDC_JWKS_ENDPOINT: Azure AD JWKS (JSON Web Key Set) endpoint for signature verification

    """

    JWT_ALGORITHM: str = "HS256"
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    JWT_EXPIRATION_HOURS: int = 24

    # OIDC Configuration for Azure AD (REQ-B-A1-1, REQ-B-A1-2, REQ-B-A1-3)
    OIDC_CLIENT_ID: str = os.getenv("OIDC_CLIENT_ID", "")
    OIDC_CLIENT_SECRET: str = os.getenv("OIDC_CLIENT_SECRET", "")
    OIDC_TENANT_ID: str = os.getenv("OIDC_TENANT_ID", "")
    OIDC_REDIRECT_URI: str = os.getenv("OIDC_REDIRECT_URI", "http://localhost:3000/auth/callback")
    OIDC_TOKEN_ENDPOINT: str = ""
    OIDC_JWKS_ENDPOINT: str = ""

    def __init__(self) -> None:
        """
        Initialize settings and construct Azure AD endpoints.

        REQ-B-A1-2, REQ-B-A1-3
        """
        if self.OIDC_TENANT_ID:
            self.OIDC_TOKEN_ENDPOINT = f"https://login.microsoftonline.com/{self.OIDC_TENANT_ID}/oauth2/v2.0/token"
            self.OIDC_JWKS_ENDPOINT = f"https://login.microsoftonline.com/{self.OIDC_TENANT_ID}/discovery/v2.0/keys"


settings = Settings()
