from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from apps.api.app.db.session import get_db
from apps.api.app.models.tenant import Tenant
from apps.api.app.models.glossary import Glossary, GlossaryTerm
from apps.api.app.schemas.glossary import GlossaryResponse, TermCreate, TermUpdate, TermResponse
from apps.api.app.api.deps import get_current_tenant

router = APIRouter(tags=["glossary"])

@router.get("/projects/{project_id}/glossary", response_model=GlossaryResponse)
def get_project_glossary(project_id: str, tenant: Tenant = Depends(get_current_tenant), db: Session = Depends(get_db)):
    glossary = db.query(Glossary).filter(Glossary.project_id == project_id, Glossary.tenant_id == tenant.id).first()
    if not glossary:
        glossary = Glossary(tenant_id=tenant.id, project_id=project_id)
        db.add(glossary)
        db.commit()
        db.refresh(glossary)
    return glossary

@router.post("/projects/{project_id}/glossary", response_model=TermResponse, status_code=status.HTTP_201_CREATED)
def add_glossary_term(project_id: str, req: TermCreate, tenant: Tenant = Depends(get_current_tenant), db: Session = Depends(get_db)):
    glossary = db.query(Glossary).filter(Glossary.project_id == project_id, Glossary.tenant_id == tenant.id).first()
    if not glossary:
        glossary = Glossary(tenant_id=tenant.id, project_id=project_id)
        db.add(glossary)
        db.commit()
        db.refresh(glossary)

    term = GlossaryTerm(
        glossary_id=glossary.id,
        source=req.source,
        translations=req.translations,
        translate=req.translate
    )
    db.add(term)
    db.commit()
    db.refresh(term)
    return term

@router.patch("/glossary/{term_id}", response_model=TermResponse)
def update_glossary_term(term_id: str, req: TermUpdate, tenant: Tenant = Depends(get_current_tenant), db: Session = Depends(get_db)):
    term = db.query(GlossaryTerm).join(Glossary).filter(GlossaryTerm.id == term_id, Glossary.tenant_id == tenant.id).first()
    if not term:
        raise HTTPException(status_code=404, detail="Glossary term not found")
    if req.source is not None:
        term.source = req.source
    if req.translations is not None:
        term.translations = req.translations
    if req.translate is not None:
        term.translate = req.translate
    db.commit()
    db.refresh(term)
    return term

@router.delete("/glossary/{term_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_glossary_term(term_id: str, tenant: Tenant = Depends(get_current_tenant), db: Session = Depends(get_db)):
    term = db.query(GlossaryTerm).join(Glossary).filter(GlossaryTerm.id == term_id, Glossary.tenant_id == tenant.id).first()
    if not term:
        raise HTTPException(status_code=404, detail="Glossary term not found")
    db.delete(term)
    db.commit()
    return None
