import json
import logging
from typing import Any, Dict, Tuple
from fastapi import HTTPException

from ..parsers.openapi import NormalizedAPISpec, OpenAPIParser
from ..parsers.postman import PostmanParser
from ..services.scraper import ScraperService
from ..services.llm_parser import LLMParserService
from ..generators.sdk_gen import CodeGenerator
from ..core.url_validator import validate_url, URLValidationError

logger = logging.getLogger(__name__)


class PipelineService:
    """
    Centralized service for the API documentation extraction, parsing,
    and SDK/test generation pipeline.
    """

    def __init__(self):
        self.parser_service = LLMParserService()
        self.code_generator = CodeGenerator()
        self.openapi_parser = OpenAPIParser()
        self.postman_parser = PostmanParser()

    async def scrape_and_parse(self, source_url: str) -> Tuple[NormalizedAPISpec, Dict[str, Any]]:
        """
        Validates the URL, scrapes documentation, and parses it into a NormalizedAPISpec.
        Returns a tuple of (NormalizedAPISpec, spec_dict).
        """
        validate_url(source_url)
        cleaned_text = await ScraperService.scrape(source_url)

        if cleaned_text.startswith("RAW_SPEC_JSON:"):
            raw_content = cleaned_text.replace("RAW_SPEC_JSON:\n", "", 1)
            spec = self.openapi_parser.parse(raw_content)
            spec_dict = spec.model_dump() if hasattr(spec, "model_dump") else spec.dict()
            spec_dict["source"] = "direct_openapi_parser"
            spec_dict["is_mock"] = False
            return spec, spec_dict
        else:
            spec_dict = await self.parser_service.parse_docs(cleaned_text)
            spec = NormalizedAPISpec(**spec_dict)
            return spec, spec_dict

    def parse_uploaded_content(self, text: str, filename: str = "") -> Tuple[NormalizedAPISpec, str]:
        """
        Parses raw text content (JSON or YAML) from an uploaded file into NormalizedAPISpec.
        Supports Postman collections and OpenAPI/Swagger specs.
        """
        # Try Postman collection JSON
        try:
            data = json.loads(text)
            if isinstance(data, dict) and "info" in data and ("_postman_id" in data["info"] or "schema" in data["info"]):
                return self.postman_parser.parse(text), "postman_collection"
            # Try OpenAPI JSON
            return self.openapi_parser.parse(text), "openapi_json"
        except (json.JSONDecodeError, ValueError) as json_err:
            logger.debug("Content is not JSON or JSON parsing failed: %s", json_err)

        # Try OpenAPI YAML
        try:
            return self.openapi_parser.parse(text), "openapi_yaml"
        except Exception as yaml_err:
            logger.debug("YAML OpenAPI parsing failed: %s", yaml_err)

        raise HTTPException(
            status_code=400,
            detail="Unsupported or invalid specification format. Please upload a valid OpenAPI/Swagger (JSON or YAML) or Postman Collection v2.0/v2.1 JSON file."
        )

    def generate_sdk_and_tests(self, spec: NormalizedAPISpec, language: str = "python") -> Tuple[str, str]:
        """
        Generates production-grade SDK code and automated test suite for the given spec.
        """
        sdk_code = self.code_generator.generate_sdk(spec, language)
        test_code = self.code_generator.generate_tests(spec, language)
        return sdk_code, test_code
