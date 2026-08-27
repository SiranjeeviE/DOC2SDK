import pytest
from unittest.mock import AsyncMock

async def mock_scrape(url):
    return 'RAW_SPEC_JSON:\n{"openapi": "3.0.0", "info": {"title": "Test", "version": "1.0"}, "paths": {}}'

def test_playground_run(client, monkeypatch):
    monkeypatch.setattr('app.services.scraper.ScraperService.scrape', mock_scrape)
    
    # Create project first
    create_resp = client.post("/api/projects", json={
        "name": "Playground Project",
        "source_url": "https://example.com"
    })
    assert create_resp.status_code == 200
    project_id = create_resp.json()["id"]
    
    class MockResponse:
        status_code = 200
        text = '{"msg": "success"}'
        def json(self):
            return {"msg": "success"}

    async def mock_request(*args, **kwargs):
        return MockResponse()
        
    monkeypatch.setattr('httpx.AsyncClient.request', mock_request)
    
    # Mock translator service
    async def mock_translate(*args, **kwargs):
        return {"msg": "success translated"}
        
    monkeypatch.setattr('app.services.translator.TranslationService.translate_response', mock_translate)

    # Run playground request
    run_response = client.post(f"/api/projects/{project_id}/playground/run", json={
        "base_url": "https://example.com",
        "path": "/test",
        "method": "GET"
    })
    
    assert run_response.status_code == 200
    data = run_response.json()
    assert data["status_code"] == 200
    assert data["response"] == {"msg": "success translated"}
    
    # Check history
    history_resp = client.get(f"/api/projects/{project_id}/playground/history")
    assert history_resp.status_code == 200
    history = history_resp.json()
    assert len(history) == 1
    assert history[0]["method"] == "GET"
    assert history[0]["path"] == "/test"
    assert history[0]["response_status"] == 200
