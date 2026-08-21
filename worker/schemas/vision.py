from typing import Literal
from pydantic import BaseModel, Field

class ActionItem(BaseModel):
    actor: str = Field(default="作業者", description="Actor performing the action")
    action: str = Field(..., description="Action name, e.g. 押す, 回す, 投入する")
    target: str = Field(..., description="Target object, e.g. 赤色のボタン, レバー")

class VisionObservation(BaseModel):
    frame_id: str = Field(..., description="Frame ID, e.g. frame_001")
    timestamp: float = Field(..., ge=0.0, description="Exact timestamp in seconds")
    objects: list[str] = Field(default_factory=list, description="Visible objects detected")
    actions: list[ActionItem] = Field(default_factory=list, description="Detected human operations")
    visible_text: list[str] = Field(default_factory=list, description="Visible text/labels")
    uncertain: list[str] = Field(default_factory=list, description="Uncertain or low-confidence observations")
    provider_status: Literal["success", "failed", "unprocessed"] = Field(default="success")

class VisionData(BaseModel):
    observations: list[VisionObservation] = Field(default_factory=list)
