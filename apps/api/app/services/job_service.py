import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy.orm import Session
from apps.api.app.db.session import SessionLocal
from apps.api.app.models.job import ProcessingJob
from apps.api.app.models.manual import Manual
from apps.api.app.models.project import Project, VideoAsset
from apps.api.app.core.config import settings
from scripts.run_pipeline import run_video2doc_pipeline

def execute_pipeline_job(job_id: str):
    db: Session = SessionLocal()
    try:
        job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
        if not job or job.status == "canceled":
            return

        job.status = "validating"
        job.current_stage = "validation"
        job.progress = 10
        job.started_at = datetime.now(timezone.utc)
        db.commit()

        project = db.query(Project).filter(Project.id == job.project_id).first()
        video_asset = db.query(VideoAsset).filter(VideoAsset.project_id == project.id).first()

        if not video_asset or not Path(video_asset.storage_path).exists():
            job.status = "failed"
            job.error = "Source video file not found in storage"
            job.finished_at = datetime.now(timezone.utc)
            db.commit()
            return

        output_dir = Path(settings.LOCAL_STORAGE_PATH) / job.tenant_id / job.project_id
        output_dir.mkdir(parents=True, exist_ok=True)

        # Execute full CLI pipeline in service
        job.status = "processing"
        job.current_stage = "ai_pipeline"
        job.progress = 30
        db.commit()

        target_langs = [l.strip() for l in project.target_languages.split(",") if l.strip()]
        res = run_video2doc_pipeline(
            input_video_path=video_asset.storage_path,
            output_dir=str(output_dir),
            source_language=project.source_language,
            target_languages=target_langs,
            use_mock=True,
            skip_pdf=True
        )

        # Load canonical manual_master.json
        master_json_path = Path(res["manual_master"])
        master_data = json.loads(master_json_path.read_text(encoding="utf-8"))

        translations_data = {}
        for t_lang in target_langs:
            t_path = output_dir / f"manual_{t_lang}.json"
            if t_path.exists():
                translations_data[t_lang] = json.loads(t_path.read_text(encoding="utf-8"))

        # Save or update Manual record
        manual_record = db.query(Manual).filter(Manual.project_id == project.id).first()
        if not manual_record:
            manual_record = Manual(
                tenant_id=job.tenant_id,
                project_id=project.id,
                current_version_number=1,
                data=master_data,
                translations=translations_data
            )
            db.add(manual_record)
        else:
            manual_record.data = master_data
            manual_record.translations = translations_data
            manual_record.current_version_number += 1

        job.status = "completed"
        job.current_stage = "completed"
        job.progress = 100
        job.finished_at = datetime.now(timezone.utc)
        db.commit()

    except Exception as e:
        db.rollback()
        job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
        if job:
            job.status = "failed"
            job.error = str(e)
            job.finished_at = datetime.now(timezone.utc)
            db.commit()
    finally:
        db.close()

def start_background_processing(job_id: str):
    thread = threading.Thread(target=execute_pipeline_job, args=(job_id,), daemon=True)
    thread.start()
