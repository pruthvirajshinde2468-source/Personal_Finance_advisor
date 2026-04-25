import os
from dotenv import load_dotenv
load_dotenv()
import ai

print("API Key:", os.getenv("GEMINI_API_KEY"))
print("Testing parse_intent...")
res = ai.parse_intent("Hello")
print("Result:", res)
