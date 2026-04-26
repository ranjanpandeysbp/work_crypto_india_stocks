import os
import google.genai as genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

print("--- Available Model Names ---")
try:
    for m in client.models.list():
        print(f"{m.name}")
except Exception as e:
    print(f"Error listing models: {e}")
