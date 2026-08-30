import os
import asyncio
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

async def verify_groq():
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("[ERROR] GROQ_API_KEY not found in environment!")
        return

    print(f"Checking Groq API with key: {api_key[:4]}...{api_key[-4:]}")
    
    client = AsyncOpenAI(
        api_key=api_key,
        base_url="https://api.groq.com/openai/v1"
    )

    try:
        model = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": "Hello, please confirm you can hear me. Output 'OK' and nothing else."}
            ],
            max_tokens=10
        )
        print("[SUCCESS] Groq API connection successful!")
        print(f"Response: {response.choices[0].message.content.strip()}")
    except Exception as e:
        print(f"[ERROR] Groq API call failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(verify_groq())
