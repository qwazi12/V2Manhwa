"""Runtime response contract for the implemented local slice."""
from datetime import datetime
from typing import Literal, Any
from pydantic import BaseModel, ConfigDict

class BudgetResponse(BaseModel):
    model_config = ConfigDict(extra='forbid')
    job_id: str
    reserved_units: int
    settled_units: int | None

class EventResponse(BaseModel):
    model_config = ConfigDict(extra='forbid')
    id: str
    job_id: str
    kind: str
    detail: dict[str, Any]
    created_at: datetime

class JobResponse(BaseModel):
    model_config = ConfigDict(extra='forbid')
    id: str
    title: str
    state: Literal['QUEUED', 'RUNNING', 'REVIEW', 'CANCELLED', 'FAILED']
    revision: int
    attempt: int
    artifact_sha: str | None
    error: str | None
    created_at: datetime
    events: list[EventResponse]
    budget: BudgetResponse

class IdentityResponse(BaseModel):
    role: Literal['owner']
    csrf: str
    mode: Literal['local-studio']

class PreviewResponse(BaseModel):
    url: str
    sha256: str
    expires_at: int
