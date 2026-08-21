from pydantic import BaseModel

class TermCreate(BaseModel):
    source: str
    translations: dict[str, str] = {}
    translate: bool = True

class TermUpdate(BaseModel):
    source: str | None = None
    translations: dict[str, str] | None = None
    translate: bool | None = None

class TermResponse(BaseModel):
    id: str
    source: str
    translations: dict
    translate: bool

class GlossaryResponse(BaseModel):
    id: str
    project_id: str
    terms: list[TermResponse] = []

class ExportRequest(BaseModel):
    format: str # html, md, pdf
    language: str = "ja"

class ExportResponse(BaseModel):
    export_id: str
    project_id: str
    format: str
    language: str
    download_url: str
