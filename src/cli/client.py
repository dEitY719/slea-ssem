"""HTTP API client for CLI communication with FastAPI backend."""

import json
from types import TracebackType
from typing import Any

import httpx


class APIClient:
    """HTTP client for communicating with the FastAPI backend."""

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        timeout: int = 30,
    ) -> None:
        """
        Initialize the API client.

        Args:
            base_url: Base URL of the FastAPI server
            timeout: Request timeout in seconds

        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.client = httpx.Client(base_url=self.base_url, timeout=timeout)
        self.token: str | None = None

    def set_token(self, token: str) -> None:
        """
        Set JWT token for authenticated requests.

        Sets token both in Authorization header and as HTTP cookie.
        """
        self.token = token

    def get_token(self) -> str | None:
        """Get current JWT token."""
        return self.token

    def clear_token(self) -> None:
        """Clear JWT token."""
        self.token = None

    def _get_headers(self) -> dict[str, str]:
        """Get request headers with auth token if available."""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def make_request(
        self,
        method: str,
        path: str,
        json_data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> tuple[int, dict[str, Any] | None, str | None]:
        """
        Make an HTTP request to the API.

        Args:
            method: HTTP method (GET, POST, PUT, etc.)
            path: API path (e.g., '/auth/login')
            json_data: JSON request body
            params: Query parameters

        Returns:
            Tuple of (status_code, response_json, error_message)
            - If successful: (200/201/etc, response_dict, None)
            - If error: (status_code, None, error_message)

        """
        try:
            # Prepare cookies if token is set
            cookies = {}
            if self.token:
                cookies["auth_token"] = self.token

            response = self.client.request(
                method,
                path,
                headers=self._get_headers(),
                json=json_data,
                params=params,
                cookies=cookies,
            )

            if response.status_code >= 400:
                try:
                    error_data = response.json()
                    error_msg = error_data.get("detail", response.text)
                except json.JSONDecodeError:
                    error_msg = response.text

                return response.status_code, None, error_msg

            try:
                return response.status_code, response.json(), None
            except json.JSONDecodeError:
                return response.status_code, {"text": response.text}, None

        except httpx.ConnectError as e:
            return (
                0,
                None,
                f"Failed to connect to {self.base_url}: {str(e)}",
            )
        except httpx.RequestError as e:
            return 0, None, f"Request failed: {str(e)}"

    def close(self) -> None:
        """Close the HTTP client."""
        self.client.close()

    def __enter__(self) -> "APIClient":
        """Context manager entry."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Context manager exit."""
        self.close()
