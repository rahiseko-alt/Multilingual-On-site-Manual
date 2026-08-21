from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from apps.api.app.db.session import get_db
from apps.api.app.models.tenant import Tenant
from apps.api.app.models.project import Project, VideoAsset
from apps.api.app.models.job import ProcessingJob
from apps.api.app.schemas.job import JobResponse
from apps.api.app.api.deps import get_current_tenant
from apps.api.app.services.job_service import start_background_processing

router = APIRouter(tags=["processing"])

@router.post("/projects/{project_id}/process", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED)
def process_project(project_id: str, tenant: Tenant = Depends(get_current_tenant), db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id, Project.tenant_id == tenant.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    video = db.query(VideoAsset).filter(VideoAsset.project_id == project.id).first()
    if not video:
        raise HTTPException(status_code=400, detail="Cannot process project without video uploaded")

    job = ProcessingJob(
        tenant_id=tenant.id,
        project_id=project.id,
        status="queued",
        progress=0
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Start background AI pipeline worker
    start_background_processing(job.id)

    return JobResponse(
        job_id=job.id,
        project_id=job.project_id,
        tenant_id=job.tenant_id,
        status=job.status,
        progress=job.progress,
        current_stage=job.current_stage,
        error=job.error,
        created_at=job.created_at,
        started_at=job.started_at,
        finished_at=job.finished_at
    )

@router.get("/jobs/{job_id}", response_model=JobResponse)
def get_job(job_id: str, tenant: Tenant = Depends(get_current_tenant), db: Session = Depends(get_db)):
    job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id, ProcessingJob.tenant_id == tenant.id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return JobResponse(
        job_id=job.id,
        project_id=job.project_id,
        tenant_id=job.tenant_id,
        status=job.status,
        progress=job.progress,
        current_stage=job.current_stage,
        error=job.error,
        created_at=job.created_at,
        started_at=job.started_at,
        finished_at=job.finished_at
    )

@router.post("/jobs/{job_id}/cancel")
def cancel_job(job_id: str, tenant: Tenant = Depends(get_current_tenant), db: Session = Depends(get_db)):
    job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id, ProcessingJob.tenant_id == tenant.id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status not in ["completed", "failed"]:
        job.status = "canceled"
        db.commit()
    return {"message": "Job canceled"}
