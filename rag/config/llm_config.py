import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from pydantic import SecretStr

load_dotenv()


def _get_groq_llm() -> ChatGroq:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not available.")

    # Model id is env-overridable so a Groq deprecation is a config change, not a
    # code edit. Must support structured output (used by the ADR review feature).
    model = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
    return ChatGroq(
        model=model, temperature=0.0, api_key=SecretStr(api_key)
    )


groq_llm = _get_groq_llm()
