from pydantic import BaseModel, Field
from worker.schemas.vision import ActionItem

class AudioEvidence(BaseModel):
    segment_ids: list[str] = Field(default_factory=list)
    text: str = Field(default="")

class VisionEvidence(BaseModel):
    frame_ids: list[str] = Field(default_factory=list)
    objects: list[str] = Field(default_factory=list)
    actions: list[ActionItem] = Field(default_factory=list)

class EvidenceItem(BaseModel):
    id: str = Field(..., description="Unique evidence ID, e.g. ev_001")
    start: float = Field(..., ge=0.0, description="Start timestamp in seconds")
    end: float = Field(..., ge=0.0, description="End timestamp in seconds")
    audio: AudioEvidence = Field(default_factory=AudioEvidence)
    vision: VisionEvidence = Field(default_factory=VisionEvidence)
    evidence_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Confidence score based on cross-modal verification")

class EvidenceData(BaseModel):
    items: list[EvidenceItem] = Field(default_factory=list)
