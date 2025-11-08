"""
Mode 1 Question Generation Pipeline - Orchestrate Tools 1-5.

REQ: REQ-A-Mode1-Pipeline
Pipeline orchestrator for generating questions using Tools 1-5 in ReAct pattern.
"""

import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from src.agent.tools.difficulty_keywords_tool import get_difficulty_keywords
from src.agent.tools.save_question_tool import save_generated_question
from src.agent.tools.search_templates_tool import search_question_templates
from src.agent.tools.user_profile_tool import get_user_profile
from src.agent.tools.validate_question_tool import validate_question_quality

logger = logging.getLogger(__name__)

# Category mappings
TECHNICAL_DOMAINS = {
    "LLM",
    "RAG",
    "Agent Architecture",
    "Prompt Engineering",
    "Fine-tuning",
}
BUSINESS_DOMAINS = {
    "Product Strategy",
    "Team Management",
    "Project Planning",
}


def get_top_category(domain: str) -> str:
    """
    Map domain to top-level category.

    Args:
        domain: Domain name (e.g., "LLM", "RAG")

    Returns:
        Top-level category: "technical", "business", or "general"

    """
    if domain in TECHNICAL_DOMAINS:
        return "technical"
    elif domain in BUSINESS_DOMAINS:
        return "business"
    else:
        return "general"


class Mode1Pipeline:
    """
    Mode 1 Question Generation Pipeline.

    REQ: REQ-A-Mode1-Pipeline

    Orchestrates Tools 1-5 for generating questions using ReAct pattern.
    Handles conditional tool selection, error recovery, and metadata preservation.
    """

    def __init__(self, session_id: str | None = None) -> None:
        """
        Initialize Mode 1 pipeline.

        Args:
            session_id: Optional session ID for tracking

        """
        self.session_id = session_id or str(uuid.uuid4())
        logger.info(f"Mode1Pipeline initialized with session_id={self.session_id}")

    def _generate_round_id(self, session_id: str, round_number: int) -> str:
        """
        Generate round_id for tracking.

        Format: "{session_id}_{round_number}_{timestamp}"

        Args:
            session_id: Session ID
            round_number: Round number (1 or 2)

        Returns:
            Round ID string

        """
        timestamp = datetime.now(UTC).isoformat()
        round_id = f"{session_id}_{round_number}_{timestamp}"
        logger.debug(f"Generated round_id: {round_id}")
        return round_id

    def _call_tool1(self, user_id: str, max_retries: int = 3) -> dict[str, Any]:
        """
        Call Tool 1: Get User Profile.

        REQ: REQ-A-Mode1-Pipeline, AC1

        Retry logic: Fail → Retry 3x → Default values

        Args:
            user_id: User ID
            max_retries: Maximum retry attempts

        Returns:
            User profile dict

        """
        logger.info(f"Tool 1: Getting user profile for {user_id}")

        for attempt in range(max_retries):
            try:
                profile = get_user_profile(user_id)
                logger.info(f"Tool 1: Profile retrieved (attempt {attempt + 1})")
                return profile
            except Exception as e:
                logger.warning(f"Tool 1: Attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    continue

        # Fallback to default
        logger.warning("Tool 1: Using default profile after all retries failed")
        return {
            "user_id": user_id,
            "self_level": "beginner",
            "years_experience": 0,
            "job_role": "Unknown",
            "duty": "Not specified",
            "interests": [],
            "previous_score": 0,
        }

    def _call_tool2(self, interests: list[str], difficulty: int, category: str) -> list[dict[str, Any]]:
        """
        Call Tool 2: Search Question Templates (Conditional).

        REQ: REQ-A-Mode1-Pipeline, AC2

        Logic: If interests exist → Call Tool 2, else → Skip (return [])

        Args:
            interests: User interests
            difficulty: Difficulty level
            category: Category

        Returns:
            List of templates or empty list

        """
        if not interests:
            logger.info("Tool 2: Skipped (no interests)")
            return []

        logger.info(f"Tool 2: Searching templates for interests={interests}")

        try:
            templates = search_question_templates(interests, difficulty, category)
            logger.info(f"Tool 2: Found {len(templates)} templates")
            return templates
        except Exception as e:
            logger.warning(f"Tool 2: Search failed: {e}")
            return []

    def _call_tool3(self, difficulty: int, category: str) -> dict[str, Any]:
        """
        Call Tool 3: Get Difficulty Keywords.

        REQ: REQ-A-Mode1-Pipeline, AC1

        Error handling: Fail → Return cached/default

        Args:
            difficulty: Difficulty level
            category: Category

        Returns:
            Keywords dict

        """
        logger.info(f"Tool 3: Getting keywords for difficulty={difficulty}, category={category}")

        try:
            keywords = get_difficulty_keywords(difficulty, category)
            logger.info("Tool 3: Keywords retrieved")
            return keywords
        except Exception as e:
            logger.error(f"Tool 3: Failed: {e}")
            # Return default keywords
            return {
                "difficulty": difficulty,
                "category": category,
                "keywords": ["General Knowledge", "Understanding", "Application"],
                "concepts": [],
                "example_questions": [],
            }

    def _generate_questions_llm(
        self,
        user_profile: dict[str, Any],
        templates: list[dict[str, Any]],
        keywords: dict[str, Any],
        count: int,
        round_number: int,
    ) -> list[dict[str, Any]]:
        """
        Generate questions using LLM.

        REQ: REQ-A-Mode1-Pipeline, AC1

        Note: Actual LLM implementation would be here.
        For MVP, this is a placeholder that would be integrated with LangChain agent.

        Args:
            user_profile: User profile from Tool 1
            templates: Question templates from Tool 2
            keywords: Difficulty keywords from Tool 3
            count: Number of questions to generate
            round_number: Round number (1 or 2)

        Returns:
            List of generated questions

        """
        logger.info(f"LLM: Generating {count} questions for round {round_number}")

        # Placeholder: In actual implementation, this would call LLM
        # For now, return empty list - actual LLM generation would happen via LangChain agent
        return []

    def _call_tool4(self, questions: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """
        Call Tool 4: Validate Question Quality (Batch).

        REQ: REQ-A-Mode1-Pipeline, AC5

        Batch validation with recommendations: pass/revise/reject

        Args:
            questions: List of questions to validate

        Returns:
            List of validation results with recommendations

        """
        if not questions:
            logger.info("Tool 4: No questions to validate")
            return []

        logger.info(f"Tool 4: Batch validating {len(questions)} questions")

        try:
            # Batch validation
            results = validate_question_quality(
                stem=[q["stem"] for q in questions],
                question_type=[q.get("question_type", "short_answer") for q in questions],
                choices=[q.get("choices") for q in questions],
                correct_answer=[q.get("correct_answer") for q in questions],
                batch=True,
            )
            logger.info("Tool 4: Batch validation completed")
            return results
        except Exception as e:
            logger.error(f"Tool 4: Batch validation failed: {e}")
            # Return default validation (reject all)
            return [
                {
                    "is_valid": False,
                    "score": 0.5,
                    "rule_score": 0.5,
                    "final_score": 0.5,
                    "recommendation": "reject",
                    "feedback": "Validation failed",
                    "issues": ["Validation service error"],
                }
                for _ in questions
            ]

    def _call_tool5(self, question: dict[str, Any], round_id: str, validation_score: float) -> dict[str, Any]:
        """
        Call Tool 5: Save Generated Question.

        REQ: REQ-A-Mode1-Pipeline, AC1

        Saves questions that pass validation (recommendation="pass").

        Args:
            question: Question dict
            round_id: Round ID for tracking
            validation_score: Validation score from Tool 4

        Returns:
            Save result dict

        """
        logger.info(f"Tool 5: Saving question (validation_score={validation_score})")

        try:
            result = save_generated_question(
                item_type=question.get("item_type", "short_answer"),
                stem=question["stem"],
                choices=question.get("choices"),
                correct_key=question.get("correct_key"),
                correct_keywords=question.get("correct_keywords"),
                difficulty=question.get("difficulty", 5),
                categories=question.get("categories", ["general"]),
                round_id=round_id,
                validation_score=validation_score,
                explanation=question.get("explanation"),
            )
            logger.info(f"Tool 5: Question saved (id={result.get('question_id')})")
            return result
        except Exception as e:
            logger.error(f"Tool 5: Save failed: {e}")
            return {
                "question_id": None,
                "round_id": round_id,
                "saved_at": datetime.now(UTC).isoformat(),
                "success": False,
                "error": str(e),
            }

    def _parse_agent_output(self, saved_questions: list[dict[str, Any]], total_attempted: int) -> dict[str, Any]:
        """
        Parse and format final output.

        REQ: REQ-A-Mode1-Pipeline, AC7

        Args:
            saved_questions: Successfully saved questions
            total_attempted: Total questions attempted

        Returns:
            Formatted response dict

        """
        success_count = len(saved_questions)

        if success_count == 0:
            status = "failed"
        elif success_count < total_attempted:
            status = "partial"
        else:
            status = "success"

        return {
            "status": status,
            "generated_count": success_count,
            "total_attempted": total_attempted,
            "questions": saved_questions,
        }

    def generate_questions(
        self,
        user_id: str,
        round_number: int,
        count: int = 5,
        previous_score: int | None = None,
    ) -> dict[str, Any]:
        """
        Generate questions using Mode 1 pipeline.

        REQ: REQ-A-Mode1-Pipeline

        Orchestrates Tools 1-5:
        1. Tool 1: Get user profile (required, retry 3x)
        2. Tool 2: Search templates (conditional, skip if no interests)
        3. Tool 3: Get keywords (required, fallback to default)
        4. LLM: Generate questions (required)
        5. Tool 4: Batch validate (required)
        6. Tool 5: Save passing questions (conditional, on pass recommendation)

        Args:
            user_id: User ID
            round_number: Round number (1 or 2)
            count: Number of questions to generate
            previous_score: Previous round score (for round 2)

        Returns:
            dict with status, generated_count, questions list

        """
        logger.info(f"Generating {count} questions for user={user_id}, round={round_number}")

        round_id = self._generate_round_id(self.session_id, round_number)

        # Step 1: Get User Profile (Required)
        logger.info("Step 1: Tool 1 - Get User Profile")
        user_profile = self._call_tool1(user_id)

        # Determine difficulty based on round and score
        difficulty = self._calculate_difficulty(round_number, previous_score, user_profile)
        category = get_top_category(user_profile.get("interests", [""])[0])

        # Step 2: Search Question Templates (Conditional)
        logger.info("Step 2: Tool 2 - Search Question Templates")
        templates = self._call_tool2(user_profile.get("interests", []), difficulty, category)

        # Step 3: Get Difficulty Keywords (Required)
        logger.info("Step 3: Tool 3 - Get Difficulty Keywords")
        keywords = self._call_tool3(difficulty, category)

        # Step 4: Generate Questions with LLM (Required)
        logger.info("Step 4: LLM - Generate Questions")
        generated_questions = self._generate_questions_llm(user_profile, templates, keywords, count, round_number)

        if not generated_questions:
            logger.warning("No questions generated by LLM")
            return self._parse_agent_output([], 0)

        # Step 5: Batch Validate Questions (Required)
        logger.info("Step 5: Tool 4 - Batch Validate Questions")
        validation_results = self._call_tool4(generated_questions)

        # Step 6: Save Passing Questions (Conditional)
        logger.info("Step 6: Tool 5 - Save Generated Questions")
        saved_questions = []

        for question, validation_result in zip(generated_questions, validation_results, strict=True):
            # Only save if recommendation is "pass"
            if validation_result.get("recommendation") == "pass":
                save_result = self._call_tool5(question, round_id, validation_result.get("final_score", 0))

                if save_result.get("success"):
                    # Merge question with save result
                    saved_question = {
                        "question_id": save_result["question_id"],
                        "stem": question["stem"],
                        "type": question.get("item_type", question.get("question_type")),
                        "choices": question.get("choices"),
                        "correct_answer": question.get("correct_key", question.get("correct_answer")),
                        "correct_keywords": question.get("correct_keywords"),
                        "difficulty": question.get("difficulty", difficulty),
                        "category": question.get("category", category),
                        "validation_score": validation_result.get("final_score"),
                        "saved_at": save_result["saved_at"],
                    }
                    saved_questions.append(saved_question)
            else:
                logger.info(f"Question not saved: recommendation={validation_result.get('recommendation')}")

        # Step 7: Parse Output
        return self._parse_agent_output(saved_questions, len(generated_questions))

    def _calculate_difficulty(self, round_number: int, previous_score: int | None, user_profile: dict[str, Any]) -> int:
        """
        Calculate appropriate difficulty for this round.

        Args:
            round_number: Round number (1 or 2)
            previous_score: Previous round score
            user_profile: User profile

        Returns:
            Difficulty level (1-10)

        """
        if round_number == 1:
            # Round 1: Base on self-assessment level
            levels = {"beginner": 2, "intermediate": 5, "advanced": 8}
            return levels.get(user_profile.get("self_level", "intermediate"), 5)
        else:
            # Round 2: Adapt based on previous score
            if previous_score is None:
                return 5

            if previous_score >= 80:
                return 7  # Increase difficulty
            elif previous_score >= 60:
                return 5  # Keep same
            else:
                return 3  # Decrease difficulty

        return 5  # Default


# Placeholder for LLM generation function
def generate_questions_llm(
    user_profile: dict[str, Any],
    templates: list[dict[str, Any]],
    keywords: dict[str, Any],
    count: int,
    round_number: int,
) -> list[dict[str, Any]]:
    """Generate questions using LLM (placeholder for integration)."""
    return []
