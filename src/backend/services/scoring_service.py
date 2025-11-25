"""
Scoring service for calculating test results and identifying weak areas.

REQ: REQ-B-B3-Score, REQ-B-B2-Adapt
"""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from src.backend.models.attempt_answer import AttemptAnswer
from src.backend.models.question import Question
from src.backend.models.test_result import TestResult
from src.backend.models.test_session import TestSession


class ScoringService:
    """
    Service for calculating scores and analyzing test performance.

    REQ: REQ-B-B3-Score, REQ-B-B2-Adapt

    Methods:
        score_answer: Score individual answer in real-time
        calculate_round_score: Calculate score for completed round
        get_wrong_categories: Identify wrong answer categories

    """

    def __init__(self, session: Session) -> None:
        """
        Initialize ScoringService with database session.

        Args:
            session: SQLAlchemy database session

        """
        self.session = session

    def score_answer(
        self,
        session_id: str,
        question_id: str,
    ) -> dict[str, Any]:
        """
        Score a submitted answer with time penalty.

        REQ: REQ-B-B3-Score-1, 2, 3

        Performance requirement: Complete within 1 second.

        Args:
            session_id: TestSession ID
            question_id: Question ID

        Returns:
            Dictionary with:
                - scored (bool): Whether scoring completed successfully
                - question_id (str): Question ID
                - user_answer (dict/str): User's submitted answer
                - is_correct (bool): Whether answer is correct
                - score (float): Score earned (0-100 for MC/TF; 0-100 for short answer)
                - feedback (str): Human-readable feedback
                - time_penalty_applied (bool): Whether time penalty was applied
                - final_score (float): Score after time penalty
                - scored_at (str): ISO timestamp of scoring

        Raises:
            ValueError: If session, question, or answer not found

        """
        # Validate session exists
        test_session = self.session.query(TestSession).filter_by(id=session_id).first()
        if not test_session:
            raise ValueError(f"Test session {session_id} not found")

        # Validate question exists and belongs to session
        question = self.session.query(Question).filter_by(id=question_id, session_id=session_id).first()
        if not question:
            raise ValueError(f"Question {question_id} not found in session {session_id}")

        # Get the attempt answer (should already exist from autosave)
        attempt_answer = (
            self.session.query(AttemptAnswer).filter_by(session_id=session_id, question_id=question_id).first()
        )
        if not attempt_answer:
            raise ValueError(f"Answer for question {question_id} not found (not yet saved)")

        # Score based on item type
        if question.item_type == "multiple_choice":
            is_correct, base_score = self._score_multiple_choice(attempt_answer.user_answer, question.answer_schema)
        elif question.item_type == "true_false":
            is_correct, base_score = self._score_true_false(attempt_answer.user_answer, question.answer_schema)
        elif question.item_type == "short_answer":
            is_correct, base_score = self._score_short_answer(attempt_answer.user_answer, question.answer_schema)
        else:
            raise ValueError(f"Unknown item type: {question.item_type}")

        # Apply time penalty
        time_penalty_applied, final_score = self._apply_time_penalty(base_score, test_session)

        # Update attempt answer in DB
        attempt_answer.is_correct = is_correct
        attempt_answer.score = final_score
        self.session.commit()
        self.session.refresh(attempt_answer)

        # Generate feedback
        feedback = "정답입니다!" if is_correct else "오답입니다."

        scored_at = datetime.now(UTC)

        return {
            "scored": True,
            "question_id": question_id,
            "user_answer": attempt_answer.user_answer,
            "is_correct": is_correct,
            "score": base_score,
            "feedback": feedback,
            "time_penalty_applied": time_penalty_applied,
            "final_score": final_score,
            "scored_at": scored_at.isoformat(),
        }

    def _score_multiple_choice(
        self,
        user_answer: Any,  # noqa: ANN401
        answer_schema: dict[str, Any],  # noqa: ANN401
    ) -> tuple[bool, float]:
        """
        Score multiple choice question (text-based matching with normalization).

        REQ: REQ-B-B3-Score-2

        Scoring: 0-100 scale
        - Correct: 100.0
        - Incorrect: 0.0

        Since choice order can be randomized for users, answers are compared
        by full choice text. Comparison is normalized for robustness:
        - Case-insensitive (lowercase comparison)
        - Whitespace-normalized (multiple spaces → single space)

        Args:
            user_answer: User's answer dict with "selected_key"
            answer_schema: Answer schema with "correct_key" or "correct_answer"

        Returns:
            Tuple of (is_correct: bool, score: float 0-100)

        Raises:
            ValueError: If user_answer missing required field

        """
        if not isinstance(user_answer, dict):
            raise ValueError("user_answer must be a dictionary for multiple choice")

        if "selected_key" not in user_answer:
            raise ValueError("user_answer missing 'selected_key' field")

        selected_key = str(user_answer["selected_key"]).strip()

        # Try correct_key first (standard format), fallback to correct_answer (agent format)
        # Use explicit None check to handle falsy values like False correctly
        correct_key_value = answer_schema.get("correct_key")
        if correct_key_value is None:
            correct_key_value = answer_schema.get("correct_answer", "")
        correct_key = str(correct_key_value).strip()

        # Normalize both answers for robust comparison:
        # 1. Normalize internal whitespace (multiple spaces → single space)
        # 2. Case-insensitive comparison (convert to lowercase)
        normalized_selected = " ".join(selected_key.split()).lower()
        normalized_correct = " ".join(correct_key.split()).lower()

        is_correct = normalized_selected == normalized_correct
        score = 100.0 if is_correct else 0.0

        return is_correct, score

    def _score_true_false(
        self,
        user_answer: Any,  # noqa: ANN401
        answer_schema: dict[str, Any],  # noqa: ANN401
    ) -> tuple[bool, float]:
        """
        Score true/false question (exact match).

        REQ: REQ-B-B3-Score-2

        Scoring: 0-100 scale
        - Correct: 100.0
        - Incorrect: 0.0

        Args:
            user_answer: User's answer dict with "answer"
            answer_schema: Answer schema with "correct_answer"

        Returns:
            Tuple of (is_correct: bool, score: float 0-100)

        Raises:
            ValueError: If user_answer has invalid format

        """
        if not isinstance(user_answer, dict):
            raise ValueError("user_answer must be a dictionary for true/false")

        if "answer" not in user_answer:
            raise ValueError("user_answer missing 'answer' field")

        user_ans = user_answer["answer"]

        # Normalize user answer to boolean
        if isinstance(user_ans, bool):
            user_bool = user_ans
        elif isinstance(user_ans, str):
            user_lower = user_ans.lower().strip()
            if user_lower in ("true", "yes", "1"):
                user_bool = True
            elif user_lower in ("false", "no", "0"):
                user_bool = False
            else:
                raise ValueError(f"Invalid true/false answer: {user_ans}")
        else:
            raise ValueError(f"Invalid true/false answer type: {type(user_ans)}")

        # Get correct answer
        correct_ans = answer_schema.get("correct_answer")
        if isinstance(correct_ans, str):
            correct_lower = correct_ans.lower().strip()
            correct_bool = correct_lower in ("true", "yes", "1")
        else:
            correct_bool = bool(correct_ans)

        is_correct = user_bool == correct_bool
        score = 100.0 if is_correct else 0.0

        return is_correct, score

    def _score_short_answer(
        self,
        user_answer: Any,  # noqa: ANN401
        answer_schema: dict[str, Any],  # noqa: ANN401
    ) -> tuple[bool, float]:
        """
        Score short answer (keyword matching with partial credit).

        REQ: REQ-B-B3-Score-2

        Uses keyword presence checking with word-level partial credit:
        - Exact match: keyword appears in answer → full credit for this keyword
        - Partial match: some words from keyword appear → partial credit (word_matches / total_words)
        - No match: keyword not found → 0 credit

        Examples:
        - Keywords: ["conversational AI", "dialogue system", "natural language processing"]
        - User answer: "conversational dialogue natural language"
          * "conversational AI": "conversational" matches → 1/2 = 0.5 credit
          * "dialogue system": "dialogue" matches → 1/2 = 0.5 credit
          * "natural language processing": "natural" + "language" match → 2/3 = 0.67 credit
          * Total: (0.5 + 0.5 + 0.67) / 3 = 0.56 → 56 points (instead of 0)

        Args:
            user_answer: User's answer (string or dict)
            answer_schema: Answer schema with "keywords" list

        Returns:
            Tuple of (is_correct: bool, score: 0-100)

        """
        # Extract user answer text
        if isinstance(user_answer, dict):
            answer_text = str(user_answer.get("text", "")).strip()
        else:
            answer_text = str(user_answer).strip()

        # Get keywords
        keywords = answer_schema.get("keywords", [])
        if not keywords:
            # If no keywords specified, treat empty answer as 0 score, non-empty as 100
            return len(answer_text) > 0, 100.0 if len(answer_text) > 0 else 0.0

        # Prepare answer for matching
        answer_lower = answer_text.lower()
        answer_words = set(answer_lower.split())

        # Calculate score with partial credit for each keyword
        total_credit = 0.0
        exact_matches = 0

        for keyword in keywords:
            keyword_lower = str(keyword).lower().strip()
            if not keyword_lower:
                continue

            # First, check for exact match (full keyword in answer)
            if keyword_lower in answer_lower:
                total_credit += 1.0
                exact_matches += 1
            else:
                # Check for partial word-level match
                keyword_words = keyword_lower.split()
                matched_words = sum(1 for word in keyword_words if word in answer_words)

                if matched_words > 0:
                    # Partial credit: (matched_words / total_words_in_keyword)
                    partial_credit = matched_words / len(keyword_words)
                    total_credit += partial_credit

        # Calculate final score
        total_keywords = len(keywords)
        score = (total_credit / total_keywords * 100.0) if total_keywords > 0 else 0.0

        # is_correct: True only if all keywords matched exactly
        is_correct = exact_matches == total_keywords

        return is_correct, score

    def _apply_time_penalty(self, base_score: float, test_session: TestSession) -> tuple[bool, float]:
        """
        Apply time penalty if session exceeded 20-minute limit.

        REQ: REQ-B-B3-Score-3

        Penalty formula:
        - If elapsed_ms <= 1200000ms (20 min): no penalty
        - If elapsed_ms > 1200000ms: penalty = (elapsed - 1200000) / 1200000 * score
        - Final score = max(0, score - penalty)

        Args:
            base_score: Score before penalty (0-100)
            test_session: TestSession with time tracking

        Returns:
            Tuple of (penalty_applied: bool, final_score: float)

        """
        # No penalty if session not started
        if not test_session.started_at:
            return False, base_score

        # No penalty if session not paused (still in_progress)
        if test_session.status != "paused":
            return False, base_score

        # Calculate elapsed time
        paused_at = test_session.paused_at or datetime.now(UTC)
        elapsed = paused_at - test_session.started_at
        elapsed_ms = int(elapsed.total_seconds() * 1000)

        time_limit_ms = test_session.time_limit_ms

        # No penalty if within time limit
        if elapsed_ms <= time_limit_ms:
            return False, base_score

        # Calculate penalty
        excess_ms = elapsed_ms - time_limit_ms
        penalty_ratio = excess_ms / time_limit_ms
        penalty_points = penalty_ratio * base_score

        final_score = max(0.0, base_score - penalty_points)

        return True, final_score

    def _score_all_unscored_answers(self, session_id: str) -> None:
        """
        Score all unscored answers in a session.

        This is called before calculating round score to ensure all answers are scored.
        Processes answers that:
        - Have NULL is_correct (truly unscored), OR
        - Have is_correct=false with score=0 (default autosave values, not yet actually scored)

        Args:
            session_id: TestSession ID

        Raises:
            ValueError: If session/question/answer not found

        """
        # Get all unscored attempt answers for this session
        # Include both truly unscored (NULL) and default-marked (false/0) answers
        from sqlalchemy import and_, or_

        unscored = (
            self.session.query(AttemptAnswer)
            .filter(
                AttemptAnswer.session_id == session_id,
                or_(
                    AttemptAnswer.is_correct.is_(None),
                    and_(AttemptAnswer.is_correct.is_(False), AttemptAnswer.score == 0.0),
                ),
            )
            .all()
        )

        for attempt in unscored:
            # Get the question to determine item type
            question = self.session.query(Question).filter_by(id=attempt.question_id).first()
            if not question:
                continue

            # Score based on item type
            if question.item_type == "multiple_choice":
                is_correct, base_score = self._score_multiple_choice(attempt.user_answer, question.answer_schema)
            elif question.item_type == "true_false":
                is_correct, base_score = self._score_true_false(attempt.user_answer, question.answer_schema)
            elif question.item_type == "short_answer":
                is_correct, base_score = self._score_short_answer(attempt.user_answer, question.answer_schema)
            else:
                continue

            # Apply time penalty
            test_session = self.session.query(TestSession).filter_by(id=session_id).first()
            if test_session:
                _, final_score = self._apply_time_penalty(base_score, test_session)
            else:
                final_score = base_score

            # Update the attempt answer
            attempt.is_correct = is_correct
            attempt.score = final_score
            self.session.commit()

    def calculate_round_score(self, session_id: str, round_num: int) -> dict:
        """
        Calculate score for a completed test round.

        REQ: REQ-B-B3-Score-1, REQ-B-B3-Score-2

        Calculates average score from all attempt answers in session:
        - All question types (MC, TF, SA) use 0-100 scale
        - Multiple choice: 100 if correct, 0 if wrong
        - True-False: 100 if correct, 0 if wrong
        - Short answer: 0-100 based on keyword matching (partial credit)
        - Final score: Average of all question scores

        Args:
            session_id: TestSession ID
            round_num: Round number (1, 2, or 3)

        Returns:
            Dictionary with:
                - score (float): Average score (0-100)
                - total_points (int): Total points earned (sum of all scores)
                - correct_count (int): Number of fully correct answers (score=100)
                - total_count (int): Total questions
                - wrong_categories (dict): Category -> wrong count mapping

        """
        # First, score all unscored answers
        self._score_all_unscored_answers(session_id)

        # Get all attempt answers for this session
        attempts = self.session.query(AttemptAnswer).filter_by(session_id=session_id).all()

        if not attempts:
            raise ValueError(f"No attempt answers found for session {session_id}")

        total_count = len(attempts)
        correct_count = sum(1 for a in attempts if a.is_correct)
        total_points = sum(a.score for a in attempts)

        # Calculate average score (all scores are 0-100 scale)
        # Final score = (sum of all scores) / number of questions
        average_score = (total_points / total_count) if total_count > 0 else 0

        # Get wrong categories
        wrong_categories = self._get_wrong_categories(attempts)

        return {
            "score": round(average_score, 2),
            "total_points": round(total_points, 2),
            "correct_count": correct_count,
            "total_count": total_count,
            "wrong_categories": wrong_categories,
        }

    def _get_wrong_categories(self, attempts: list[AttemptAnswer]) -> dict:
        """
        Identify categories where user got wrong answers.

        REQ: REQ-B-B2-Adapt-3

        Args:
            attempts: List of AttemptAnswer records

        Returns:
            Dictionary mapping category -> number of wrong answers
            Example: {"LLM": 1, "RAG": 2}

        """
        wrong_categories = {}

        for attempt in attempts:
            if not attempt.is_correct:
                # Get question to find category
                question = self.session.query(Question).filter_by(id=attempt.question_id).first()
                if question:
                    category = question.category
                    wrong_categories[category] = wrong_categories.get(category, 0) + 1

        return wrong_categories

    def save_round_result(self, session_id: str, round_num: int) -> TestResult:
        """
        Calculate and persist round result to database.

        Args:
            session_id: TestSession ID
            round_num: Round number

        Returns:
            TestResult record created

        """
        score_data = self.calculate_round_score(session_id, round_num)

        result = TestResult(
            session_id=session_id,
            round=round_num,
            score=score_data["score"],
            total_points=score_data["total_points"],
            correct_count=score_data["correct_count"],
            total_count=score_data["total_count"],
            wrong_categories=score_data["wrong_categories"],
        )

        self.session.add(result)
        self.session.commit()
        return result
