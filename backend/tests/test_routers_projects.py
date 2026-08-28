import pytest
from unittest.mock import patch

async def mock_scrape(url):
    return 'RAW_SPEC_JSON:\n{"openapi": "3.0.0", "info": {"title": "Test", "version": "1.0"}, "paths": {}}'

def test_create_and_list_project(client, monkeypatch):
    # Mock the scraper to return a raw spec instead of doing real scraping
    monkeypatch.setattr('app.services.scraper.ScraperService.scrape', mock_scrape)
    
    # 1. Create project
    response = client.post("/api/projects", json={
        "name": "Test Project",
        "description": "Test Desc",
        "source_url": "https://example.com"
    })
    assert response.status_code == 200
    project_data = response.json()
    assert project_data["name"] == "Test Project"
    project_id = project_data["id"]
    
    # 2. List projects
    list_response = client.get("/api/projects")
    assert list_response.status_code == 200
    projects = list_response.json()
    assert len(projects) >= 1
    assert any(p["id"] == project_id for p in projects)
    
    # 3. Get project by ID
    get_response = client.get(f"/api/projects/{project_id}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == project_id
    
    # 4. Check initial spec was created (due to background task executing synchronously in TestClient)
    specs_response = client.get(f"/api/projects/{project_id}/specs")
    assert specs_response.status_code == 200
    specs = specs_response.json()
    assert len(specs) == 1
    assert specs[0]["version"] == 1
    
async def mock_initial_scrape(url):
    return 'RAW_SPEC_JSON:\n{"openapi": "3.0.0", "info": {"title": "Initial", "version": "1.0"}, "paths": {}}'

async def mock_updated_scrape(url):
    return 'RAW_SPEC_JSON:\n{"openapi": "3.0.0", "info": {"title": "Updated", "version": "2.0"}, "paths": {}}'

def test_rescrape_versioning(client, monkeypatch):
    # Mock initial scrape
    monkeypatch.setattr('app.services.scraper.ScraperService.scrape', mock_initial_scrape)
    create_response = client.post("/api/projects", json={
        "name": "Rescrape Project",
        "source_url": "https://example.com/api"
    })
    project_id = create_response.json()["id"]
    
    # Verify version 1
    specs_response = client.get(f"/api/projects/{project_id}/specs")
    assert len(specs_response.json()) == 1
    assert specs_response.json()[0]["version"] == 1
    
    # Mock rescrape
    monkeypatch.setattr('app.services.scraper.ScraperService.scrape', mock_updated_scrape)
    rescrape_response = client.post(f"/api/projects/{project_id}/rescrape", json={
        "source_url": "https://example.com/api/v2"
    })
    assert rescrape_response.status_code == 202
    
    # Verify version 2 created
    specs_response = client.get(f"/api/projects/{project_id}/specs")
    assert len(specs_response.json()) == 2
    versions = [s["version"] for s in specs_response.json()]
    assert 1 in versions
    assert 2 in versions
    
async def mock_sdk_scrape(url):
    return 'RAW_SPEC_JSON:\n{"openapi": "3.0.0", "info": {"title": "SDK API", "version": "1.0"}, "paths": {}}'

def test_regenerate_sdk_versioning(client, monkeypatch):
    monkeypatch.setattr('app.services.scraper.ScraperService.scrape', mock_sdk_scrape)
    create_response = client.post("/api/projects", json={
        "name": "SDK Project",
        "source_url": "https://example.com"
    })
    project_id = create_response.json()["id"]
    
    # Initial SDK generation (version 1)
    sdks_response = client.get(f"/api/projects/{project_id}/sdks")
    assert sdks_response.status_code == 200
    sdks = sdks_response.json()
    assert len(sdks) == 1
    assert sdks[0]["version"] == 1
    assert sdks[0]["language"] == "python"
    
    # Regenerate SDK (defaults to python, version 2)
    regen_response = client.post(f"/api/projects/{project_id}/regenerate-sdk", json={
        "language": "python"
    })
    assert regen_response.status_code == 200
    assert regen_response.json()["version"] == 2
    
    # Check SDKs list again
    sdks_response = client.get(f"/api/projects/{project_id}/sdks")
    sdks = sdks_response.json()
    assert len(sdks) == 2
    versions = [s["version"] for s in sdks]
    assert 1 in versions
    assert 2 in versions


def test_update_project(client, monkeypatch):
    monkeypatch.setattr('app.services.scraper.ScraperService.scrape', mock_scrape)
    
    # 1. Create project
    create_response = client.post("/api/projects", json={
        "name": "Original Name",
        "description": "Original Description",
        "source_url": "https://example.com"
    })
    assert create_response.status_code == 200
    project_id = create_response.json()["id"]

    # 2. Update project
    update_response = client.put(f"/api/projects/{project_id}", json={
        "name": "Updated Name",
        "description": "Updated Description"
    })
    assert update_response.status_code == 200
    updated_data = update_response.json()
    assert updated_data["name"] == "Updated Name"
    assert updated_data["description"] == "Updated Description"

    # 3. Fetch project and verify persistence
    get_response = client.get(f"/api/projects/{project_id}")
    assert get_response.status_code == 200
    assert get_response.json()["name"] == "Updated Name"
    assert get_response.json()["description"] == "Updated Description"

    # 4. Update non-existent project -> 404
    bad_id_response = client.put("/api/projects/00000000-0000-0000-0000-000000000000", json={
        "name": "Ghost"
    })
    assert bad_id_response.status_code == 404

    # 5. Empty name validation -> 400
    bad_name_response = client.put(f"/api/projects/{project_id}", json={
        "name": "   "
    })
    assert bad_name_response.status_code == 400


def test_patch_project(client, monkeypatch):
    monkeypatch.setattr('app.services.scraper.ScraperService.scrape', mock_scrape)
    
    # 1. Create project without description -> description defaults to source_url
    create_response = client.post("/api/projects", json={
        "name": "Patch Target",
        "source_url": "https://example.com/api"
    })
    assert create_response.status_code == 200
    project_data = create_response.json()
    project_id = project_data["id"]
    assert project_data["description"] == "https://example.com/api"

    # 2. PATCH update name only
    patch_response = client.patch(f"/api/projects/{project_id}", json={
        "name": "Patched Name"
    })
    assert patch_response.status_code == 200
    assert patch_response.json()["name"] == "Patched Name"
    assert patch_response.json()["description"] == "https://example.com/api"

    # 3. PATCH update description
    patch_response2 = client.patch(f"/api/projects/{project_id}", json={
        "description": "https://example.com/new-api"
    })
    assert patch_response2.status_code == 200
    assert patch_response2.json()["description"] == "https://example.com/new-api"

    # 4. Verify in GET
    get_res = client.get(f"/api/projects/{project_id}")
    assert get_res.status_code == 200
    assert get_res.json()["name"] == "Patched Name"
    assert get_res.json()["description"] == "https://example.com/new-api"

