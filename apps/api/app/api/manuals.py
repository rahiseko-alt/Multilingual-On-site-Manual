from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from apps.api.app.db.session import get_db
from apps.api.app.models.tenant import Tenant
from apps.api.app.models.manual import Manual, ManualVersion
from apps.api.app.schemas.manual import ManualResponse, ManualUpdateRequest
from apps.api.app.api.deps import get_current_tenant

router = APIRouter(prefix="/projects", tags=["manuals"])

@router.get("/{project_id}/manual", response_model=ManualResponse)
def get_manual(project_id: str, tenant: Tenant = Depends(get_current_tenant), db: Session = Depends(get_db)):
    manual = db.query(Manual).filter(Manual.project_id == project_id, Manual.tenant_id == tenant.id).first()
    if not manual:
        raise HTTPException(status_code=404, detail="Manual not found for this project")
    return manual

@router.patch("/{project_id}/manual", response_model=ManualResponse)
def update_manual(project_id: str, req: ManualUpdateRequest, tenant: Tenant = Depends(get_current_tenant), db: Session = Depends(get_db)):
    manual = db.query(Manual).filter(Manual.project_id == project_id, Manual.tenant_id == tenant.id).first()
    if not manual:
        raise HTTPException(status_code=404, detail="Manual not found")

    # Create new version history
    version = ManualVersion(
        manual_id=manual.id,
        version_number=manual.current_version_number,
        note="User edit",
        data=manual.data
    )
    db.add(version)

    manual.data = req.data
    manual.current_version_number += 1
    db.commit()
    db.refresh(manual)
    return manual
