"""
ReAct Prompt Builder - Follows Builder Pattern for flexible prompt construction.

SOLID Principles Applied:
- Single Responsibility: PromptBuilder handles ONLY template construction logic
- Open/Closed: Easy to extend with new prompt variations
- Liskov Substitution: All builders implement same interface
- Interface Segregation: Clients depend only on build() method
- Dependency Inversion: Depends on content interface, not implementation

Benefits over inline templates:
✅ Content and logic are completely separated
✅ No need to escape JSON or special characters in content
✅ Easy to test (mock content, test template logic)
✅ Easy to modify (change content without touching template logic)
✅ Reusable across different prompt templates
"""

from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
)

from src.agent.prompts.prompt_content import (
    get_react_system_prompt,
    get_simple_system_prompt,
)


class PromptBuilder:
    """
    Base class for prompt builders.

    SOLID: Defines interface that all prompt builders follow.
    """

    def build(self) -> ChatPromptTemplate:
        """
        Build the prompt template.

        Returns:
            ChatPromptTemplate: Configured prompt template.

        """
        raise NotImplementedError("Subclasses must implement build()")


class ReactPromptBuilder(PromptBuilder):
    """
    Builder for ReAct (Reasoning + Acting) prompt template.

    Features:
    - Comprehensive format rules for tool calling
    - Explicit JSON examples (no escaping needed!)
    - Tool selection strategy
    - Response format rules
    - User proficiency level guidance
    - Quality requirements

    Design Pattern: Builder Pattern
    - Separates prompt content from template construction
    - Allows future customization (add/remove rules dynamically)

    SOLID Principle (Dependency Inversion):
    - Uses LangChain's SystemMessage directly instead of from_template()
    - This avoids ChatPromptTemplate.from_template() which interprets {} as variables
    - JSON in content is preserved as-is without escaping
    """

    def build(self) -> ChatPromptTemplate:
        """
        Build ReAct prompt template.

        Process:
        1. Get complete system prompt from content module (content is pure text)
        2. Create SystemMessage directly (not from_template) to avoid {} interpretation
        3. Add MessagesPlaceholder for chat history
        4. Return composed ChatPromptTemplate

        Key insight: Using SystemMessage directly instead of from_template()
        prevents JSON braces from being interpreted as template variables.

        Returns:
            ChatPromptTemplate: ReAct prompt template with only 'messages' variable

        """
        from langchain_core.messages import SystemMessage

        # Step 1: Get content (pure text, no escaping needed!)
        system_prompt = get_react_system_prompt()

        # Step 2: Create SystemMessage directly (NOT from_template)
        # This prevents {} in JSON from being interpreted as template variables
        system_message = SystemMessage(content=system_prompt)

        # Step 3: Create template with direct messages
        return ChatPromptTemplate.from_messages(
            [
                system_message,
                MessagesPlaceholder(variable_name="messages"),
            ]
        )


class SimpleReactPromptBuilder(PromptBuilder):
    """
    Builder for simple ReAct prompt (MVP version).

    Use when:
    - Minimal token usage is critical
    - Simple task doesn't need detailed rules
    - Want to test with minimal prompt overhead
    """

    def build(self) -> ChatPromptTemplate:
        """
        Build simple ReAct prompt template.

        Uses SystemMessage directly (same as ReactPromptBuilder)
        to avoid template variable interpretation issues.

        Returns:
            ChatPromptTemplate: Simple ReAct prompt template

        """
        from langchain_core.messages import SystemMessage

        system_prompt = get_simple_system_prompt()

        # Use SystemMessage directly to avoid {} interpretation
        system_message = SystemMessage(content=system_prompt)

        return ChatPromptTemplate.from_messages(
            [
                system_message,
                MessagesPlaceholder(variable_name="messages"),
            ]
        )


class PromptFactory:
    """
    Factory for creating prompt builders.

    SOLID: Factory Pattern + Dependency Inversion
    - Clients depend on factory, not concrete builders
    - Easy to add new prompt types
    - Centralizes prompt creation logic

    Usage:
        >>> builder = PromptFactory.get_builder("react")
        >>> prompt = builder.build()
    """

    _builders = {
        "react": ReactPromptBuilder,
        "simple": SimpleReactPromptBuilder,
    }

    @staticmethod
    def get_builder(builder_type: str = "react") -> PromptBuilder:
        """
        Get prompt builder by type.

        Args:
            builder_type: Type of builder ("react" or "simple")

        Returns:
            PromptBuilder: Appropriate prompt builder instance

        Raises:
            ValueError: If builder_type is not recognized

        """
        if builder_type not in PromptFactory._builders:
            raise ValueError(f"Unknown builder type: {builder_type}. Available: {list(PromptFactory._builders.keys())}")

        builder_class = PromptFactory._builders[builder_type]
        return builder_class()

    @staticmethod
    def register_builder(builder_type: str, builder_class: type[PromptBuilder]) -> None:
        """
        Register new prompt builder.

        Allows extending with custom builders without modifying factory.

        Args:
            builder_type: Name of the builder type
            builder_class: Builder class (must extend PromptBuilder)

        """
        if not issubclass(builder_class, PromptBuilder):
            raise TypeError(f"{builder_class} must extend PromptBuilder")

        PromptFactory._builders[builder_type] = builder_class
