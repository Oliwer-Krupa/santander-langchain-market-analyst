from langchain_openai import ChatOpenAI

from app.config import Settings


def get_llm(settings: Settings) -> ChatOpenAI:
    """Create a ChatOpenAI instance with deterministic settings for stable analysis."""
    return ChatOpenAI(
        model=settings.OPENAI_MODEL,
        temperature=0.2,
        api_key=settings.OPENAI_API_KEY,
    )
