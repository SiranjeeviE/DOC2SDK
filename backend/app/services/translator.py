import logging
import os
import json
import google.generativeai as genai
from openai import AsyncOpenAI
from typing import Any, Dict
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class TranslationService:
    def __init__(self):
        self.model = None
        self.groq_client = None
        self.groq_model = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")
        self._initialize_model()

    def _initialize_model(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key and api_key != "your_gemini_api_key_here":
            try:
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel("models/gemini-2.0-flash")
                return
            except Exception as e:
                logger.warning("Failed to initialize Gemini model for translation: %s", e)

        # Fallback to Groq
        groq_key = os.getenv("GROQ_API_KEY")
        if groq_key and groq_key != "your_groq_api_key_here":
            try:
                self.groq_client = AsyncOpenAI(
                    api_key=groq_key,
                    base_url="https://api.groq.com/openai/v1"
                )
                logger.info("Initialized Groq fallback for translation.")
            except Exception as e:
                logger.warning("Failed to initialize Groq for translation: %s", e)

    async def translate_response(self, data: Any) -> Any:
        """
        Translates all string values in a JSON-like object to English using AI.
        """
        if not self.model and not self.groq_client:
            return data

        if not data:
            return data

        prompt = f"""
        You are a translator. Translate all human-readable string values in the following JSON to English. 
        Keep the keys and structure EXACTLY the same. 
        Only translate values that are likely to be human-readable text (sentences, titles, names, etc.).
        Do not translate technical identifiers, IDs, or URLs.

        JSON Data:
        {json.dumps(data, indent=2)}
        """

        if self.model:
            try:
                response = await self.model.generate_content_async(
                    prompt,
                    generation_config={"response_mime_type": "application/json"},
                )
                return json.loads(response.text)
            except Exception as e:
                logger.warning("Translation failed (%s). Returning raw data.", e)
                return data
        else:
            try:
                response = await self.groq_client.chat.completions.create(
                    model=self.groq_model,
                    messages=[
                        {"role": "system", "content": "You are a translator. Return a STRICT JSON object matching the requested schema exactly. Do not add markdown formatting."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    response_format={"type": "json_object"}
                )
                raw_text = response.choices[0].message.content
                if "```json" in raw_text:
                    raw_text = raw_text.replace("```json", "").replace("```", "")
                elif "```" in raw_text:
                     raw_text = raw_text.replace("```", "")
                return json.loads(raw_text.strip())
            except Exception as e:
                logger.warning("Groq Translation failed (%s). Returning raw data.", e)
                return data
