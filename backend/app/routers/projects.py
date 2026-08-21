import logging
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Response, UploadFile, File, Form
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from .. import schemas
from ..core.auth import require_auth
from ..core.database import get_db, SessionLocal
from ..core.rate_limiter import rate_limit_ai
from ..core.url_validator import validate_url, URLValidationError
from ..services.diff import SpecDiffService
from ..services.pipeline import PipelineService
from ..repositories.project_repo import ProjectRepository
from ..models import domain as models
from ..parsers.openapi import NormalizedAPISpec

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects", tags=["projects"])
pipeline_service = PipelineService()


class WorkspaceStatsResponse(BaseModel):
    total_projects: int
    total_sdks: int
    total_endpoints: int
    total_api_calls: int


class ProjectCreateRequest(schemas.domain.ProjectCreate):
    source_url: str

    @field_validator("source_url")
    @classmethod
    def validate_source_url(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("source_url cannot be empty")
        return v.strip()


class RescrapeRequest(BaseModel):
    source_url: str

    @field_validator("source_url")
    @classmethod
    def validate_source_url(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("source_url cannot be empty")
        return v.strip()


class RegenerateSDKRequest(BaseModel):
    language: str = "python"
    spec_id: Optional[UUID] = None


def _decode_content(content: bytes) -> str:
    try:
        return content.decode("utf-8")
    except UnicodeDecodeError:
        try:
            return content.decode("latin-1")
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="Uploaded file is not valid UTF-8 or text.")


async def process_project_background(project_id: UUID, source_url: str):
    db = SessionLocal()
    try:
        project = ProjectRepository.get_project(db, project_id)
        if not project:
            return

        # 1. Scrape & Parse
        spec, spec_dict = await pipeline_service.scrape_and_parse(source_url)

        # 2. Determine next spec version
        latest_spec = ProjectRepository.get_latest_spec(db, project.id)
        next_version = (latest_spec.version + 1) if latest_spec else 1

        # 3. Create ApiSpec
        api_spec = ProjectRepository.create_spec(
            db=db,
            project_id=project.id,
            version=next_version,
            spec_data=spec_dict,
        )

        # 4. Generate SDK & Tests
        sdk_code, test_code = pipeline_service.generate_sdk_and_tests(spec, "python")

        # 5. Create GeneratedSDK
        ProjectRepository.create_sdk(
            db=db,
            api_spec_id=api_spec.id,
            version=1,
            language="python",
            sdk_code=sdk_code,
            test_code=test_code,
        )

    except Exception as e:
        logger.exception("Background task failed for project %s: %s", project_id, e)
    finally:
        db.close()


@router.post("", response_model=schemas.domain.ProjectResponse)
async def create_project(
    request: ProjectCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _auth: bool = Depends(require_auth),
    _rate: None = Depends(rate_limit_ai),
):
    try:
        validate_url(request.source_url)
    except URLValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

    project = ProjectRepository.create_project(
        db=db,
        name=request.name,
        description=request.description or request.source_url,
    )

    background_tasks.add_task(process_project_background, project.id, request.source_url)
    return project


@router.get("", response_model=List[schemas.domain.ProjectResponse])
def get_projects(db: Session = Depends(get_db)):
    return ProjectRepository.list_projects(db)


@router.get("/stats/overview", response_model=WorkspaceStatsResponse)
def get_workspace_stats(db: Session = Depends(get_db)):
    total_projects = db.query(models.Project).count()
    total_sdks = db.query(models.GeneratedSDK).count()
    total_api_calls = db.query(models.PlaygroundRequest).count()

    total_endpoints = 0
    projects = db.query(models.Project).all()
    for p in projects:
        latest = ProjectRepository.get_latest_spec(db, p.id)
        if latest and latest.spec_data and isinstance(latest.spec_data, dict):
            eps = latest.spec_data.get("endpoints", [])
            if isinstance(eps, list):
                total_endpoints += len(eps)

    return WorkspaceStatsResponse(
        total_projects=total_projects,
        total_sdks=total_sdks,
        total_endpoints=total_endpoints,
        total_api_calls=total_api_calls,
    )


@router.get("/{id}", response_model=schemas.domain.ProjectResponse)
def get_project(id: UUID, db: Session = Depends(get_db)):
    project = ProjectRepository.get_project(db, id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.delete("/{id}", status_code=204)
def delete_project(
    id: UUID,
    db: Session = Depends(get_db),
    _auth: bool = Depends(require_auth),
):
    success = ProjectRepository.delete_project(db, id)
    if not success:
        raise HTTPException(status_code=404, detail="Project not found")


@router.put("/{id}", response_model=schemas.domain.ProjectResponse)
@router.patch("/{id}", response_model=schemas.domain.ProjectResponse)
def update_project(
    id: UUID,
    request: schemas.domain.ProjectUpdate,
    db: Session = Depends(get_db),
    _auth: bool = Depends(require_auth),
):
    project = ProjectRepository.get_project(db, id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    name = None
    if request.name is not None:
        name = request.name.strip()
        if not name:
            raise HTTPException(status_code=400, detail="Project name cannot be empty")

    desc = request.description.strip() if request.description else None

    return ProjectRepository.update_project(
        db=db,
        project_id=id,
        name=name,
        description=desc,
    )


@router.get("/{id}/specs", response_model=List[schemas.domain.ApiSpecResponse])
def get_project_specs(id: UUID, db: Session = Depends(get_db)):
    project = ProjectRepository.get_project(db, id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectRepository.get_specs(db, id)


@router.get("/{id}/specs/{spec_id}", response_model=schemas.domain.ApiSpecResponse)
def get_project_spec(id: UUID, spec_id: UUID, db: Session = Depends(get_db)):
    spec = ProjectRepository.get_spec_by_id(db, spec_id)
    if not spec or spec.project_id != id:
        raise HTTPException(status_code=404, detail="ApiSpec not found")
    return spec


@router.post("/{id}/rescrape", status_code=202)
async def rescrape_project(
    id: UUID,
    request: RescrapeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _auth: bool = Depends(require_auth),
    _rate: None = Depends(rate_limit_ai),
):
    project = ProjectRepository.get_project(db, id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        validate_url(request.source_url)
    except URLValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

    background_tasks.add_task(process_project_background, project.id, request.source_url)
    return {"message": "Rescrape triggered successfully"}


@router.post("/{id}/regenerate-sdk", response_model=schemas.domain.GeneratedSDKResponse)
def regenerate_sdk(
    id: UUID,
    request: RegenerateSDKRequest,
    db: Session = Depends(get_db),
    _auth: bool = Depends(require_auth),
    _rate: None = Depends(rate_limit_ai),
):
    project = ProjectRepository.get_project(db, id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if request.spec_id:
        spec = ProjectRepository.get_spec_by_id(db, request.spec_id)
        if not spec or spec.project_id != id:
            raise HTTPException(status_code=404, detail="ApiSpec not found")
    else:
        spec = ProjectRepository.get_latest_spec(db, id)
        if not spec:
            raise HTTPException(status_code=404, detail="No ApiSpec found for project")

    try:
        normalized_spec = NormalizedAPISpec(**spec.spec_data)
        sdk_code, test_code = pipeline_service.generate_sdk_and_tests(normalized_spec, language=request.language)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to generate SDK or tests: {str(e)}")

    existing_sdks = ProjectRepository.get_sdks(db, id)
    next_version = len(existing_sdks) + 1

    return ProjectRepository.create_sdk(
        db=db,
        api_spec_id=spec.id,
        version=next_version,
        language=request.language,
        sdk_code=sdk_code,
        test_code=test_code,
    )


@router.get("/{id}/sdk/{sdk_id}/download")
def download_sdk(id: UUID, sdk_id: UUID, db: Session = Depends(get_db)):
    project = ProjectRepository.get_project(db, id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    sdk = ProjectRepository.get_sdk_by_id(db, sdk_id)
    if not sdk or sdk.api_spec.project_id != id:
        raise HTTPException(status_code=404, detail="SDK not found")

    extension = "ts" if sdk.language.lower() in ["typescript", "ts"] else "py"
    filename = f"{project.name.replace(' ', '_').lower()}_sdk_v{sdk.version}.{extension}"

    return Response(
        content=sdk.sdk_code,
        media_type="text/plain",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/{id}/sdk/{sdk_id}/download-tests")
def download_tests(id: UUID, sdk_id: UUID, db: Session = Depends(get_db)):
    project = ProjectRepository.get_project(db, id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    sdk = ProjectRepository.get_sdk_by_id(db, sdk_id)
    if not sdk or sdk.api_spec.project_id != id or not sdk.test_code:
        raise HTTPException(status_code=404, detail="Test suite not found for this SDK")

    extension = "ts" if sdk.language.lower() in ["typescript", "ts"] else "py"
    filename = f"test_{project.name.replace(' ', '_').lower()}_v{sdk.version}.{extension}"

    return Response(
        content=sdk.test_code,
        media_type="text/plain",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/{id}/sdks", response_model=List[schemas.domain.GeneratedSDKResponse])
def get_project_sdks(id: UUID, db: Session = Depends(get_db)):
    project = ProjectRepository.get_project(db, id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectRepository.get_sdks(db, id)


# --- FILE UPLOAD & CHANGE MONITORING ENDPOINTS ---

@router.post("/upload", response_model=schemas.domain.ProjectResponse)
async def upload_project(
    file: UploadFile = File(...),
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    _auth: bool = Depends(require_auth),
    _rate: None = Depends(rate_limit_ai),
):
    content = await file.read(10 * 1024 * 1024 + 1)
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File size exceeds maximum limit of 10MB")

    text = _decode_content(content)
    spec, format_type = pipeline_service.parse_uploaded_content(text, file.filename or "")
    spec_dict = spec.model_dump() if hasattr(spec, "model_dump") else spec.dict()
    spec_dict["source"] = f"upload_{format_type}"
    spec_dict["is_mock"] = False

    project_name = (name or "").strip() or spec.name or file.filename or "Uploaded Project"
    project_desc = (description or "").strip() or spec.description or f"Imported from {file.filename or 'file'}"

    project = ProjectRepository.create_project(db=db, name=project_name, description=project_desc)
    api_spec = ProjectRepository.create_spec(db=db, project_id=project.id, version=1, spec_data=spec_dict)

    sdk_code, test_code = pipeline_service.generate_sdk_and_tests(spec, "python")
    ProjectRepository.create_sdk(
        db=db,
        api_spec_id=api_spec.id,
        version=1,
        language="python",
        sdk_code=sdk_code,
        test_code=test_code,
    )

    db.refresh(project)
    return project


@router.post("/{id}/upload-spec", response_model=schemas.domain.ApiSpecResponse)
async def upload_project_spec(
    id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _auth: bool = Depends(require_auth),
    _rate: None = Depends(rate_limit_ai),
):
    project = ProjectRepository.get_project(db, id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    content = await file.read(10 * 1024 * 1024 + 1)
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File size exceeds maximum limit of 10MB")

    text = _decode_content(content)
    spec, format_type = pipeline_service.parse_uploaded_content(text, file.filename or "")
    spec_dict = spec.model_dump() if hasattr(spec, "model_dump") else spec.dict()
    spec_dict["source"] = f"upload_{format_type}"
    spec_dict["is_mock"] = False

    latest_spec = ProjectRepository.get_latest_spec(db, project.id)
    next_version = (latest_spec.version + 1) if latest_spec else 1

    api_spec = ProjectRepository.create_spec(
        db=db,
        project_id=project.id,
        version=next_version,
        spec_data=spec_dict,
    )

    sdk_code, test_code = pipeline_service.generate_sdk_and_tests(spec, "python")
    ProjectRepository.create_sdk(
        db=db,
        api_spec_id=api_spec.id,
        version=next_version,
        language="python",
        sdk_code=sdk_code,
        test_code=test_code,
    )

    return api_spec


@router.get("/{id}/diff")
def get_project_diff(
    id: UUID,
    from_version: Optional[int] = None,
    to_version: Optional[int] = None,
    db: Session = Depends(get_db),
):
    project = ProjectRepository.get_project(db, id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    specs = sorted(ProjectRepository.get_specs(db, id), key=lambda s: s.version)
    if not specs:
        raise HTTPException(status_code=404, detail="No specifications found for project")

    if len(specs) < 2 and (from_version is None or to_version is None):
        return {
            "has_breaking_changes": False,
            "breaking_count": 0,
            "non_breaking_count": 0,
            "total_changes": 0,
            "changes": [],
            "summary": "Only one specification version exists. Rescrape or upload a new version to compare changes.",
            "from_version": specs[0].version,
            "to_version": specs[0].version
        }

    if from_version is None or to_version is None:
        old_spec_obj = specs[-2]
        new_spec_obj = specs[-1]
    else:
        old_spec_obj = next((s for s in specs if s.version == from_version), None)
        new_spec_obj = next((s for s in specs if s.version == to_version), None)
        if not old_spec_obj or not new_spec_obj:
            raise HTTPException(status_code=404, detail="Specified specification versions not found")

    report = SpecDiffService.compare_specs(old_spec_obj.spec_data or {}, new_spec_obj.spec_data or {})
    report["from_version"] = old_spec_obj.version
    report["to_version"] = new_spec_obj.version
    return report


@router.post("/{id}/check-changes")
async def check_api_changes(
    id: UUID,
    db: Session = Depends(get_db),
    _auth: bool = Depends(require_auth),
    _rate: None = Depends(rate_limit_ai),
):
    project = ProjectRepository.get_project(db, id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    source_url = project.description
    if not source_url or not (source_url.startswith("http://") or source_url.startswith("https://")):
        raise HTTPException(
            status_code=400,
            detail="Project does not have an active documentation URL to monitor. Please use upload-spec to add new versions."
        )

    try:
        new_spec, new_spec_dict = await pipeline_service.scrape_and_parse(source_url)
    except URLValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

    latest_spec = ProjectRepository.get_latest_spec(db, project.id)
    if not latest_spec:
        ProjectRepository.create_spec(db=db, project_id=project.id, version=1, spec_data=new_spec_dict)
        return {
            "has_breaking_changes": False,
            "breaking_count": 0,
            "non_breaking_count": 0,
            "total_changes": 0,
            "changes": [],
            "summary": "Initial specification version established.",
            "from_version": 1,
            "to_version": 1,
            "new_version_created": False
        }

    report = SpecDiffService.compare_specs(latest_spec.spec_data or {}, new_spec_dict)
    report["from_version"] = latest_spec.version

    if report["total_changes"] > 0:
        next_version = latest_spec.version + 1
        api_spec = ProjectRepository.create_spec(
            db=db,
            project_id=project.id,
            version=next_version,
            spec_data=new_spec_dict,
        )

        sdk_code, test_code = pipeline_service.generate_sdk_and_tests(new_spec, "python")
        ProjectRepository.create_sdk(
            db=db,
            api_spec_id=api_spec.id,
            version=next_version,
            language="python",
            sdk_code=sdk_code,
            test_code=test_code,
        )

        report["new_version_created"] = True
        report["to_version"] = next_version
    else:
        report["new_version_created"] = False
        report["to_version"] = latest_spec.version

    return report


async def check_api_changes_background(project_id: UUID):
    db = SessionLocal()
    try:
        project = ProjectRepository.get_project(db, project_id)
        if not project:
            return
        source_url = project.description
        if not source_url or not (source_url.startswith("http://") or source_url.startswith("https://")):
            return

        new_spec, new_spec_dict = await pipeline_service.scrape_and_parse(source_url)
        latest_spec = ProjectRepository.get_latest_spec(db, project.id)
        if latest_spec:
            report = SpecDiffService.compare_specs(latest_spec.spec_data or {}, new_spec_dict)
            if report["total_changes"] > 0:
                next_version = latest_spec.version + 1
                api_spec = ProjectRepository.create_spec(
                    db=db,
                    project_id=project.id,
                    version=next_version,
                    spec_data=new_spec_dict,
                )

                sdk_code, test_code = pipeline_service.generate_sdk_and_tests(new_spec, "python")
                ProjectRepository.create_sdk(
                    db=db,
                    api_spec_id=api_spec.id,
                    version=next_version,
                    language="python",
                    sdk_code=sdk_code,
                    test_code=test_code,
                )
                logger.info("Background change check created version %d for project %s: %s", next_version, project_id, report["summary"])
    except Exception as e:
        logger.exception("Background change check failed for project %s: %s", project_id, e)
    finally:
        db.close()
