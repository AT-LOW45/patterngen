import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from pydantic import SecretStr

load_dotenv()


def _get_groq_llm() -> ChatGroq:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not available.")

    return ChatGroq(
        model="llama-3.3-70b-versatile", temperature=0.0, api_key=SecretStr(api_key)
    )


groq_llm = _get_groq_llm()
