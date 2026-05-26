import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from pydantic import SecretStr

load_dotenv()

groq_api_key = os.getenv("GROQ_API_KEY")

if not groq_api_key:
    raise ValueError("GROQ_API_KEY not available.")

groq_llm = ChatGroq(
    model="llama-3.3-70b-versatile", temperature=0.0, api_key=SecretStr(groq_api_key)
)
