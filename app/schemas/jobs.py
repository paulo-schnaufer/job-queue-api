from datetime import datetime
from typing import Any

from pydantic import BaseModel


class JobCreate(BaseModel):
    payload: dict[str, Any]


class JobCreated(BaseModel):
    job_id: int
    status: str


class JobResponse(BaseModel):
    id: int
    client_id: int
    status: str
    payload: dict[str, Any]
    result: str | None = None
    created_at: datetime
    updated_at: datetime | None = None
