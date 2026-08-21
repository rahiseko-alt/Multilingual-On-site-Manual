from pydantic import BaseModel, Field

class SceneItem(BaseModel):
    id: str = Field(..., description="Unique scene ID, e.g. scene_001")
    start: float = Field(..., ge=0.0, description="Start timestamp in seconds")
    end: float = Field(..., ge=0.0, description="End timestamp in seconds")

class SceneData(BaseModel):
    scenes: list[SceneItem] = Field(default_factory=list)
