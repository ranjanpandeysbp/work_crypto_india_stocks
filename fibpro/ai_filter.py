import os
from groq import Groq
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

if os.getenv("GROQ_API_KEY"):
    api_key = os.getenv("GROQ_API_KEY")
    model_name = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    client = Groq(api_key=api_key)
elif os.getenv("GEMINI_API_KEY"):
    api_key = os.getenv("GEMINI_API_KEY")
    print(f"Using Gemini API Key. GEMINI_API_KEY: {os.getenv('GEMINI_API_KEY', 'GEMINI_API_KEY')}")
    print(f"Using Gemini API Key. MODEL_NAME: {os.getenv('MODEL_NAME', 'gemini-2.0-flash')}")
    model_name = os.getenv("MODEL_NAME", "gemini-2.0-flash")
    client = genai.Client()
else:
    raise ValueError("Either GROQ_API_KEY or GEMINI_API_KEY must be set in the environment variables")

model_name = model_name

def analyze_trade(symbol, trade):

    prompt = f"""
    You are a professional trader.

    Analyze this:

    Symbol: {symbol}
    Trade: {trade}

    Output EXACT format:

    Score: <0-100>
    Confidence: <Low/Medium/High>
    Decision: <BUY/AVOID>
    Reason: <2 lines max>
    """

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model=model_name,
        )
        text = chat_completion.choices[0].message.content

        score_line = [line for line in text.split("\n") if "Score" in line]

        if score_line:
            score = int(''.join(filter(str.isdigit, score_line[0])))
        else:
            score = 0

        return {
            "raw": text,
            "ai_score": score
        }

    except Exception as e:
        return {
            "raw": f"AI Error: {str(e)}",
            "ai_score": 0
        }