import logging
from fastapi import APIRouter, Depends, HTTPException

from .. import schemas
from ..core.auth import require_auth
from ..core.rate_limiter import rate_limit_ai, rate_limit_general
from ..core.url_validator import URLValidationError
from ..services.pipeline import PipelineService
from ..services.executor import ExecutionService

logger = logging.getLogger(__name__)

router = APIRouter()
pipeline_service = PipelineService()
executor_service = ExecutionService()


@router.post("/generate", response_model=schemas.GenerateResponse)
async def generate_sdk(
    request: schemas.GenerateRequest,
    _auth: bool = Depends(require_auth),
    _rate: None = Depends(rate_limit_ai),
):
    try:
        # 1. Scrape & Parse
        spec, spec_dict = await pipeline_service.scrape_and_parse(request.source_url)

        # 2. Generate Python SDK & Tests
        sdk_code, test_code = pipeline_service.generate_sdk_and_tests(spec, "python")

        return schemas.GenerateResponse(
            name=spec.name,
            version=spec.version,
            spec=spec_dict,
            sdk_code=sdk_code,
            test_code=test_code,
            is_mock=spec_dict.get("is_mock", False),
            source=spec_dict.get("source"),
        )
    except URLValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error during SDK generation for %s", request.source_url)
        raise HTTPException(status_code=500, detail="Failed to generate SDK. Please check your source URL and try again.")


@router.post("/playground/execute", response_model=schemas.ExecuteResponse)
async def execute_api_call(
    request: schemas.ExecuteRequest,
    _auth: bool = Depends(require_auth),
    _rate: None = Depends(rate_limit_general),
):
    status_code, data = await executor_service.execute_request(
        base_url=request.base_url,
        path=request.path,
        method=request.method,
        params=request.params,
        headers=request.headers,
        json_body=request.json_body,
    )

    return schemas.ExecuteResponse(
        status_code=status_code,
        response=data,
    )
