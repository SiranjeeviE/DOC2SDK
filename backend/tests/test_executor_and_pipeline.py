import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import HTTPException

from app.services.executor import ExecutionService
from app.services.pipeline import PipelineService
from app.parsers.openapi import NormalizedAPISpec


@pytest.mark.asyncio
async def test_execution_service_success(monkeypatch):
    service = ExecutionService()

    # Mock safe client
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": "ok", "message": "hello"}

    mock_client = AsyncMock()
    mock_client.request.return_value = mock_response
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None

    monkeypatch.setattr("app.services.executor.create_safe_client", lambda timeout=30.0: mock_client)
    monkeypatch.setattr("app.services.executor.validate_url", lambda url: url)

    status_code, data = await service.execute_request(
        base_url="https://api.example.com",
        path="/v1/status",
        method="GET",
    )

    assert status_code == 200
    assert data == {"status": "ok", "message": "hello"}


@pytest.mark.asyncio
async def test_execution_service_ssrf_block():
    service = ExecutionService()
    with pytest.raises(HTTPException) as exc_info:
        await service.execute_request(
            base_url="http://127.0.0.1",
            path="/admin",
            method="GET",
        )
    assert exc_info.value.status_code == 400


def test_pipeline_service_parse_and_generate():
    pipeline = PipelineService()
    spec = NormalizedAPISpec(
        name="TestApi",
        version="1.0.0",
        base_url="https://api.example.com",
        endpoints=[]
    )

    sdk_code, test_code = pipeline.generate_sdk_and_tests(spec, "python")
    assert "class TestApiClient:" in sdk_code
    assert "class TestTestApiEndpoints:" in test_code
