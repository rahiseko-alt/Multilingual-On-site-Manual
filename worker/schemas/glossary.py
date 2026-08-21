from pydantic import BaseModel, Field

class GlossaryTerm(BaseModel):
    source: str = Field(..., description="Original term to protect or translate")
    translation: dict[str, str] = Field(default_factory=dict, description="Target language mappings, e.g. {'vi': 'nút START', 'id': 'tombol START'}")
    translate: bool = Field(default=True, description="If false, keep original source term untouched across all languages")

class GlossaryData(BaseModel):
    terms: list[GlossaryTerm] = Field(default_factory=list)
