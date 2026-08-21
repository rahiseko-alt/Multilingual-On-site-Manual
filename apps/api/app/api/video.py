import shutil
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from apps.api.app.db.session import get_db
from apps.api.app.models.tenant import Tenant
from apps.api.app.models.project import Project, VideoAsset
from apps.api.app.schemas.project import VideoAssetResponse
from apps.api.app.api.deps import get_current_tenant
from apps.api.app.core.config import settings
from worker.pipeline.validation import validate_video

router = APIRouter(prefix="/projects", tags=["video"])

@router.post("/{project_id}/video", response_model=VideoAssetResponse)
def upload_video(
    project_id: str,
    file: UploadFile = File(...),
    tenant: Tenant = Depends(get_current_tenant),
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(Project.id == project_id, Project.tenant_id == tenant.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Storage destination
    dest_dir = Path(settings.LOCAL_STORAGE_PATH) / tenant.id / project.id / "source"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_file = dest_dir / (file.filename or "original.mp4")

    with open(dest_file, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        meta = validate_video(str(dest_file))
    except Exception as e:
        dest_file.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=f"Invalid video file: {str(e)}")

    video_asset = db.query(VideoAsset).filter(VideoAsset.project_id == project.id).first()
    if not video_asset:
        video_asset = VideoAsset(
            tenant_id=tenant.id,
            project_id=project.id,
            filename=file.filename or "original.mp4",
            storage_path=str(dest_file),
            size_mb=meta["size_mb"],
            duration=meta["duration"],
            has_audio=meta["has_audio"]
        )
        db.add(video_asset)
    else:
        video_asset.filename = file.filename or "original.mp4"
        video_asset.storage_path = str(dest_file)
        video_asset.size_mb = meta["size_mb"]
        video_asset.duration = meta["duration"]
        video_asset.has_audio = meta["has_audio"]

    db.commit()
    db.refresh(video_asset)
    return video_asset

@router.get("/{project_id}/video", response_model=VideoAssetResponse)
def get_video(project_id: str, tenant: Tenant = Depends(get_current_tenant), db: Session = Depends(get_db)):
    video_asset = db.query(VideoAsset).filter(VideoAsset.project_id == project_id, VideoAsset.tenant_id == tenant.id).first()
    if not video_asset:
        raise HTTPException(status_code=404, detail="Video asset not found")
    return video_asset
