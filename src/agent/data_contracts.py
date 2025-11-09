"""
REQ-A-DataContract: Tool input/output data contracts for Item-Gen-Agent.

This module defines Pydantic models that specify the exact input/output
schema for all 6 tools in the question generation and scoring pipeline.

Tools:
- Tool 1: Get User Profile
- Tool 2: Search Question Templates
- Tool 3: Get Difficulty Keywords
- Tool 4: Validate Question Quality
- Tool 5: Save Generated Question
- Tool 6: Score & Generate Explanation
"""


from pydantic import BaseModel, Field, field_validator

# ============================================================================
# Tool 1: Get User Profile
# ============================================================================


class Tool1Input(BaseModel):
    """
    Input contract for Tool 1: Get User Profile.

    Retrieves user's self-assessment information for context in question generation.
    """

    user_id: str = Field(..., min_length=1, description="User unique identifier")

    class Config:
        """Pydantic config."""

        str_strip_whitespace = True


class Tool1Output(BaseModel):
    """
    Output contract for Tool 1: Get User Profile.

    Returns user's profile information including level, experience, and interests.
    """

    self_level: int = Field(..., ge=1, le=10, description="Self-assessed level (1-10)")
    years_experience: int = Field(..., ge=0, description="Years of experience in the domain")
    job_role: str = Field(..., description="User's job role/title")
    duty: str = Field(..., description="Primary duty or responsibility")
    interests: list[str] = Field(default_factory=list, description="Areas of interest (e.g., ['LLM', 'RAG'])")
    previous_score: float | None = Field(default=None, ge=0.0, le=100.0, description="Previous test score")

    class Config:
        """Pydantic config."""

        str_strip_whitespace = True


# ============================================================================
# Tool 2: Search Question Templates
# ============================================================================


class Tool2Input(BaseModel):
    """Input contract for Tool 2: Search Question Templates."""

    interests: list[str] = Field(..., min_items=1, description="List of interest areas to search")
    difficulty: int = Field(..., ge=1, le=10, description="Target difficulty level")
    category: str = Field(..., description="Category: 'technical', 'business', or 'general'")

    class Config:
        """Pydantic config."""

        str_strip_whitespace = True


class QuestionTemplate(BaseModel):
    """Represents a question template from the question bank."""

    id: str = Field(..., description="Template ID")
    stem: str = Field(..., description="Question text")
    type: str = Field(..., description="Question type: multiple_choice, true_false, short_answer")
    choices: list[str] | None = Field(default=None, description="Answer choices (if applicable)")
    correct_answer: str = Field(..., description="Correct answer/key")
    correct_rate: float = Field(..., ge=0.0, le=1.0, description="Historical correct answer rate")
    usage_count: int = Field(..., ge=0, description="Number of times used")
    avg_difficulty_score: float = Field(..., ge=0.0, le=10.0, description="Average difficulty rating")

    class Config:
        """Pydantic config."""

        str_strip_whitespace = True


class Tool2Output(BaseModel):
    """Output contract for Tool 2: Search Question Templates."""

    templates: list[QuestionTemplate] = Field(default_factory=list, description="List of matching templates")

    class Config:
        """Pydantic config."""

        str_strip_whitespace = True


# ============================================================================
# Tool 3: Get Difficulty Keywords
# ============================================================================


class Tool3Input(BaseModel):
    """Input contract for Tool 3: Get Difficulty Keywords."""

    difficulty: int = Field(..., ge=1, le=10, description="Difficulty level")
    category: str = Field(..., description="Category: 'technical', 'business', or 'general'")

    class Config:
        """Pydantic config."""

        str_strip_whitespace = True


class Tool3Output(BaseModel):
    """Output contract for Tool 3: Get Difficulty Keywords."""

    keywords: list[str] = Field(..., description="Keywords for this difficulty level")
    concepts: list[str] = Field(..., description="Core concepts to include in questions")
    example_questions: list[str] = Field(..., description="Example questions at this difficulty")

    class Config:
        """Pydantic config."""

        str_strip_whitespace = True


# ============================================================================
# Tool 4: Validate Question Quality
# ============================================================================


class Tool4Input(BaseModel):
    """Input contract for Tool 4: Validate Question Quality."""

    stem: str = Field(..., description="Question text")
    question_type: str = Field(..., description="Type: multiple_choice, true_false, short_answer")
    choices: list[str] | None = Field(default=None, description="Answer choices (if applicable)")
    correct_answer: str = Field(..., description="Correct answer/key")

    class Config:
        """Pydantic config."""

        str_strip_whitespace = True


class Tool4Output(BaseModel):
    """Output contract for Tool 4: Validate Question Quality."""

    is_valid: bool = Field(..., description="Whether question passes validation")
    score: float = Field(..., ge=0.0, le=1.0, description="LLM semantic validation score")
    rule_score: float = Field(..., ge=0.0, le=1.0, description="Rule-based validation score")
    final_score: float = Field(..., ge=0.0, le=1.0, description="min(score, rule_score)")
    recommendation: str = Field(..., description="Action: 'pass', 'revise', or 'reject'")
    feedback: str = Field(..., description="Validation feedback message")
    issues: list[str] = Field(default_factory=list, description="List of identified issues")

    @field_validator("recommendation")
    @classmethod
    def validate_recommendation(cls, v: str) -> str:
        """Validate recommendation is one of allowed values."""
        if v not in ("pass", "revise", "reject"):
            raise ValueError("recommendation must be 'pass', 'revise', or 'reject'")
        return v

    class Config:
        """Pydantic config."""

        str_strip_whitespace = True


# ============================================================================
# Tool 5: Save Generated Question
# ============================================================================


class Tool5Input(BaseModel):
    """Input contract for Tool 5: Save Generated Question."""

    item_type: str = Field(..., description="Type: multiple_choice, true_false, short_answer")
    stem: str = Field(..., description="Question text")
    choices: list[str] | None = Field(default=None, description="Answer choices (for multiple_choice/true_false)")
    correct_key: str | None = Field(default=None, description="Correct answer key (for multiple_choice/true_false)")
    correct_keywords: list[str] | None = Field(default=None, description="Correct keywords (for short_answer)")
    difficulty: int = Field(..., ge=1, le=10, description="Difficulty level")
    categories: list[str] = Field(..., min_items=1, description="Question categories (e.g., ['LLM', 'RAG'])")
    round_id: str = Field(..., description="Round ID from REQ-A-RoundID")
    validation_score: float | None = Field(default=None, ge=0.0, le=1.0, description="Score from Tool 4 validation")
    explanation: str | None = Field(default=None, description="Optional explanation for future use")

    class Config:
        """Pydantic config."""

        str_strip_whitespace = True


class Tool5Output(BaseModel):
    """Output contract for Tool 5: Save Generated Question."""

    question_id: str = Field(..., description="Unique question ID (UUID)")
    round_id: str = Field(..., description="Associated round ID")
    saved_at: str = Field(..., description="Timestamp when saved (ISO format)")
    success: bool = Field(..., description="Whether save was successful")

    class Config:
        """Pydantic config."""

        str_strip_whitespace = True


# ============================================================================
# Tool 6: Score & Generate Explanation
# ============================================================================


class Tool6Input(BaseModel):
    """Input contract for Tool 6: Score & Generate Explanation."""

    session_id: str = Field(..., description="Test session ID")
    user_id: str = Field(..., description="User ID")
    question_id: str = Field(..., description="Question ID")
    question_type: str = Field(..., description="Type: multiple_choice, true_false, short_answer")
    user_answer: str = Field(..., description="User's answer text")
    correct_answer: str = Field(..., description="Correct answer/key")
    correct_keywords: list[str] = Field(default_factory=list, description="Keywords for short_answer validation")
    difficulty: int = Field(..., ge=1, le=10, description="Question difficulty")
    category: str = Field(..., description="Question category")

    class Config:
        """Pydantic config."""

        str_strip_whitespace = True


class Tool6Output(BaseModel):
    """Output contract for Tool 6: Score & Generate Explanation."""

    attempt_id: str = Field(..., description="Unique attempt ID")
    session_id: str = Field(..., description="Test session ID")
    question_id: str = Field(..., description="Question ID")
    user_id: str = Field(..., description="User ID")
    is_correct: bool = Field(..., description="Whether answer is correct")
    score: float = Field(..., ge=0.0, le=100.0, description="Score (0-100)")
    explanation: str = Field(..., description="Answer explanation")
    keyword_matches: list[str] = Field(default_factory=list, description="Matched keywords (for short_answer)")
    feedback: str = Field(..., description="Feedback message for user")
    graded_at: str = Field(..., description="Timestamp when graded (ISO format)")

    class Config:
        """Pydantic config."""

        str_strip_whitespace = True


# ============================================================================
# Pipeline Output
# ============================================================================


class GeneratedQuestionOutput(BaseModel):
    """Represents a generated question in the pipeline output."""

    question_id: str = Field(..., description="Question ID from Tool 5")
    stem: str = Field(..., description="Question text")
    type: str = Field(..., description="Type: multiple_choice, true_false, short_answer")
    choices: list[str] | None = Field(default=None, description="Answer choices")
    correct_answer: str = Field(..., description="Correct answer/key")
    difficulty: int = Field(..., ge=1, le=10, description="Difficulty level")
    category: str = Field(..., description="Question category")
    round_id: str = Field(..., description="Associated round ID")
    validation_score: float = Field(..., ge=0.0, le=1.0, description="Validation score from Tool 4")
    saved_at: str = Field(..., description="Timestamp when saved (ISO format)")

    class Config:
        """Pydantic config."""

        str_strip_whitespace = True


class PipelineOutput(BaseModel):
    """
    Final output contract for the question generation pipeline.

    Aggregates results from all tools into a unified response.
    """

    questions: list[GeneratedQuestionOutput] = Field(
        default_factory=list, description="Successfully generated questions"
    )
    total_generated: int = Field(..., ge=0, description="Total questions attempted")
    total_valid: int = Field(..., ge=0, description="Questions with final_score >= 0.85")
    total_rejected: int = Field(..., ge=0, description="Questions with final_score < 0.70")

    class Config:
        """Pydantic config."""

        str_strip_whitespace = True


# ============================================================================
# Error Response Contract
# ============================================================================


class ErrorResponse(BaseModel):
    """Standard error response contract for all tools."""

    error: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Machine-readable error code")
    detail: str | None = Field(default=None, description="Additional error details")
    timestamp: str = Field(..., description="When error occurred (ISO format)")

    class Config:
        """Pydantic config."""

        str_strip_whitespace = True
