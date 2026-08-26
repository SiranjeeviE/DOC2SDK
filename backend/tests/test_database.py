import os
import uuid
import tempfile
import pytest
from unittest.mock import patch
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError
from alembic.config import Config
from alembic import command

from app.core.database import create_db_engine, normalize_database_url
from app.core.sanitizer import sanitize_headers, sanitize_payload, REDACTED
from app.models.domain import Project, ApiSpec, GeneratedSDK, PlaygroundRequest
from app.repositories.project_repo import ProjectRepository


def test_normalize_database_url():
    legacy_url = "postgres://user:secret@localhost:5432/doc2sdk"
    normalized = normalize_database_url(legacy_url)
    assert normalized == "postgresql://user:secret@localhost:5432/doc2sdk"

    standard_url = "postgresql://user:secret@localhost:5432/doc2sdk"
    assert normalize_database_url(standard_url) == standard_url

    sqlite_url = "sqlite:///./dev.db"
    assert normalize_database_url(sqlite_url) == sqlite_url


def test_production_postgresql_engine_configuration():
    pg_url = "postgresql://user:secret@localhost:5432/doc2sdk"
    with patch.dict(os.environ, {"DB_POOL_SIZE": "15", "DB_MAX_OVERFLOW": "25", "DB_POOL_RECYCLE": "600"}):
        engine = create_db_engine(pg_url)
        assert engine.pool.size() == 15
        assert engine.pool._max_overflow == 25
        assert engine.pool._recycle == 600
        assert engine.pool._pre_ping is True


def test_credential_sanitizer():
    raw_headers = {
        "Authorization": "Bearer secret-token-12345",
        "X-API-Key": "my-api-key-999",
        "Content-Type": "application/json",
        "Cookie": "session=abcde12345",
        "User-Agent": "Doc2SDK-Client/1.0",
    }
    cleaned_headers = sanitize_headers(raw_headers)
    assert cleaned_headers["Authorization"] == REDACTED
    assert cleaned_headers["X-API-Key"] == REDACTED
    assert cleaned_headers["Cookie"] == REDACTED
    assert cleaned_headers["Content-Type"] == "application/json"
    assert cleaned_headers["User-Agent"] == "Doc2SDK-Client/1.0"

    raw_payload = {
        "username": "alice",
        "password": "super-secret-password",
        "nested": {
            "api_key": "nested-key-val",
            "safe_field": "hello world",
        },
        "tokens": ["token1", "token2"],
    }
    cleaned_payload = sanitize_payload(raw_payload)
    assert cleaned_payload["username"] == "alice"
    assert cleaned_payload["password"] == REDACTED
    assert cleaned_payload["nested"]["api_key"] == REDACTED
    assert cleaned_payload["nested"]["safe_field"] == "hello world"


def test_project_creation(db):
    project = ProjectRepository.create_project(
        db=db,
        name="Payment Service API",
        description="Core payment processing gateway",
    )
    assert project.id is not None
    assert project.name == "Payment Service API"
    assert project.created_at is not None
    assert project.updated_at is not None

    fetched = ProjectRepository.get_project(db, project.id)
    assert fetched is not None
    assert fetched.name == "Payment Service API"


def test_api_spec_versions_and_unique_constraint(db):
    project = ProjectRepository.create_project(db, name="Billing API")

    # Version 1
    spec1 = ProjectRepository.create_spec(
        db=db,
        project_id=project.id,
        version=1,
        spec_data={"openapi": "3.0.0", "info": {"title": "Billing API v1"}},
    )
    assert spec1.version == 1

    # Version 2
    spec2 = ProjectRepository.create_spec(
        db=db,
        project_id=project.id,
        version=2,
        spec_data={"openapi": "3.0.0", "info": {"title": "Billing API v2"}},
    )
    assert spec2.version == 2

    # Verify latest spec
    latest = ProjectRepository.get_latest_spec(db, project.id)
    assert latest.version == 2

    # Verify order
    specs = ProjectRepository.get_specs(db, project.id)
    assert len(specs) == 2
    assert specs[0].version == 2
    assert specs[1].version == 1

    # Unique constraint test: duplicate version for the same project must fail
    with pytest.raises(IntegrityError):
        duplicate_spec = ApiSpec(
            project_id=project.id,
            version=1,
            spec_data={"duplicate": True},
        )
        db.add(duplicate_spec)
        db.commit()
    db.rollback()


def test_sdk_versions_and_cascade_delete(db):
    project = ProjectRepository.create_project(db, name="Messaging API")
    spec = ProjectRepository.create_spec(db, project.id, 1, {"title": "Messaging"})

    sdk = ProjectRepository.create_sdk(
        db=db,
        api_spec_id=spec.id,
        version=1,
        language="python",
        sdk_code="class MessagingClient: pass",
        test_code="def test_client(): pass",
    )
    assert sdk.id is not None
    assert sdk.test_code == "def test_client(): pass"

    # Verify SDK retrieval
    sdks = ProjectRepository.get_sdks(db, project.id)
    assert len(sdks) == 1
    assert sdks[0].id == sdk.id

    # Cascade delete: deleting project must cascade and delete spec and SDK
    success = ProjectRepository.delete_project(db, project.id)
    assert success is True

    assert db.query(Project).filter_by(id=project.id).first() is None
    assert db.query(ApiSpec).filter_by(id=spec.id).first() is None
    assert db.query(GeneratedSDK).filter_by(id=sdk.id).first() is None


def test_playground_request_history_and_sanitization(db):
    project = ProjectRepository.create_project(db, name="Users API")

    req = ProjectRepository.record_playground_request(
        db=db,
        project_id=project.id,
        method="POST",
        path="/users",
        base_url="https://api.example.com",
        params={"active": "true"},
        request_headers={"Authorization": "Bearer secret-val", "Content-Type": "application/json"},
        request_body={"username": "john", "password": "supersecretpassword"},
        response_status=201,
        response_headers={"Content-Type": "application/json", "Set-Cookie": "session=123"},
        response_body={"id": 101, "username": "john"},
        execution_time_ms=85,
    )

    assert req.id is not None
    assert req.execution_time_ms == 85
    # Verify sanitization
    assert req.request_headers["Authorization"] == REDACTED
    assert req.request_body["password"] == REDACTED
    assert req.response_headers["Set-Cookie"] == REDACTED
    assert req.response_body["username"] == "john"

    # History retrieval
    history = ProjectRepository.get_playground_history(db, project.id)
    assert len(history) == 1
    assert history[0].id == req.id

    # Cascade delete test
    ProjectRepository.delete_project(db, project.id)
    assert db.query(PlaygroundRequest).filter_by(id=req.id).first() is None


def test_playground_replay_endpoint(client, db):
    project = ProjectRepository.create_project(db, name="Replay Test API")

    # Record historical request
    historical_req = ProjectRepository.record_playground_request(
        db=db,
        project_id=project.id,
        method="GET",
        path="/items",
        base_url="https://httpbin.org",
        params={"limit": "5"},
        request_headers={"Accept": "application/json"},
        request_body=None,
        response_status=200,
        response_body={"items": []},
        execution_time_ms=50,
    )

    # Replay request via API endpoint with mocked executor
    with patch("app.routers.playground.executor_service.execute_request") as mock_exec:
        mock_exec.return_value = (200, {"items": ["item1", "item2"]})

        response = client.post(f"/api/projects/{project.id}/playground/history/{historical_req.id}/replay")
        assert response.status_code == 200
        data = response.json()
        assert data["status_code"] == 200
        assert data["response"] == {"items": ["item1", "item2"]}

    # Verify a new history entry was created by the replay
    history = ProjectRepository.get_playground_history(db, project.id)
    assert len(history) == 2


def test_migration_from_empty_database():
    """
    Tests creating a fresh database from scratch via Alembic migrations,
    verifying all tables, columns, and indexes, and testing clean downgrade.
    """
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_db:
        tmp_db_path = tmp_db.name

    try:
        db_url = f"sqlite:///{tmp_db_path}"
        backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        alembic_ini_path = os.path.join(backend_dir, "alembic.ini")

        with patch.dict(os.environ, {"DATABASE_URL": db_url}):
            alembic_cfg = Config(alembic_ini_path)
            alembic_cfg.set_main_option("sqlalchemy.url", db_url)
            alembic_cfg.set_main_option("script_location", os.path.join(backend_dir, "alembic"))

            # Run upgrade head on fresh database
            command.upgrade(alembic_cfg, "head")

            # Inspect created schema
            temp_engine = create_db_engine(db_url)
            inspector = inspect(temp_engine)

            tables = inspector.get_table_names()
            assert "projects" in tables
            assert "api_specs" in tables
            assert "generated_sdks" in tables
            assert "playground_requests" in tables

            # Verify composite indexes
            spec_indexes = [idx["name"] for idx in inspector.get_indexes("api_specs")]
            assert "ix_api_specs_project_id_version" in spec_indexes

            sdk_indexes = [idx["name"] for idx in inspector.get_indexes("generated_sdks")]
            assert "ix_generated_sdks_api_spec_id_version" in sdk_indexes

            # Verify replay columns in playground_requests
            play_cols = [c["name"] for c in inspector.get_columns("playground_requests")]
            assert "base_url" in play_cols
            assert "params" in play_cols
            assert "request_headers" in play_cols
            assert "request_body" in play_cols
            assert "response_headers" in play_cols
            assert "response_body" in play_cols
            assert "execution_time_ms" in play_cols
            assert "error_message" in play_cols

            # Test downgrade to base
            command.downgrade(alembic_cfg, "base")

            downgraded_tables = inspect(temp_engine).get_table_names()
            assert "projects" not in downgraded_tables
            assert "api_specs" not in downgraded_tables
            assert "generated_sdks" not in downgraded_tables
            assert "playground_requests" not in downgraded_tables

            temp_engine.dispose()

    finally:
        if os.path.exists(tmp_db_path):
            try:
                os.remove(tmp_db_path)
            except OSError:
                pass


def test_workspace_stats_endpoint(client, db):
    p1 = ProjectRepository.create_project(db, name="API 1")
    ProjectRepository.create_spec(
        db, p1.id, 1,
        {"endpoints": [{"path": "/e1", "method": "GET"}, {"path": "/e2", "method": "POST"}]}
    )
    s1 = ProjectRepository.get_latest_spec(db, p1.id)
    ProjectRepository.create_sdk(db, s1.id, 1, "python", "code1")

    p2 = ProjectRepository.create_project(db, name="API 2")
    ProjectRepository.create_spec(
        db, p2.id, 1,
        {"endpoints": [{"path": "/users", "method": "GET"}]}
    )

    ProjectRepository.record_playground_request(db, p1.id, "GET", "/e1", 200)

    res = client.get("/api/projects/stats/overview")
    assert res.status_code == 200
    data = res.json()
    assert data["total_projects"] == 2
    assert data["total_sdks"] == 1
    assert data["total_endpoints"] == 3
    assert data["total_api_calls"] == 1

