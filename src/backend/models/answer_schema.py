"""
AnswerSchemaTransformer pattern for normalizing diverse answer_schema formats.

REQ: REQ-REFACTOR-SOLID-1, REQ-REFACTOR-SOLID-2
Implementation: Transformer Pattern + Factory Pattern + Value Object

This module provides a SOLID-based approach to handling multiple answer_schema
formats from different sources (LLM Agent, Mock data, etc.) without modifying
existing code when new formats are added.

SOLID Principles:
- Single Responsibility: Each transformer handles one format
- Open/Closed: New formats extend abstract class, existing code unchanged
- Liskov Substitution: All transformers implement same interface
- Interface Segregation: Factory provides minimal interface
- Dependency Inversion: Depends on abstract interface, not concrete classes

Classes:
- AnswerSchemaTransformer: Abstract base class defining interface
- AgentResponseTransformer: Converts Agent LLM format to standard
- MockDataTransformer: Converts Mock test data format to standard
- TransformerFactory: Creates appropriate transformer by format type
- AnswerSchema: Immutable Value Object for standardized answer schema
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any

# ============================================================================
# CUSTOM EXCEPTIONS
# ============================================================================


class TransformerError(Exception):
    """Base exception for transformer operations."""

    pass


class UnknownFormatError(TransformerError):
    """Raised when format type is not recognized."""

    pass


class ValidationError(TransformerError):
    """Raised when validation of input data fails."""

    pass


# ============================================================================
# ABSTRACT BASE CLASS
# ============================================================================


class AnswerSchemaTransformer(ABC):
    """
    Abstract base class for answer_schema transformers.

    Defines the interface that all concrete transformers must implement.
    Each transformer is responsible for converting a specific input format
    into a standardized answer_schema dict.

    Concrete implementations:
    - AgentResponseTransformer: Handles Agent LLM response format
    - MockDataTransformer: Handles Mock test data format

    Example:
        >>> transformer = AgentResponseTransformer()
        >>> raw_data = {
        ...     "correct_keywords": ["battery", "lithium"],
        ...     "explanation": "Lithium-ion batteries..."
        ... }
        >>> result = transformer.transform(raw_data)
        >>> result["type"]
        'keyword_match'
        >>> result["keywords"]
        ['battery', 'lithium']

    """

    @abstractmethod
    def transform(self, raw_data: dict[str, Any]) -> dict[str, Any]:
        """
        Transform raw answer_schema data to standard format.

        This method must be implemented by concrete subclasses to handle
        their specific format's transformation logic.

        Args:
            raw_data: Raw answer_schema dictionary from specific source format

        Returns:
            Normalized answer_schema dictionary with standard fields:
            - type: str (e.g., "keyword_match", "exact_match")
            - keywords: list[str] | None (for keyword-based questions)
            - correct_answer: str | None (for exact match questions)
            - explanation: str (explanation of correct answer)

        Raises:
            ValidationError: If required fields are missing or invalid
            TypeError: If data types don't match expectations

        """
        pass


# ============================================================================
# CONCRETE TRANSFORMER 1: AGENT RESPONSE FORMAT
# ============================================================================


class AgentResponseTransformer(AnswerSchemaTransformer):
    """
    Transformer for Agent LLM response format.

    Converts Agent responses with 'correct_keywords' field to standard format
    with 'keywords' field.

    Input Format (from LLM Agent):
        {
            "correct_keywords": ["keyword1", "keyword2"],
            "explanation": "Explanation text"
        }

    Output Format (normalized):
        {
            "type": "keyword_match",
            "keywords": ["keyword1", "keyword2"],
            "explanation": "Explanation text",
            "source_format": "agent_response"
        }

    Transformation Rules:
    - correct_keywords → keywords (rename and validate as list)
    - explanation → explanation (validate non-empty string)
    - Infer type as "keyword_match" (questions with keywords use keyword matching)
    - Add source_format metadata

    Error Handling:
    - Missing correct_keywords → ValidationError
    - Missing explanation → ValidationError
    - Empty keywords list → ValidationError (agent response should have keywords)
    - keywords not a list → TypeError
    - Non-string keywords → TypeError
    - Empty/None explanation → ValidationError
    """

    def transform(self, raw_data: dict[str, Any]) -> dict[str, Any]:
        """
        Transform Agent response format to standard format.

        Args:
            raw_data: Agent response dictionary with 'correct_keywords' and 'explanation'

        Returns:
            Normalized dictionary with 'keywords', 'explanation', 'type', 'source_format'

        Raises:
            ValidationError: If required fields missing or invalid
            TypeError: If data types don't match expectations

        """
        # Validate input is a dict
        if not isinstance(raw_data, dict):
            raise TypeError(f"raw_data must be dict, got {type(raw_data).__name__}")

        # Step 1: Extract and validate correct_keywords
        if "correct_keywords" not in raw_data:
            raise ValidationError(
                "Missing required field 'correct_keywords' in agent response format. "
                "Expected: {'correct_keywords': [...], 'explanation': '...'}"
            )

        correct_keywords = raw_data.get("correct_keywords")

        # Validate correct_keywords is a list
        if not isinstance(correct_keywords, list):
            raise TypeError(
                f"Field 'correct_keywords' must be list, got {type(correct_keywords).__name__}. "
                f"Value: {correct_keywords}"
            )

        # Validate list is not empty
        if len(correct_keywords) == 0:
            raise ValidationError(
                "Field 'correct_keywords' cannot be empty. Agent response must provide at least one keyword."
            )

        # Validate all items in list are strings
        for i, keyword in enumerate(correct_keywords):
            if not isinstance(keyword, str):
                raise TypeError(
                    f"All items in 'correct_keywords' must be strings. Item {i} is {type(keyword).__name__}: {keyword}"
                )

        # Step 2: Extract and validate explanation
        if "explanation" not in raw_data:
            raise ValidationError(
                "Missing required field 'explanation' in agent response format. Explanation is mandatory."
            )

        explanation = raw_data.get("explanation")

        # Validate explanation is a string
        if not isinstance(explanation, str):
            raise TypeError(f"Field 'explanation' must be string, got {type(explanation).__name__}")

        # Validate explanation is not empty
        if len(explanation.strip()) == 0:
            raise ValidationError(
                "Field 'explanation' cannot be empty or whitespace-only. Provide a meaningful explanation."
            )

        # Step 3: Build and return normalized dict
        return {
            "type": "keyword_match",
            "keywords": correct_keywords,
            "explanation": explanation,
            "source_format": "agent_response",
        }


# ============================================================================
# CONCRETE TRANSFORMER 2: MOCK DATA FORMAT
# ============================================================================


class MockDataTransformer(AnswerSchemaTransformer):
    """
    Transformer for Mock test data format.

    Converts Mock data with 'correct_key' field to standard format with
    'correct_answer' field.

    Input Format (from Mock data):
        {
            "correct_key": "B",
            "explanation": "Explanation text"
        }

    Output Format (normalized):
        {
            "type": "exact_match",
            "correct_answer": "B",
            "explanation": "Explanation text",
            "source_format": "mock_data"
        }

    Transformation Rules:
    - correct_key → correct_answer (rename and validate as string)
    - explanation → explanation (validate non-empty string)
    - Infer type as "exact_match" (mock uses exact answer matching)
    - Add source_format metadata

    Error Handling:
    - Missing correct_key → ValidationError
    - Missing explanation → ValidationError
    - Empty/None correct_key → ValidationError
    - correct_key not a string → TypeError
    - Empty/None explanation → ValidationError
    """

    def transform(self, raw_data: dict[str, Any]) -> dict[str, Any]:
        """
        Transform Mock data format to standard format.

        Args:
            raw_data: Mock data dictionary with 'correct_key' and 'explanation'

        Returns:
            Normalized dictionary with 'correct_answer', 'explanation', 'type', 'source_format'

        Raises:
            ValidationError: If required fields missing or invalid
            TypeError: If data types don't match expectations

        """
        # Validate input is a dict
        if not isinstance(raw_data, dict):
            raise TypeError(f"raw_data must be dict, got {type(raw_data).__name__}")

        # Validate dict is not empty
        if len(raw_data) == 0:
            raise ValidationError("Input dictionary is empty. Expected: {'correct_key': '...', 'explanation': '...'}")

        # Step 1: Extract and validate correct_key
        if "correct_key" not in raw_data:
            raise ValidationError(
                "Missing required field 'correct_key' in mock data format. "
                "Expected: {'correct_key': '...', 'explanation': '...'}"
            )

        correct_key = raw_data.get("correct_key")

        # Validate correct_key is a string
        if not isinstance(correct_key, str):
            raise TypeError(
                f"Field 'correct_key' must be string, got {type(correct_key).__name__}. Value: {correct_key}"
            )

        # Validate correct_key is not empty
        if len(correct_key.strip()) == 0:
            raise ValidationError("Field 'correct_key' cannot be empty or whitespace-only. Provide a valid answer key.")

        # Step 2: Extract and validate explanation
        if "explanation" not in raw_data:
            raise ValidationError("Missing required field 'explanation' in mock data format. Explanation is mandatory.")

        explanation = raw_data.get("explanation")

        # Validate explanation is a string
        if not isinstance(explanation, str):
            raise TypeError(f"Field 'explanation' must be string, got {type(explanation).__name__}")

        # Validate explanation is not empty
        if len(explanation.strip()) == 0:
            raise ValidationError(
                "Field 'explanation' cannot be empty or whitespace-only. Provide a meaningful explanation."
            )

        # Step 3: Build and return normalized dict
        return {
            "type": "exact_match",
            "correct_answer": correct_key,
            "explanation": explanation,
            "source_format": "mock_data",
        }


# ============================================================================
# FACTORY PATTERN
# ============================================================================


class TransformerFactory:
    """
    Factory for creating appropriate AnswerSchemaTransformer instances.

    This factory implements the Factory Pattern to encapsulate transformer
    creation logic. It maps format types to their corresponding transformer
    classes, allowing new formats to be added without modifying existing code
    (Open/Closed principle).

    Supported formats:
    - "agent_response": AgentResponseTransformer (for LLM Agent outputs)
    - "mock_data": MockDataTransformer (for test mock data)

    Usage:
        >>> factory = TransformerFactory()
        >>> transformer = factory.get_transformer("agent_response")
        >>> result = transformer.transform(raw_data)

    Adding new formats:
        1. Create new transformer class extending AnswerSchemaTransformer
        2. Add format_type mapping in _get_transformer_class()
        3. No changes needed to existing code (Open/Closed principle)
    """

    # Mapping of format types to transformer classes
    _TRANSFORMERS: dict[str, type[AnswerSchemaTransformer]] = {
        "agent_response": AgentResponseTransformer,
        "mock_data": MockDataTransformer,
    }

    def get_transformer(self, format_type: str) -> AnswerSchemaTransformer:
        """
        Get transformer instance for specified format type.

        Args:
            format_type: Format identifier string (e.g., "agent_response", "mock_data")

        Returns:
            New instance of appropriate transformer class

        Raises:
            UnknownFormatError: If format_type is not recognized

        Example:
            >>> factory = TransformerFactory()
            >>> transformer = factory.get_transformer("agent_response")
            >>> isinstance(transformer, AgentResponseTransformer)
            True

        """
        # Normalize format_type (lowercase, strip whitespace)
        normalized_format = format_type.lower().strip()

        # Check if format type is registered
        if normalized_format not in self._TRANSFORMERS:
            available_formats = ", ".join(self._TRANSFORMERS.keys())
            raise UnknownFormatError(f"Unknown format type '{format_type}'. Supported formats: {available_formats}")

        # Get transformer class and instantiate
        transformer_class = self._TRANSFORMERS[normalized_format]
        return transformer_class()

    @classmethod
    def register_transformer(cls, format_type: str, transformer_class: type[AnswerSchemaTransformer]) -> None:
        """
        Register a new transformer class for a format type (extension point).

        This class method allows registering new transformer implementations
        at runtime, enabling the system to support additional formats without
        modifying the factory code.

        Args:
            format_type: Format identifier string to register
            transformer_class: Class that extends AnswerSchemaTransformer

        Raises:
            TypeError: If transformer_class doesn't extend AnswerSchemaTransformer
            ValueError: If format_type is already registered

        Example:
            >>> class CustomTransformer(AnswerSchemaTransformer):
            ...     def transform(self, raw_data):
            ...         return {"type": "custom", ...}
            >>> factory = TransformerFactory()
            >>> factory.register_transformer("custom", CustomTransformer)
            >>> transformer = factory.get_transformer("custom")

        """
        # Validate transformer class extends AnswerSchemaTransformer
        if not issubclass(transformer_class, AnswerSchemaTransformer):
            raise TypeError(f"transformer_class must extend AnswerSchemaTransformer, got {transformer_class.__name__}")

        # Normalize format type
        normalized_format = format_type.lower().strip()

        # Check if already registered
        if normalized_format in cls._TRANSFORMERS:
            raise ValueError(
                f"Format type '{format_type}' is already registered. Use a different name or unregister first."
            )

        # Register new transformer
        cls._TRANSFORMERS[normalized_format] = transformer_class


# ============================================================================
# VALUE OBJECT: ANSWERSCHEMA
# ============================================================================


@dataclass(frozen=True)
class AnswerSchema:
    """
    Immutable Value Object representing a standardized answer schema.

    REQ: REQ-REFACTOR-SOLID-2

    This frozen dataclass enforces immutability and provides factory methods
    to create instances from different source formats (Agent LLM, Mock data, etc).

    An AnswerSchema instance guarantees:
    - Immutability: frozen=True prevents post-creation modifications
    - Type Safety: All fields are strictly typed (mypy strict compatible)
    - Validation: __post_init__() validates field constraints
    - Consistency: Always has either keywords or correct_answer (not both None)

    Fields:
        type: Question answer type (keyword_match, exact_match, multiple_choice, etc)
        keywords: List of acceptable keywords for short_answer questions (optional)
        correct_answer: Single correct answer for multiple_choice/true_false (optional)
        explanation: Explanation of why this is the correct answer (required)
        source_format: Source format identifier (agent_response, mock_data, unknown)
        created_at: Timestamp when schema was created (auto-set to now)

    Factory Methods (recommended usage):
        - from_agent_response(data: dict) → AnswerSchema
          Creates from Agent LLM response format (correct_keywords field)
        - from_mock_data(data: dict) → AnswerSchema
          Creates from Mock test data format (correct_key field)
        - from_dict(data: dict, source: str = "unknown") → AnswerSchema
          Generic creation from dict with source format metadata

    Conversion Methods:
        - to_db_dict() → dict
          Converts to database-compatible dict (includes created_at, source_format)
        - to_response_dict() → dict
          Converts to API response dict (excludes internal metadata like created_at)

    Value Object Pattern:
        - __eq__(): Compares instances by value (all fields)
        - __hash__(): Consistent hashing for use in sets/dicts

    Example:
        >>> # Create from Agent response
        >>> schema = AnswerSchema.from_agent_response({
        ...     "correct_keywords": ["battery", "lithium"],
        ...     "explanation": "Lithium batteries store energy..."
        ... })
        >>> schema.keywords
        ['battery', 'lithium']

        >>> # Create from Mock data
        >>> schema = AnswerSchema.from_mock_data({
        ...     "correct_key": "B",
        ...     "explanation": "Option B is correct because..."
        ... })
        >>> schema.correct_answer
        'B'

        >>> # Convert for database storage
        >>> db_dict = schema.to_db_dict()
        >>> # {'keywords': [...], 'explanation': '...', 'source_format': '...', 'created_at': ...}

        >>> # Convert for API response
        >>> api_dict = schema.to_response_dict()
        >>> # {'keywords': [...], 'explanation': '...', 'type': '...'}

    Error Handling:
        - Both keywords and correct_answer None → ValidationError
        - Empty/whitespace-only explanation → ValidationError
        - Missing required fields → ValidationError
        - Type mismatches → TypeError

    """

    type: str
    keywords: list[str] | None = None
    correct_answer: str | None = None
    explanation: str = ""
    source_format: str = "unknown"
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        """
        Validate AnswerSchema fields after initialization.

        Enforces:
        1. type is non-empty string
        2. keywords is list if present
        3. correct_answer is string if present
        4. explanation is non-empty string
        5. At least one of keywords or correct_answer is present
        6. source_format is non-empty string

        Raises:
            ValidationError: If any validation constraint is violated
            TypeError: If field types don't match expectations

        """
        # Validate type field
        if not isinstance(self.type, str):
            raise TypeError(f"Field 'type' must be str, got {type(self.type).__name__}")
        if len(self.type.strip()) == 0:
            raise ValidationError("Field 'type' cannot be empty")

        # Validate keywords field if present
        if self.keywords is not None:
            if not isinstance(self.keywords, list):
                raise TypeError(f"Field 'keywords' must be list or None, got {type(self.keywords).__name__}")
            for i, keyword in enumerate(self.keywords):
                if not isinstance(keyword, str):
                    raise TypeError(f"All items in 'keywords' must be strings. Item {i} is {type(keyword).__name__}")

        # Validate correct_answer field if present
        if self.correct_answer is not None:
            if not isinstance(self.correct_answer, str):
                raise TypeError(f"Field 'correct_answer' must be str or None, got {type(self.correct_answer).__name__}")

        # Validate explanation field
        if not isinstance(self.explanation, str):
            raise TypeError(f"Field 'explanation' must be str, got {type(self.explanation).__name__}")
        if len(self.explanation.strip()) == 0:
            raise ValidationError("Field 'explanation' cannot be empty or whitespace-only")

        # Validate at least one of keywords or correct_answer is present
        if self.keywords is None and self.correct_answer is None:
            raise ValidationError("AnswerSchema must have either 'keywords' or 'correct_answer' (not both None)")

        # Validate source_format field
        if not isinstance(self.source_format, str):
            raise TypeError(f"Field 'source_format' must be str, got {type(self.source_format).__name__}")

        # Set created_at to now if not provided
        if self.created_at is None:
            object.__setattr__(self, "created_at", datetime.now())

    def __hash__(self) -> int:
        """
        Compute hash for AnswerSchema Value Object.

        Converts mutable keywords list to immutable tuple for hashing.
        This allows AnswerSchema instances to be used in sets and as dict keys.

        Returns:
            Hash value based on all fields (keywords converted to tuple)

        """
        keywords_tuple = tuple(self.keywords) if self.keywords is not None else None
        return hash(
            (
                self.type,
                keywords_tuple,
                self.correct_answer,
                self.explanation,
                self.source_format,
                self.created_at,
            )
        )

    @classmethod
    def from_agent_response(cls, data: dict[str, Any]) -> "AnswerSchema":
        """
        Create AnswerSchema from Agent LLM response format.

        This factory method transforms Agent response format (with correct_keywords)
        into a standardized AnswerSchema using AgentResponseTransformer.

        Input Format:
            {
                "correct_keywords": ["keyword1", "keyword2"],
                "explanation": "Explanation text"
            }

        Args:
            data: Agent response dictionary with correct_keywords and explanation

        Returns:
            AnswerSchema instance with keywords from correct_keywords

        Raises:
            ValidationError: If required fields missing or invalid
            TypeError: If data types don't match expectations

        Example:
            >>> schema = AnswerSchema.from_agent_response({
            ...     "correct_keywords": ["battery"],
            ...     "explanation": "Batteries..."
            ... })
            >>> schema.keywords
            ['battery']

        """
        transformer = AgentResponseTransformer()
        transformed = transformer.transform(data)
        return cls(
            type=transformed["type"],
            keywords=transformed.get("keywords"),
            correct_answer=transformed.get("correct_answer"),
            explanation=transformed.get("explanation", ""),
            source_format=transformed.get("source_format", "agent_response"),
        )

    @classmethod
    def from_mock_data(cls, data: dict[str, Any]) -> "AnswerSchema":
        """
        Create AnswerSchema from Mock test data format.

        This factory method transforms Mock data format (with correct_key)
        into a standardized AnswerSchema using MockDataTransformer.

        Input Format:
            {
                "correct_key": "B",
                "explanation": "Explanation text"
            }

        Args:
            data: Mock data dictionary with correct_key and explanation

        Returns:
            AnswerSchema instance with correct_answer from correct_key

        Raises:
            ValidationError: If required fields missing or invalid
            TypeError: If data types don't match expectations

        Example:
            >>> schema = AnswerSchema.from_mock_data({
            ...     "correct_key": "B",
            ...     "explanation": "This is correct..."
            ... })
            >>> schema.correct_answer
            'B'

        """
        transformer = MockDataTransformer()
        transformed = transformer.transform(data)
        return cls(
            type=transformed["type"],
            keywords=transformed.get("keywords"),
            correct_answer=transformed.get("correct_answer"),
            explanation=transformed.get("explanation", ""),
            source_format=transformed.get("source_format", "mock_data"),
        )

    @classmethod
    def from_dict(cls, data: dict[str, Any], source: str = "unknown") -> "AnswerSchema":
        """
        Create AnswerSchema from generic dict with optional format detection.

        This factory method provides flexibility for creating AnswerSchema from
        pre-transformed dicts or when format is already known. It auto-detects
        the source format if not explicitly provided.

        Args:
            data: Dictionary with answer schema fields
            source: Format source identifier ("agent_response", "mock_data", etc)
                   If "auto", detects format from data presence (correct_keywords or correct_key)

        Returns:
            AnswerSchema instance

        Raises:
            ValidationError: If required fields missing or invalid

        Example:
            >>> # With explicit source
            >>> schema = AnswerSchema.from_dict(
            ...     {"keywords": ["answer"], "explanation": "..."},
            ...     source="custom_format"
            ... )

            >>> # With auto-detection
            >>> schema = AnswerSchema.from_dict(
            ...     {"correct_keywords": [...], "explanation": "..."}
            ... )  # Detects as agent_response format

        """
        # Auto-detect source format if not provided
        detected_source = source
        if source == "unknown" or source == "auto":
            if "correct_keywords" in data:
                # Delegate to from_agent_response for proper transformation
                return cls.from_agent_response(data)
            elif "correct_key" in data:
                # Delegate to from_mock_data for proper transformation
                return cls.from_mock_data(data)

        # For already-transformed dicts or unknown format, extract fields directly
        return cls(
            type=data.get("type", "keyword_match"),
            keywords=data.get("keywords"),
            correct_answer=data.get("correct_answer"),
            explanation=data.get("explanation", ""),
            source_format=detected_source,
        )

    def to_db_dict(self) -> dict[str, Any]:
        """
        Convert AnswerSchema to database-compatible dictionary.

        This conversion includes all fields necessary for persistent storage,
        including metadata fields like created_at and source_format.

        Returns:
            Dictionary with all fields suitable for database INSERT/UPDATE:
            {
                "type": str,
                "keywords": list[str] | None,
                "correct_answer": str | None,
                "explanation": str,
                "source_format": str,
                "created_at": datetime
            }

        Example:
            >>> schema = AnswerSchema.from_agent_response({...})
            >>> db_dict = schema.to_db_dict()
            >>> session.query(TestQuestion).update({"answer_schema": db_dict})

        """
        return {
            "type": self.type,
            "keywords": self.keywords,
            "correct_answer": self.correct_answer,
            "explanation": self.explanation,
            "source_format": self.source_format,
            "created_at": self.created_at,
        }

    def to_response_dict(self) -> dict[str, Any]:
        """
        Convert AnswerSchema to API response-compatible dictionary.

        This conversion excludes internal metadata fields (created_at, source_format)
        that are implementation details, returning only the information relevant
        to API clients.

        Returns:
            Dictionary suitable for API responses:
            {
                "type": str,
                "keywords": list[str] | None,
                "correct_answer": str | None,
                "explanation": str
            }

        Example:
            >>> schema = AnswerSchema.from_agent_response({...})
            >>> api_dict = schema.to_response_dict()
            >>> return {"answer_schema": api_dict}

        """
        return {
            "type": self.type,
            "keywords": self.keywords,
            "correct_answer": self.correct_answer,
            "explanation": self.explanation,
        }
