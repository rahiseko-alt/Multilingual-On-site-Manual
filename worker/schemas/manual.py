from typing import Literal
from pydantic import BaseModel, Field

class StepMedia(BaseModel):
    primary_frame_id: str | None = Field(default=None, description="Main illustration frame ID for the step")
    additional_frame_ids: list[str] = Field(default_factory=list, description="Supplemental frame IDs")

class StepEvidence(BaseModel):
    video_start: float = Field(..., ge=0.0, description="Start timestamp in seconds")
    video_end: float = Field(..., ge=0.0, description="End timestamp in seconds")
    transcript_ids: list[str] = Field(default_factory=list, description="Referenced transcript segment IDs")
    frame_ids: list[str] = Field(default_factory=list, description="Referenced visual frame IDs")

class ManualStep(BaseModel):
    step_id: str = Field(..., description="Unique step ID, e.g. step_001")
    order: int = Field(..., ge=1, description="Sequential order starting from 1")
    title: str = Field(..., description="Short summary title of the action")
    instruction: str = Field(..., description="Detailed operational instruction")
    warning: str | None = Field(default=None, description="Explicit warning if verified by evidence")
    equipment: list[str] = Field(default_factory=list, description="Identified equipment, buttons, tools")
    media: StepMedia = Field(default_factory=StepMedia)
    evidence: StepEvidence
    evidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    status: Literal["generated", "needs_review", "reviewed"] = Field(default="generated")

class ManualMeta(BaseModel):
    title: str = Field(default="作業手順マニュアル", description="Title of the manual")
    source_language: str = Field(default="ja", description="Original language of the manual")
    steps: list[ManualStep] = Field(default_factory=list)

class ManualMaster(BaseModel):
    schema_version: str = Field(default="1.0")
    manual: ManualMeta

class TranslatedStep(BaseModel):
    step_id: str
    order: int
    title: str
    instruction: str
    warning: str | None = None
    description: str | None = None
    equipment: list[str] = Field(default_factory=list)
    media: StepMedia = Field(default_factory=StepMedia)
    evidence: StepEvidence
    evidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    status: Literal["generated", "needs_review", "reviewed"] = Field(default="generated")

class TranslatedManual(BaseModel):
    title: str
    source_language: str
    target_language: str
    steps: list[TranslatedStep]
