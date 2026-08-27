import pytest
from app.parsers.openapi import OpenAPIParser

def test_openapi_parser_json():
    sample_spec = """
    {
      "openapi": "3.0.0",
      "info": {
        "title": "Test API",
        "version": "1.0.0"
      },
      "paths": {
        "/users": {
          "get": {
            "summary": "List users",
            "responses": {
              "200": {
                "description": "Success"
              }
            }
          }
        }
      }
    }
    """
    parser = OpenAPIParser()
    result = parser.parse(sample_spec)
    
    assert result.name == "Test API"
    assert result.version == "1.0.0"
    assert len(result.endpoints) == 1
    assert result.endpoints[0].method == "GET"
    assert result.endpoints[0].path == "/users"

def test_openapi_parser_yaml():
    sample_spec = """
openapi: 3.0.0
info:
  title: YAML API
  version: 2.0.0
paths:
  /ping:
    get:
      summary: Ping
    """
    parser = OpenAPIParser()
    result = parser.parse(sample_spec)
    
    assert result.name == "YAML API"
    assert result.version == "2.0.0"
    assert result.endpoints[0].path == "/ping"
