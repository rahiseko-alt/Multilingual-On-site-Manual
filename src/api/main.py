"""
FastAPI Backend for Manga Character Extraction and Animation Export.
"""
import os
import shutil
import uuid
from typing import List, Optional, Tuple
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from src.core.pipeline import MangaSeparationPipeline, CharacterTarget

app = FastAPI(
    title="Manga Character Separation & Animation Pipeline API",
    version="1.0.0",
    description="API for extracting characters from manga panels and exporting for animation tools."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = os.path.abspath("storage/uploads")
OUTPUT_DIR = os.path.abspath("storage/outputs")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

app.mount("/static/outputs", StaticFiles(directory=OUTPUT_DIR), name="outputs")

pipeline = MangaSeparationPipeline()


class CharacterSpec(BaseModel):
    name: str
    box: Optional[Tuple[int, int, int, int]] = None
    points: Optional[List[Tuple[int, int]]] = None
    point_labels: Optional[List[int]] = None
    prompt: Optional[str] = None


class SeparationRequest(BaseModel):
    file_id: str
    panel_id: str = "panel_01"
    characters: List[CharacterSpec]
    generate_bg: bool = True
    crop_characters: bool = False


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "manga-separation-api"}


@app.post("/api/upload")
async def upload_image(file: UploadFile = File(...)):
    ext = os.path.splitext(file.filename)[1] or ".png"
    file_id = str(uuid.uuid4())
    filename = f"{file_id}{ext}"
    dest_path = os.path.join(UPLOAD_DIR, filename)

    with open(dest_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {
        "file_id": file_id,
        "filename": filename,
        "path": dest_path
    }


@app.post("/api/separate-panel")
async def separate_panel(req: SeparationRequest):
    # Locate file
    matched_files = [f for f in os.listdir(UPLOAD_DIR) if f.startswith(req.file_id)]
    if not matched_files:
        raise HTTPException(status_code=404, detail="Uploaded image not found")

    image_path = os.path.join(UPLOAD_DIR, matched_files[0])
    session_out_dir = os.path.join(OUTPUT_DIR, req.file_id)

    targets = [
        CharacterTarget(
            name=c.name,
            points=c.points,
            point_labels=c.point_labels,
            box=c.box,
            prompt=c.prompt,
        )
        for c in req.characters
    ]

    result = pipeline.process(
        image_path=image_path,
        targets=targets,
        output_dir=session_out_dir,
        panel_id=req.panel_id,
        generate_bg=req.generate_bg,
        crop_characters=req.crop_characters,
    )

    # Build relative URLs
    char_urls = {
        name: f"/static/outputs/{req.file_id}/{os.path.basename(path)}"
        for name, path in result.character_paths.items()
    }
    bg_url = f"/static/outputs/{req.file_id}/{os.path.basename(result.clean_plate_path)}" if result.clean_plate_path else None
    manifest_url = f"/static/outputs/{req.file_id}/{os.path.basename(result.manifest_path)}"

    return {
        "panel_id": req.panel_id,
        "clean_background_url": bg_url,
        "characters": char_urls,
        "manifest_url": manifest_url,
        "ready_for": ["Cartoon Animator 5", "Adobe After Effects", "Spine 2D"]
    }
