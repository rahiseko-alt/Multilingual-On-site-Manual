from pydantic import BaseModel, Field

class TranscriptSegment(BaseModel):
    id: str = Field(..., description="Unique segment ID, e.g. seg_001")
    start: float = Field(..., ge=0.0, description="Start timestamp in seconds")
    end: float = Field(..., ge=0.0, description="End timestamp in seconds")
    text: str = Field(..., description="Recognized speech text")

class TranscriptData(BaseModel):
    language: str = Field(default="ja", description="Detected or specified audio language")
    segments: list[TranscriptSegment] = Field(default_factory=list)
