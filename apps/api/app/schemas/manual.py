from datetime import datetime
from pydantic import BaseModel

class ManualUpdateRequest(BaseModel):
    data: dict

class ManualResponse(BaseModel):
    id: str
    project_id: str
    tenant_id: str
    current_version_number: int
    data: dict
    translations: dict
    updated_at: datetime
