from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from apps.api.app.db.session import get_db
from apps.api.app.models.tenant import Tenant
from apps.api.app.models.glossary import ExportAsset
from apps.api.app.schemas.glossary import ExportRequest, ExportResponse
from apps.api.app.api.deps import get_current_tenant
from apps.api.app.core.config import settings

router = APIRouter(tags=["exports"])

@router.post("/projects/{project_id}/exports", response_model=ExportResponse)
def create_export(project_id: str, req: ExportRequest, tenant: Tenant = Depends(get_current_tenant), db: Session = Depends(get_db)):
    # Check rendered file existence
    expected_filename = f"manual_{req.language}.{req.format}"
    file_path = Path(settings.LOCAL_STORAGE_PATH) / tenant.id / project_id / expected_filename
    
    export_asset = ExportAsset(
        tenant_id=tenant.id,
        project_id=project_id,
        format=req.format,
        language=req.language,
        storage_path=str(file_path)
    )
    db.add(export_asset)
    db.commit()
    db.refresh(export_asset)

    return ExportResponse(
        export_id=export_asset.id,
        project_id=project_id,
        format=export_asset.format,
        language=export_asset.language,
        download_url=f"/api/exports/{export_asset.id}/download"
    )

@router.get("/exports/{export_id}/download")
def download_export(export_id: str, tenant: Tenant = Depends(get_current_tenant), db: Session = Depends(get_db)):
    export_asset = db.query(ExportAsset).filter(ExportAsset.id == export_id, ExportAsset.tenant_id == tenant.id).first()
    if not export_asset or not Path(export_asset.storage_path).exists():
        raise HTTPException(status_code=404, detail="Export file not found")

    return FileResponse(
        path=export_asset.storage_path,
        filename=Path(export_asset.storage_path).name
    )
