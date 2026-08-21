from datetime import datetime
from pydantic import BaseModel

class ProjectCreate(BaseModel):
    title: str
    source_language: str = "ja"
    target_languages: str = "vi,id"

class ProjectUpdate(BaseModel):
    title: str | None = None
    target_languages: str | None = None

class VideoAssetResponse(BaseModel):
    id: str
    filename: str
    size_mb: float
    duration: float
    has_audio: bool

class ProjectResponse(BaseModel):
    id: str
    tenant_id: str
    title: str
    source_language: str
    target_languages: str
    created_at: datetime
    updated_at: datetime
    video_asset: VideoAssetResponse | None = None
