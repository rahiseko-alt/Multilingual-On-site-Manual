from datetime import datetime
from pydantic import BaseModel

class JobResponse(BaseModel):
    job_id: str
    project_id: str
    tenant_id: str
    status: str
    progress: int
    current_stage: str | None = None
    error: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
