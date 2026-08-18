from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, JSON, Uuid, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from .base import Base

class Project(Base):
    __tablename__ = "projects"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, nullable=False, default="Untitled Project")
    description = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    api_specs = relationship("ApiSpec", back_populates="project", cascade="all, delete-orphan")
    playground_requests = relationship("PlaygroundRequest", back_populates="project", cascade="all, delete-orphan")


class ApiSpec(Base):
    __tablename__ = "api_specs"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    project_id = Column(Uuid, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    version = Column(Integer, default=1, nullable=False)
    spec_data = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    project = relationship("Project", back_populates="api_specs")
    generated_sdks = relationship("GeneratedSDK", back_populates="api_spec", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_api_specs_project_id_version", "project_id", "version"),
        UniqueConstraint("project_id", "version", name="uq_api_specs_project_id_version"),
    )


class GeneratedSDK(Base):
    __tablename__ = "generated_sdks"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    api_spec_id = Column(Uuid, ForeignKey("api_specs.id", ondelete="CASCADE"), nullable=False, index=True)
    version = Column(Integer, default=1, nullable=False)
    language = Column(String, nullable=False, default="python")
    sdk_code = Column(Text, nullable=False)
    test_code = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    api_spec = relationship("ApiSpec", back_populates="generated_sdks")

    __table_args__ = (
        Index("ix_generated_sdks_api_spec_id_version", "api_spec_id", "version"),
    )


class PlaygroundRequest(Base):
    __tablename__ = "playground_requests"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    project_id = Column(Uuid, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    method = Column(String, nullable=False)
    path = Column(String, nullable=False)
    base_url = Column(String, nullable=True)
    params = Column(JSON, nullable=True)
    request_headers = Column(JSON, nullable=True)
    request_body = Column(JSON, nullable=True)
    response_status = Column(Integer, nullable=True)
    response_headers = Column(JSON, nullable=True)
    response_body = Column(JSON, nullable=True)
    execution_time_ms = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    project = relationship("Project", back_populates="playground_requests")
