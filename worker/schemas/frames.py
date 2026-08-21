from pydantic import BaseModel, Field

class FrameItem(BaseModel):
    id: str = Field(..., description="Unique frame ID, e.g. frame_001")
    timestamp: float = Field(..., ge=0.0, description="Exact timestamp in seconds")
    path: str = Field(..., description="Relative or absolute path to the extracted image")
    phash: str | None = Field(default=None, description="Perceptual hash string for deduplication")

class FrameData(BaseModel):
    frames: list[FrameItem] = Field(default_factory=list)
