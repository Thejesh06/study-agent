# backend/llm.py

from groq import Groq
from dotenv import load_dotenv
from typing import List
import os

load_dotenv()

GROQ_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_KEY:
    raise RuntimeError("GROQ_API_KEY is not set in .env")

client = Groq(api_key=GROQ_KEY)


def ask_groq(messages: List[dict]) -> str:
    """
    Send a list of messages (with roles) to Groq and return the reply.
    Supports multi-turn conversation history.
    messages format: [{"role": "system"|"user"|"assistant", "content": "..."}]
    """
    try:
        response = client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=messages,
            max_tokens=1024,
            temperature=0.4,
        )
        return response.choices[0].message.content
    except Exception as e:
        print("Groq error:", repr(e))
        return f"Error from Groq: {e}"
