# backend/llm.py
from groq import Groq
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

GROQ_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_KEY:
    # This will show clearly in the server logs if key is missing
    raise RuntimeError("GROQ_API_KEY is not set in .env")

# Create Groq client
client = Groq(api_key=GROQ_KEY)

def ask_groq(prompt: str) -> str:
    """
    Send a simple prompt to Groq and return the model's response text.
    """
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=256,
            temperature=0.7
        )

        # For Groq, use .content, not ["content"]
        return response.choices[0].message.content

    except Exception as e:
        # Print to server logs for debugging
        print("Groq error:", repr(e))
        # Return a safe error string instead of crashing
        return f"Error from Groq: {e}"
