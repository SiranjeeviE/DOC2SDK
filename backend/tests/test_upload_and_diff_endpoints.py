import io
import json
import pytest

OPENAPI_YAML = """
openapi: 3.0.0
info:
  title: Petstore YAML API
  version: 1.0.0
paths:
  /pets:
    get:
      summary: List all pets
      responses:
        '200':
          description: A paged array of pets
"""

POSTMAN_JSON = {
    "info": {
        "_postman_id": "test-uuid-99",
        "name": "Postman Upload API",
        "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
    },
    "item": [
        {
            "name": "Get Status",
            "request": {
                "method": "GET",
                "url": "https://api.test.com/status"
            }
        }
    ]
}


def test_upload_openapi_yaml(client):
    file_bytes = OPENAPI_YAML.encode("utf-8")
    response = client.post(
        "/api/projects/upload",
        files={"file": ("openapi.yaml", file_bytes, "application/x-yaml")},
        data={"name": "YAML Petstore"}
    )
    assert response.status_code == 200
    project = response.json()
    assert project["name"] == "YAML Petstore"
    project_id = project["id"]

    # Verify specs were created
    specs_res = client.get(f"/api/projects/{project_id}/specs")
    assert specs_res.status_code == 200
    specs = specs_res.json()
    assert len(specs) == 1
    assert specs[0]["version"] == 1

    # Verify SDK and test_code were generated
    sdks_res = client.get(f"/api/projects/{project_id}/sdks")
    assert sdks_res.status_code == 200
    sdks = sdks_res.json()
    assert len(sdks) == 1
    assert sdks[0]["test_code"] is not None
    assert "test_list_all_pets_success" in sdks[0]["test_code"]

    # Test downloading tests
    sdk_id = sdks[0]["id"]
    download_res = client.get(f"/api/projects/{project_id}/sdk/{sdk_id}/download-tests")
    assert download_res.status_code == 200
    assert "test_list_all_pets_success" in download_res.text


def test_upload_postman_collection(client):
    file_bytes = json.dumps(POSTMAN_JSON).encode("utf-8")
    response = client.post(
        "/api/projects/upload",
        files={"file": ("collection.json", file_bytes, "application/json")},
        data={"name": "Postman API"}
    )
    assert response.status_code == 200
    project = response.json()
    assert project["name"] == "Postman API"


def test_upload_spec_version_and_diff(client):
    # 1. Create project via upload v1
    v1_bytes = OPENAPI_YAML.encode("utf-8")
    create_res = client.post(
        "/api/projects/upload",
        files={"file": ("v1.yaml", v1_bytes, "application/x-yaml")}
    )
    assert create_res.status_code == 200
    project_id = create_res.json()["id"]

    # 2. Check diff with only 1 version
    diff_v1 = client.get(f"/api/projects/{project_id}/diff")
    assert diff_v1.status_code == 200
    assert diff_v1.json()["total_changes"] == 0

    # 3. Upload v2 (breaking change: remove /pets, add /animals)
    openapi_v2 = """
openapi: 3.0.0
info:
  title: Petstore YAML API
  version: 2.0.0
paths:
  /animals:
    get:
      summary: List animals
      responses:
        '200':
          description: OK
"""
    v2_bytes = openapi_v2.encode("utf-8")
    v2_res = client.post(
        f"/api/projects/{project_id}/upload-spec",
        files={"file": ("v2.yaml", v2_bytes, "application/x-yaml")}
    )
    assert v2_res.status_code == 200
    assert v2_res.json()["version"] == 2

    # 4. Check diff between v1 and v2
    diff_v2 = client.get(f"/api/projects/{project_id}/diff")
    assert diff_v2.status_code == 200
    data = diff_v2.json()
    assert data["has_breaking_changes"] is True
    assert data["breaking_count"] >= 1  # /pets removed
    assert data["non_breaking_count"] >= 1  # /animals added
