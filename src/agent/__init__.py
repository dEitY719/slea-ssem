"""
Item-Gen-Agent: LangChain ReAct 기반 자율 AI 에이전트.

REQ: REQ-A-ItemGen, REQ-A-Mode1-*, REQ-A-Mode2-*
"""

# Lazy imports to avoid langgraph dependency issues during testing
def __getattr__(name: str):
    """Lazy load agent components on demand."""
    if name == "ItemGenAgent":
        from src.agent.llm_agent import ItemGenAgent
        return ItemGenAgent
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["ItemGenAgent"]
