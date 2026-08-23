import logging
import os
import json
import google.generativeai as genai
from openai import AsyncOpenAI
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class LLMParserService:
    def __init__(self):
        self.model = None
        self.model_name = None
        self.groq_client = None
        self.groq_model = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")
        self._initialize_model()

    def _initialize_model(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key and api_key != "your_gemini_api_key_here":
            try:
                genai.configure(api_key=api_key)
                # Find the best available gemini model
                models = [m.name for m in genai.list_models() if "gemini" in m.name]
                
                # Preference order
                preferred = ["models/gemini-2.0-flash", "models/gemini-1.5-flash", "models/gemini-1.5-pro", "models/gemini-pro"]
                for p in preferred:
                    if p in models:
                        self.model_name = p
                        break
                
                if not self.model_name and models:
                    self.model_name = models[0]
                    
                if self.model_name:
                    self.model = genai.GenerativeModel(self.model_name)
                    logger.info("Initialized with model: %s", self.model_name)
                    return
            except Exception as e:
                logger.warning("Failed to initialize Gemini model: %s", e)
                self.model = None

        # Fallback to Groq
        groq_key = os.getenv("GROQ_API_KEY")
        if groq_key and groq_key != "your_groq_api_key_here":
            try:
                self.groq_client = AsyncOpenAI(
                    api_key=groq_key,
                    base_url="https://api.groq.com/openai/v1"
                )
                logger.info("Initialized fallback to Groq with model: %s", self.groq_model)
            except Exception as e:
                logger.warning("Failed to initialize Groq client: %s", e)
                self.groq_client = None

    async def parse_docs(self, cleaned_text: str) -> Dict[str, Any]:
        if not self.model and not self.groq_client:
            self._initialize_model()

        # 1. Spec-First Bypass: If scraper found a raw JSON spec, parse it directly
        if "RAW_SPEC_JSON:" in cleaned_text:
            try:
                raw_content = cleaned_text.replace("RAW_SPEC_JSON:", "", 1).strip()
                
                # Attempt to parse as OpenAPI (JSON or YAML)
                from ..parsers.openapi import OpenAPIParser
                parser = OpenAPIParser()
                try:
                    normalized = parser.parse(raw_content)
                    res = normalized.model_dump() if hasattr(normalized, "model_dump") else normalized.dict()
                    res["source"] = "direct_extraction_openapi"
                    res["is_mock"] = False
                    return res
                except Exception as parse_err:
                    logger.debug("OpenAPIParser failed on RAW_SPEC_JSON: %s", parse_err)
                    
                    # Fallback to basic JSON extraction if it was just a custom JSON
                    try:
                        spec = json.loads(raw_content)
                        res = {
                            "name": spec.get("info", {}).get("title", spec.get("name", "Extracted API")),
                            "version": spec.get("info", {}).get("version", spec.get("version", "1.0.0")),
                            "base_url": spec.get("servers", [{"url": ""}])[0].get("url", spec.get("base_url", "")),
                            "description": spec.get("info", {}).get("description", spec.get("description", "")),
                            "authentication": spec.get("authentication", {"type": "none"}),
                            "endpoints": spec.get("endpoints", []),
                            "source": "direct_extraction",
                            "is_mock": False
                        }
                        if res["endpoints"]:
                            return res
                    except json.JSONDecodeError:
                        pass
            except Exception as e:
                logger.debug("Direct extraction failed: %s", e)


        # 2. LLM Parsing with Gemini
        prompt = f"""
        You are an expert API architect. Your goal is to extract a structured API specification from the provided documentation text.
        
        INSTRUCTIONS:
        1. Extract all API endpoints, methods (GET, POST, etc.), paths, and parameters.
        2. If a method is not explicitly stated, INFER it from the context (e.g., "submit form" -> POST, "retrieve" -> GET).
        3. If parameters are described in text, extract them into the JSON structure.
        4. Translating non-English descriptions to English is REQUIRED.
        5. Return a STRICT JSON object matching the structure below. Do not add markdown formatting if possible.
        6. If the text seems to be a raw JSON spec, parse it accordingly.

        API Documentation Text:
        {cleaned_text}

        REQUIRED JSON OUTPUT STRUCTURE:
        {{
            "name": "inferred or explicit API Name",
            "version": "1.0.0",
            "base_url": "https://api.example.com/v1 (infer from docs or use placeholder)",
            "description": "Short description of the API",
            "authentication": {{
                "type": "bearer" or "apiKey" or "none",
                "name": "api_key (if known)",
                "in": "header" or "query"
            }},
            "endpoints": [
                {{
                    "method": "GET",
                    "path": "/resource/{{id}}",
                    "summary": "Short summary of action",
                    "parameters": {{
                        "path": [{{ "name": "id", "type": "string", "required": true }}],
                        "query": [],
                        "header": [],
                        "body": [] 
                    }},
                    "request_body": {{ "key": "value (example)" }},
                    "responses": {{ "200": {{ "description": "Success" }} }}
                }}
            ]
        }}
        """

        if not self.model and not self.groq_client:
            raise Exception("AI service unavailable: Neither Gemini model nor Groq client initialized. Please check your GEMINI_API_KEY or GROQ_API_KEY.")

        if self.model:
            try:
                response = await self.model.generate_content_async(
                    prompt,
                    generation_config={"response_mime_type": "application/json"},
                )
                
                raw_text = response.text
                # Clean up markdown code blocks if present
                if "```json" in raw_text:
                    raw_text = raw_text.replace("```json", "").replace("```", "")
                elif "```" in raw_text:
                     raw_text = raw_text.replace("```", "")

                try:
                    spec_json = json.loads(raw_text.strip())
                except json.JSONDecodeError:
                    # Fallback: Use json_repair
                    import json_repair
                    spec_json = json_repair.loads(raw_text.strip())
                    
                return {**spec_json, "source": f"gemini_{self.model_name.split('/')[-1]}", "is_mock": False}
            except Exception as e:
                logger.warning("Gemini parsing failed: %s", e)
                # Final Fallback: try to repair whatever text we have
                try:
                    import json_repair
                    spec_json = json_repair.loads(response.text)
                    if spec_json:
                        return {**spec_json, "source": f"gemini_{self.model_name.split('/')[-1]}", "is_mock": False}
                except Exception as repair_err:
                    logger.debug("Fallback json_repair failed: %s", repair_err)
                raise Exception(f"AI Generation failed: {str(e)}")
        else:
            try:
                response = await self.groq_client.chat.completions.create(
                    model=self.groq_model,
                    messages=[
                        {"role": "system", "content": "You are an expert API architect. Return a STRICT JSON object according to the requested schema. Do not add markdown formatting or wrapper around the JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    max_tokens=900,
                    response_format={"type": "json_object"}
                )
                raw_text = response.choices[0].message.content
                # Clean up markdown code blocks if present
                if "```json" in raw_text:
                    raw_text = raw_text.replace("```json", "").replace("```", "")
                elif "```" in raw_text:
                     raw_text = raw_text.replace("```", "")

                try:
                    spec_json = json.loads(raw_text.strip())
                except json.JSONDecodeError:
                    import json_repair
                    spec_json = json_repair.loads(raw_text.strip())
                    
                return {**spec_json, "source": f"groq_{self.groq_model}", "is_mock": False}
            except Exception as e:
                logger.warning("Groq parsing failed: %s", e)
                raise Exception(f"AI Generation via Groq failed: {str(e)}")

