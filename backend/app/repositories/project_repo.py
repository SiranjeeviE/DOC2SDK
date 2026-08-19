import logging
from typing import Any, Dict, List, Optional
from uuid import UUID
from sqlalchemy.orm import Session

from ..models import domain as models
from ..core.sanitizer import sanitize_headers, sanitize_payload

logger = logging.getLogger(__name__)


class ProjectRepository:
    """
    Data repository for Projects, API Specifications, Generated SDKs,
    and Playground Request history.
    """

    @staticmethod
    def list_projects(db: Session) -> List[models.Project]:
        return db.query(models.Project).all()

    @staticmethod
    def get_project(db: Session, project_id: UUID) -> Optional[models.Project]:
        return db.query(models.Project).filter(models.Project.id == project_id).first()

    @staticmethod
    def create_project(db: Session, name: str, description: Optional[str] = None) -> models.Project:
        project = models.Project(name=name, description=description)
        db.add(project)
        db.commit()
        db.refresh(project)
        return project

    @staticmethod
    def update_project(
        db: Session,
        project_id: UUID,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Optional[models.Project]:
        project = db.query(models.Project).filter(models.Project.id == project_id).first()
        if not project:
            return None
        if name is not None:
            project.name = name
        if description is not None:
            project.description = description
        db.commit()
        db.refresh(project)
        return project

    @staticmethod
    def delete_project(db: Session, project_id: UUID) -> bool:
        project = db.query(models.Project).filter(models.Project.id == project_id).first()
        if not project:
            return False
        db.delete(project)
        db.commit()
        return True

    @staticmethod
    def get_specs(db: Session, project_id: UUID) -> List[models.ApiSpec]:
        return (
            db.query(models.ApiSpec)
            .filter(models.ApiSpec.project_id == project_id)
            .order_by(models.ApiSpec.version.desc())
            .all()
        )

    @staticmethod
    def get_spec_by_id(db: Session, spec_id: UUID) -> Optional[models.ApiSpec]:
        return db.query(models.ApiSpec).filter(models.ApiSpec.id == spec_id).first()

    @staticmethod
    def get_latest_spec(db: Session, project_id: UUID) -> Optional[models.ApiSpec]:
        return (
            db.query(models.ApiSpec)
            .filter(models.ApiSpec.project_id == project_id)
            .order_by(models.ApiSpec.version.desc())
            .first()
        )

    @staticmethod
    def get_spec_by_version(db: Session, project_id: UUID, version: int) -> Optional[models.ApiSpec]:
        return (
            db.query(models.ApiSpec)
            .filter(models.ApiSpec.project_id == project_id, models.ApiSpec.version == version)
            .first()
        )

    @staticmethod
    def create_spec(db: Session, project_id: UUID, version: int, spec_data: Dict[str, Any]) -> models.ApiSpec:
        api_spec = models.ApiSpec(
            project_id=project_id,
            version=version,
            spec_data=spec_data,
        )
        db.add(api_spec)
        db.commit()
        db.refresh(api_spec)
        return api_spec

    @staticmethod
    def get_sdks(db: Session, project_id: UUID) -> List[models.GeneratedSDK]:
        return (
            db.query(models.GeneratedSDK)
            .join(models.ApiSpec)
            .filter(models.ApiSpec.project_id == project_id)
            .order_by(models.GeneratedSDK.created_at.desc())
            .all()
        )

    @staticmethod
    def get_sdk_by_id(db: Session, sdk_id: UUID) -> Optional[models.GeneratedSDK]:
        return db.query(models.GeneratedSDK).filter(models.GeneratedSDK.id == sdk_id).first()

    @staticmethod
    def create_sdk(
        db: Session,
        api_spec_id: UUID,
        version: int,
        language: str,
        sdk_code: str,
        test_code: Optional[str] = None,
    ) -> models.GeneratedSDK:
        generated_sdk = models.GeneratedSDK(
            api_spec_id=api_spec_id,
            version=version,
            language=language,
            sdk_code=sdk_code,
            test_code=test_code,
        )
        db.add(generated_sdk)
        db.commit()
        db.refresh(generated_sdk)
        return generated_sdk

    @staticmethod
    def record_playground_request(
        db: Session,
        project_id: UUID,
        method: str,
        path: str,
        base_url: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        request_headers: Optional[Dict[str, Any]] = None,
        request_body: Optional[Any] = None,
        response_status: Optional[int] = None,
        response_headers: Optional[Dict[str, Any]] = None,
        response_body: Optional[Any] = None,
        execution_time_ms: Optional[int] = None,
        error_message: Optional[str] = None,
    ) -> models.PlaygroundRequest:
        play_req = models.PlaygroundRequest(
            project_id=project_id,
            method=method,
            path=path,
            base_url=base_url,
            params=sanitize_payload(params),
            request_headers=sanitize_headers(request_headers),
            request_body=sanitize_payload(request_body),
            response_status=response_status,
            response_headers=sanitize_headers(response_headers),
            response_body=sanitize_payload(response_body),
            execution_time_ms=execution_time_ms,
            error_message=error_message,
        )
        db.add(play_req)
        db.commit()
        db.refresh(play_req)
        return play_req

    @staticmethod
    def get_playground_request(db: Session, request_id: UUID) -> Optional[models.PlaygroundRequest]:
        return (
            db.query(models.PlaygroundRequest)
            .filter(models.PlaygroundRequest.id == request_id)
            .first()
        )

    @staticmethod
    def get_playground_history(db: Session, project_id: UUID) -> List[models.PlaygroundRequest]:
        return (
            db.query(models.PlaygroundRequest)
            .filter(models.PlaygroundRequest.project_id == project_id)
            .order_by(models.PlaygroundRequest.created_at.desc())
            .all()
        )
