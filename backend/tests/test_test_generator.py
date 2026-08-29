import pytest
from app.generators.sdk_gen import CodeGenerator
from app.parsers.openapi import NormalizedAPISpec, APIEndpointSchema

SAMPLE_SPEC = NormalizedAPISpec(
    name="PaymentGateway",
    version="1.0.0",
    base_url="https://api.payment.com/v1",
    authentication={"type": "apiKey", "name": "X-API-Key", "in": "header"},
    endpoints=[
        APIEndpointSchema(
            method="POST",
            path="/charges",
            summary="Create Charge",
            parameters={
                "path": [],
                "query": [{"name": "currency", "type": "string", "example": "USD"}],
                "header": [],
                "cookie": []
            },
            request_body={"required": True},
            responses={"200": {"description": "Charge created"}}
        ),
        APIEndpointSchema(
            method="GET",
            path="/charges/{charge_id}",
            summary="Get Charge",
            parameters={
                "path": [{"name": "charge_id", "type": "string", "required": True}],
                "query": [],
                "header": [],
                "cookie": []
            },
            responses={"200": {"description": "Charge details"}}
        )
    ]
)


def test_generate_python_tests():
    generator = CodeGenerator()
    test_code = generator.generate_python_tests(SAMPLE_SPEC)

    assert "import pytest" in test_code
    assert "import httpx" in test_code
    assert "mock_client" in test_code
    # Endpoints tested
    assert "test_create_charge_success" in test_code
    assert "test_create_charge_client_error" in test_code
    assert "test_create_charge_server_error" in test_code
    assert "test_get_charge_success" in test_code
    assert "assert result is not None" in test_code


def test_generate_typescript_tests():
    generator = CodeGenerator()
    test_code = generator.generate_tests(SAMPLE_SPEC, language="typescript")

    assert "describe('PaymentGatewayClient Test Suite'" in test_code
    assert "should successfully execute" in test_code
    assert "should handle API errors" in test_code
    assert "expect(result).toEqual" in test_code
