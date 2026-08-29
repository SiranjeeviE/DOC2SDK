import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("GEMINI_API_KEY not set")
else:
    print(f"Key configured: {api_key[:4]}...{api_key[-4:]}")

try:
    genai.configure(api_key=api_key)
    models = [m.name for m in genai.list_models() if "gemini" in m.name]
    print(f"Models: {models}")
except Exception as e:
    print(f"Error: {str(e)}")
