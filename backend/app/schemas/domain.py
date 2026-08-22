from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID

# --- PROJECT ---
class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class ProjectResponse(ProjectBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# --- API SPEC ---
class ApiSpecBase(BaseModel):
    version: int = 1
    spec_data: Optional[Dict[str, Any]] = None

class ApiSpecCreate(ApiSpecBase):
    project_id: UUID

class ApiSpecUpdate(BaseModel):
    version: Optional[int] = None
    spec_data: Optional[Dict[str, Any]] = None

class ApiSpecResponse(ApiSpecBase):
    id: UUID
    project_id: UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# --- GENERATED SDK ---
class GeneratedSDKBase(BaseModel):
    version: int = 1
    language: str = "python"
    sdk_code: str
    test_code: Optional[str] = None

class GeneratedSDKCreate(GeneratedSDKBase):
    api_spec_id: UUID

class GeneratedSDKUpdate(BaseModel):
    version: Optional[int] = None
    language: Optional[str] = None
    sdk_code: Optional[str] = None
    test_code: Optional[str] = None

class GeneratedSDKResponse(GeneratedSDKBase):
    id: UUID
    api_spec_id: UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# --- PLAYGROUND REQUEST ---
class PlaygroundRequestBase(BaseModel):
    method: str
    path: str
    base_url: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    request_headers: Optional[Dict[str, str]] = None
    request_body: Optional[Any] = None
    response_status: Optional[int] = None
    response_headers: Optional[Dict[str, str]] = None
    response_body: Optional[Any] = None
    execution_time_ms: Optional[int] = None
    error_message: Optional[str] = None

class PlaygroundRequestCreate(PlaygroundRequestBase):
    project_id: UUID

class PlaygroundRequestUpdate(BaseModel):
    method: Optional[str] = None
    path: Optional[str] = None
    response_status: Optional[int] = None

class PlaygroundRequestResponse(PlaygroundRequestBase):
    id: UUID
    project_id: UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
