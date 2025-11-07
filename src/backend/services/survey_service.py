"""
Survey service for self-assessment form schema and submission.

REQ: REQ-B-B1-1, REQ-B-B1-2
"""

from typing import Any

from sqlalchemy.orm import Session

from src.backend.services.profile_service import ProfileService


class SurveyService:
    """
    Service for managing survey schema and submissions.

    REQ: REQ-B-B1-1, REQ-B-B1-2

    Methods:
        get_survey_schema: Return survey form schema with field definitions
        submit_survey: Validate and save survey submission data

    """

    # Survey schema definition
    SURVEY_SCHEMA: dict[str, Any] = {
        "fields": [
            {
                "name": "self_level",
                "type": "enum",
                "label": "자신의 기술 수준",
                "required": False,
                "choices": ["beginner", "intermediate", "advanced"],
                "help_text": "현재 기술 수준을 선택하세요",
            },
            {
                "name": "years_experience",
                "type": "integer",
                "label": "경력 연수",
                "required": False,
                "min": 0,
                "max": 60,
                "help_text": "0~60년 범위에서 입력하세요",
            },
            {
                "name": "job_role",
                "type": "string",
                "label": "직책/직무",
                "required": False,
                "min_length": 1,
                "max_length": 100,
                "help_text": "예: Senior Engineer, Project Manager, Product Manager",
            },
            {
                "name": "duty",
                "type": "string",
                "label": "주요 업무",
                "required": False,
                "min_length": 1,
                "max_length": 500,
                "help_text": "담당하고 있는 주요 업무를 설명해주세요",
            },
            {
                "name": "interests",
                "type": "array",
                "label": "관심 분야",
                "required": False,
                "items": "string",
                "min_items": 1,
                "max_items": 20,
                "choices": [
                    "AI",
                    "LLM",
                    "RAG",
                    "Robotics",
                    "Marketing",
                    "Semiconductor",
                    "Sensor",
                    "RTL",
                    "Backend",
                    "Frontend",
                    "DevOps",
                    "Data Science",
                    "Cloud",
                    "Security",
                ],
                "help_text": "관심 있는 분야를 선택하세요 (여러 개 선택 가능)",
            },
        ]
    }

    def __init__(self, session: Session) -> None:
        """
        Initialize SurveyService with database session.

        Args:
            session: SQLAlchemy database session

        """
        self.session = session
        self.profile_service = ProfileService(session)

    def get_survey_schema(self) -> dict[str, Any]:
        """
        Return survey form schema with field definitions.

        REQ: REQ-B-B1-1

        Returns:
            Dictionary containing survey schema with field metadata

        """
        return self.SURVEY_SCHEMA

    def submit_survey(self, user_id: int, survey_data: dict[str, Any]) -> dict[str, Any]:
        """
        Validate and save survey submission data.

        REQ: REQ-B-B1-2

        Uses ProfileService.update_survey() to save data (maintains audit trail).

        Args:
            user_id: User ID submitting survey
            survey_data: Survey data dict with keys:
                - self_level: 'beginner', 'intermediate', or 'advanced'
                - years_experience: int (0-60)
                - job_role: str (1-100 chars)
                - duty: str (1-500 chars)
                - interests: list[str] (1-20 items)

        Returns:
            Dictionary with:
                - survey_id (str): UUID of created survey
                - user_id (int): User ID
                - self_level (str): Self-assessed level
                - submitted_at (str): ISO format timestamp

        Raises:
            ValueError: If survey data is invalid
            Exception: If user not found

        """
        # Use ProfileService to validate and save (avoids duplication)
        result = self.profile_service.update_survey(user_id, survey_data)
        return result
