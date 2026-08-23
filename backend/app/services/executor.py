import json
import logging
from typing import Any, Dict, Optional, Tuple
from fastapi import HTTPException

from ..core.url_validator import validate_url, create_safe_client, URLValidationError
from ..services.translator import TranslationService

logger = logging.getLogger(__name__)


class ExecutionService:
    """
    Centralized execution service for dispatching safe, SSRF-validated HTTP requests
    in the interactive playground with automatic response translation.
    """

    def __init__(self):
        self.translator_service = TranslationService()

    async def execute_request(
        self,
        base_url: str,
        path: str,
        method: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        json_body: Optional[Any] = None,
        timeout: float = 30.0,
    ) -> Tuple[Optional[int], Any]:
        """
        Executes an HTTP request to an external API endpoint with SSRF protection,
        error handling, and AI-powered response translation.

        Returns:
            Tuple[status_code, response_data]
        """
        url = base_url.rstrip("/") + "/" + path.lstrip("/")
        try:
            validated_url = validate_url(url)
        except URLValidationError as e:
            raise HTTPException(status_code=400, detail=str(e))

        client = create_safe_client(timeout=timeout)
        async with client:
            try:
                response = await client.request(
                    method=method,
                    url=validated_url,
                    params=params,
                    headers=headers,
                    json=json_body,
                )
                status_code = response.status_code

                try:
                    raw_data = response.json()
                    data = await self.translator_service.translate_response(raw_data)
                except (json.JSONDecodeError, ValueError) as json_err:
                    logger.debug("Response body is not JSON, falling back to raw text: %s", json_err)
                    data = response.text

                return status_code, data
            except URLValidationError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except HTTPException:
                raise
            except Exception as e:
                logger.warning("External request failed for %s: %s", validated_url, e)
                raise HTTPException(status_code=400, detail="Request to external API failed.")
