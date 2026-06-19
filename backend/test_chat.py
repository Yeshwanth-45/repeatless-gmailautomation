import os
from dotenv import load_dotenv

load_dotenv()

from services.gemini_service import _try_gemini, _nvidia_generate

prompt = "Hello, please answer yes or no."

print("Testing Gemini...")
try:
    import google.generativeai as genai
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model = genai.GenerativeModel("gemini-2.0-flash-lite")
    response = model.generate_content(prompt)
    print("Gemini response:", response.text)
except Exception as e:
    print("Gemini error:", repr(e))

print("\nTesting NVIDIA...")
try:
    res = _nvidia_generate(prompt)
    print("NVIDIA response:", res)
except Exception as e:
    print("NVIDIA error:", repr(e))
