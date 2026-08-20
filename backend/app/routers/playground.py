import time
import logging
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import schemas
from ..core.auth import require_auth
from ..core.database import get_db
from ..core.rate_limiter import rate_limit_general
from ..repositories.project_repo import ProjectRepository
from ..services.executor import ExecutionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects", tags=["playground"])
executor_service = ExecutionService()


@router.post("/{id}/playground/run", response_model=schemas.core.ExecuteResponse)
async def run_playground_request(
    id: UUID,
    request: schemas.core.ExecuteRequest,
    db: Session = Depends(get_db),
    _auth: bool = Depends(require_auth),
    _rate: None = Depends(rate_limit_general),
):
    project = ProjectRepository.get_project(db, id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    start_time = time.perf_counter()
    try:
        status_code, data = await executor_service.execute_request(
            base_url=request.base_url,
            path=request.path,
            method=request.method,
            params=request.params,
            headers=request.headers,
            json_body=request.json_body,
        )
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        ProjectRepository.record_playground_request(
            db=db,
            project_id=id,
            method=request.method,
            path=request.path,
            base_url=request.base_url,
            params=request.params,
            request_headers=request.headers,
            request_body=request.json_body,
            response_status=status_code,
            response_body=data,
            execution_time_ms=duration_ms,
        )
        return schemas.core.ExecuteResponse(
            status_code=status_code,
            response=data,
        )
    except HTTPException as e:
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        ProjectRepository.record_playground_request(
            db=db,
            project_id=id,
            method=request.method,
            path=request.path,
            base_url=request.base_url,
            params=request.params,
            request_headers=request.headers,
            request_body=request.json_body,
            response_status=e.status_code if hasattr(e, 'status_code') else None,
            error_message=str(e.detail) if hasattr(e, 'detail') else str(e),
            execution_time_ms=duration_ms,
        )
        raise


@router.post("/{id}/playground/history/{request_id}/replay", response_model=schemas.core.ExecuteResponse)
async def replay_playground_request(
    id: UUID,
    request_id: UUID,
    db: Session = Depends(get_db),
    _auth: bool = Depends(require_auth),
    _rate: None = Depends(rate_limit_general),
):
    project = ProjectRepository.get_project(db, id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    historical = ProjectRepository.get_playground_request(db, request_id)
    if not historical or historical.project_id != id:
        raise HTTPException(status_code=404, detail="History record not found")

    base_url = historical.base_url or "https://api.example.com"
    start_time = time.perf_counter()
    try:
        status_code, data = await executor_service.execute_request(
            base_url=base_url,
            path=historical.path,
            method=historical.method,
            params=historical.params,
            headers=historical.request_headers,
            json_body=historical.request_body,
        )
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        ProjectRepository.record_playground_request(
            db=db,
            project_id=id,
            method=historical.method,
            path=historical.path,
            base_url=base_url,
            params=historical.params,
            request_headers=historical.request_headers,
            request_body=historical.request_body,
            response_status=status_code,
            response_body=data,
            execution_time_ms=duration_ms,
        )
        return schemas.core.ExecuteResponse(
            status_code=status_code,
            response=data,
        )
    except HTTPException as e:
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        ProjectRepository.record_playground_request(
            db=db,
            project_id=id,
            method=historical.method,
            path=historical.path,
            base_url=base_url,
            params=historical.params,
            request_headers=historical.request_headers,
            request_body=historical.request_body,
            response_status=e.status_code if hasattr(e, 'status_code') else None,
            error_message=str(e.detail) if hasattr(e, 'detail') else str(e),
            execution_time_ms=duration_ms,
        )
        raise


@router.get("/{id}/playground/history", response_model=List[schemas.domain.PlaygroundRequestResponse])
def get_playground_history(id: UUID, db: Session = Depends(get_db)):
    project = ProjectRepository.get_project(db, id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return ProjectRepository.get_playground_history(db, id)
