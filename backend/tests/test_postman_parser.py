import pytest
import json
from app.parsers.postman import PostmanParser

SAMPLE_POSTMAN_COLLECTION = {
    "info": {
        "_postman_id": "12345-abcde",
        "name": "E-Commerce Postman API",
        "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        "description": "API for e-commerce orders and products"
    },
    "auth": {
        "type": "bearer",
        "bearer": [{"key": "token", "value": "secret_token_123"}]
    },
    "item": [
        {
            "name": "Products",
            "item": [
                {
                    "name": "Get Product by ID",
                    "request": {
                        "method": "GET",
                        "url": {
                            "raw": "https://api.store.com/v1/products/:productId?include_reviews=true",
                            "host": ["api", "store", "com"],
                            "path": ["v1", "products", ":productId"],
                            "query": [
                                {"key": "include_reviews", "value": "true", "description": "Include user reviews"}
                            ],
                            "variable": [
                                {"key": "productId", "value": "p100", "description": "Target product ID"}
                            ]
                        },
                        "description": "Fetches a single product by unique ID"
                    },
                    "response": [
                        {
                            "code": 200,
                            "name": "Product Found",
                            "body": "{\"id\": \"p100\", \"title\": \"Smart Watch\"}"
                        }
                    ]
                }
            ]
        },
        {
            "name": "Create Order",
            "request": {
                "method": "POST",
                "url": "https://api.store.com/v1/orders",
                "header": [
                    {"key": "Content-Type", "value": "application/json"}
                ],
                "body": {
                    "mode": "raw",
                    "raw": "{\"item_id\": \"p100\", \"quantity\": 2}"
                }
            }
        }
    ]
}


def test_postman_parser_success():
    parser = PostmanParser()
    spec = parser.parse(json.dumps(SAMPLE_POSTMAN_COLLECTION))

    assert spec.name == "E-Commerce Postman API"
    assert spec.authentication["type"] == "bearer"
    assert spec.base_url == "https://api.store.com"
    assert len(spec.endpoints) == 2

    # Check first endpoint (under folder Products)
    ep1 = next(e for e in spec.endpoints if e.method == "GET")
    assert ep1.path == "/v1/products/{productId}"
    assert ep1.summary == "Get Product by ID"
    assert "Products" in ep1.tags
    assert any(p["name"] == "productId" for p in ep1.parameters["path"])
    assert any(p["name"] == "include_reviews" for p in ep1.parameters["query"])
    assert "200" in ep1.responses

    # Check second endpoint
    ep2 = next(e for e in spec.endpoints if e.method == "POST")
    assert ep2.path == "/v1/orders"
    assert ep2.request_body is not None


def test_postman_parser_rejects_invalid_json():
    parser = PostmanParser()
    with pytest.raises(ValueError, match="Invalid JSON"):
        parser.parse("not json content {")


def test_postman_parser_rejects_non_collection():
    parser = PostmanParser()
    with pytest.raises(ValueError, match="Not a valid Postman collection"):
        parser.parse(json.dumps({"some_key": "some_value"}))
