from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from apps.api.app.db.session import get_db
from apps.api.app.models.tenant import Tenant
from apps.api.app.models.project import Project, VideoAsset
from apps.api.app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse
from apps.api.app.api.deps import get_current_tenant

router = APIRouter(prefix="/projects", tags=["projects"])

@router.get("", response_model=list[ProjectResponse])
def list_projects(tenant: Tenant = Depends(get_current_tenant), db: Session = Depends(get_db)):
    projects = db.query(Project).filter(Project.tenant_id == tenant.id).all()
    return projects

@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(req: ProjectCreate, tenant: Tenant = Depends(get_current_tenant), db: Session = Depends(get_db)):
    project = Project(
        tenant_id=tenant.id,
        title=req.title,
        source_language=req.source_language,
        target_languages=req.target_languages
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project

@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: str, tenant: Tenant = Depends(get_current_tenant), db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id, Project.tenant_id == tenant.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.patch("/{project_id}", response_model=ProjectResponse)
def update_project(project_id: str, req: ProjectUpdate, tenant: Tenant = Depends(get_current_tenant), db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id, Project.tenant_id == tenant.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if req.title is not None:
        project.title = req.title
    if req.target_languages is not None:
        project.target_languages = req.target_languages
    db.commit()
    db.refresh(project)
    return project

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: str, tenant: Tenant = Depends(get_current_tenant), db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id, Project.tenant_id == tenant.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(project)
    db.commit()
    return None
