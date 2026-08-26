import pytest
from app.services.diff import SpecDiffService

SPEC_V1 = {
    "name": "User Service",
    "version": "1.0.0",
    "authentication": {"type": "none"},
    "endpoints": [
        {
            "method": "GET",
            "path": "/users",
            "summary": "List Users",
            "parameters": {
                "query": [
                    {"name": "page", "type": "integer", "required": False}
                ]
            },
            "responses": {"200": {"description": "OK"}}
        },
        {
            "method": "DELETE",
            "path": "/users/{id}",
            "summary": "Delete User",
            "parameters": {
                "path": [{"name": "id", "type": "string", "required": True}]
            },
            "responses": {"204": {"description": "Deleted"}}
        }
    ]
}

SPEC_V2_BREAKING = {
    "name": "User Service",
    "version": "2.0.0",
    "authentication": {"type": "bearer"},  # BREAKING: Auth changed from none to bearer
    "endpoints": [
        {
            "method": "GET",
            "path": "/users",
            "summary": "List Users",
            "parameters": {
                "query": [
                    {"name": "page", "type": "integer", "required": True}  # BREAKING: page became required
                ]
            },
            "responses": {"200": {"description": "OK"}}
        },
        # BREAKING: DELETE /users/{id} was removed!
        {
            "method": "POST",
            "path": "/users",
            "summary": "Create User",
            "parameters": {},
            "request_body": {"required": True},
            "responses": {"201": {"description": "Created"}}
        }
    ]
}


def test_spec_diff_detects_breaking_changes():
    report = SpecDiffService.compare_specs(SPEC_V1, SPEC_V2_BREAKING)

    assert report["has_breaking_changes"] is True
    assert report["breaking_count"] >= 3
    assert report["non_breaking_count"] >= 1  # Added POST /users

    # Verify specific breaking detections
    descriptions = [c["description"] for c in report["changes"]]
    assert any("DELETE /users/{id}" in d and "removed" in d for d in descriptions)
    assert any("page" in d and "required" in d for d in descriptions)
    assert any("authentication type changed" in d for d in descriptions)


def test_spec_diff_no_changes():
    report = SpecDiffService.compare_specs(SPEC_V1, SPEC_V1)

    assert report["has_breaking_changes"] is False
    assert report["breaking_count"] == 0
    assert report["non_breaking_count"] == 0
    assert report["total_changes"] == 0
    assert "No changes detected" in report["summary"]
