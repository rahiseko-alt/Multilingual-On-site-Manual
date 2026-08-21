from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from apps.api.app.db.session import get_db
from apps.api.app.models.tenant import Tenant
from apps.api.app.models.manual import Manual
from apps.api.app.api.deps import get_current_tenant

router = APIRouter(prefix="/projects", tags=["translations"])

@router.get("/{project_id}/translations/{language}")
def get_translation(project_id: str, language: str, tenant: Tenant = Depends(get_current_tenant), db: Session = Depends(get_db)):
    manual = db.query(Manual).filter(Manual.project_id == project_id, Manual.tenant_id == tenant.id).first()
    if not manual:
        raise HTTPException(status_code=404, detail="Manual not found")
    
    if language not in manual.translations:
        raise HTTPException(status_code=404, detail=f"Translation for '{language}' not found")
    return manual.translations[language]

@router.patch("/{project_id}/translations/{language}")
def update_translation(project_id: str, language: str, req: dict, tenant: Tenant = Depends(get_current_tenant), db: Session = Depends(get_db)):
    manual = db.query(Manual).filter(Manual.project_id == project_id, Manual.tenant_id == tenant.id).first()
    if not manual:
        raise HTTPException(status_code=404, detail="Manual not found")

    translations = dict(manual.translations)
    translations[language] = req
    manual.translations = translations
    db.commit()
    return {"message": f"Translation for '{language}' updated successfully"}
