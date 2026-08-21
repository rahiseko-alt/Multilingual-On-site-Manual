"""
Video2Doc MultiLang - FastAPI Web Application
Provides REST API and serves Web UI for automated video-to-manual generation.
"""
import os
import uuid
import shutil
import asyncio
from typing import List, Optional
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from scripts.run_pipeline import run_video2doc_pipeline

app = FastAPI(
    title="Video2Doc MultiLang API",
    version="1.0.0",
    description="Evidence-first multilingual on-site manual generation system."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STORAGE_DIR = os.path.abspath("storage/jobs")
os.makedirs(STORAGE_DIR, exist_ok=True)

# In-memory job tracker for lightweight status monitoring
jobs_db = {}


class JobStatus(BaseModel):
    job_id: str
    status: str  # pending, processing, completed, failed
    progress: int  # 0 - 100
    message: str
    source_language: str
    target_languages: List[str]
    artifacts: Optional[dict] = None
    error: Optional[str] = None


def execute_pipeline_task(
    job_id: str,
    video_path: str,
    source_lang: str,
    target_langs: List[str],
    use_mock: bool,
):
    job_dir = os.path.join(STORAGE_DIR, job_id)
    try:
        jobs_db[job_id]["status"] = "processing"
        jobs_db[job_id]["progress"] = 20
        jobs_db[job_id]["message"] = "Processing video and extracting evidence..."

        result = run_video2doc_pipeline(
            input_video_path=video_path,
            output_dir=job_dir,
            source_language=source_lang,
            target_languages=target_langs,
            use_mock=use_mock,
        )

        jobs_db[job_id]["status"] = "completed"
        jobs_db[job_id]["progress"] = 100
        jobs_db[job_id]["message"] = "Manual generated successfully!"
        jobs_db[job_id]["artifacts"] = {
            "master_json": f"/api/jobs/{job_id}/artifact/manual_master.json",
            "html": f"/api/jobs/{job_id}/artifact/manual.html",
            "markdown": f"/api/jobs/{job_id}/artifact/manual.md",
            "pdf": f"/api/jobs/{job_id}/artifact/manual.pdf",
            "translations": {
                lang: f"/api/jobs/{job_id}/artifact/manual_{lang}.json"
                for lang in target_langs
            }
        }
    except Exception as e:
        jobs_db[job_id]["status"] = "failed"
        jobs_db[job_id]["error"] = str(e)
        jobs_db[job_id]["message"] = f"Pipeline execution failed: {str(e)}"


@app.get("/health")
def health():
    return {"status": "ok", "service": "video2doc-multilang-api"}


@app.post("/api/jobs/create")
async def create_job(
    background_tasks: BackgroundTasks,
    video: Optional[UploadFile] = File(None),
    use_sample: bool = Form(False),
    source_lang: str = Form("ja"),
    target_langs: str = Form("vi,id"),
    use_mock: bool = Form(True),
):
    job_id = str(uuid.uuid4())
    job_dir = os.path.join(STORAGE_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)

    target_lang_list = [l.strip() for l in target_langs.split(",") if l.strip()]

    video_path = os.path.join(job_dir, "input.mp4")
    if use_sample or video is None:
        sample_path = os.path.abspath("fixtures/sample/sample.mp4")
        if not os.path.exists(sample_path):
            from scripts.generate_sample_media import generate_sample_media
            generate_sample_media("fixtures/sample")
        shutil.copy(sample_path, video_path)
    else:
        with open(video_path, "wb") as f:
            shutil.copyfileobj(video.file, f)

    jobs_db[job_id] = {
        "job_id": job_id,
        "status": "pending",
        "progress": 5,
        "message": "Job queued",
        "source_language": source_lang,
        "target_languages": target_lang_list,
        "artifacts": None,
        "error": None,
    }

    background_tasks.add_task(
        execute_pipeline_task,
        job_id=job_id,
        video_path=video_path,
        source_lang=source_lang,
        target_langs=target_lang_list,
        use_mock=use_mock,
    )

    return {"job_id": job_id, "status": "queued"}


@app.get("/api/jobs/{job_id}", response_model=JobStatus)
def get_job_status(job_id: str):
    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs_db[job_id]


@app.get("/api/jobs/{job_id}/artifact/{filename}")
def get_job_artifact(job_id: str, filename: str):
    file_path = os.path.join(STORAGE_DIR, job_id, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Artifact not found")
    
    media_type = "application/json"
    if filename.endswith(".html"):
        media_type = "text/html"
    elif filename.endswith(".pdf"):
        media_type = "application/pdf"
    elif filename.endswith(".md"):
        media_type = "text/markdown"
    elif filename.endswith(".jpg") or filename.endswith(".jpeg"):
        media_type = "image/jpeg"

    return FileResponse(file_path, media_type=media_type)


# Mount static storage for frames
app.mount("/storage", StaticFiles(directory="storage"), name="storage")

# Mount web UI
WEB_DIR = os.path.abspath("apps/web")
if os.path.exists(WEB_DIR):
    app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="web")
