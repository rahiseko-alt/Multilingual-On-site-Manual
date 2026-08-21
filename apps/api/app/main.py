from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apps.api.app.core.config import settings
from apps.api.app.db.base import Base
from apps.api.app.db.session import engine

# Import all models to register with Base metadata
import apps.api.app.models.tenant
import apps.api.app.models.project
import apps.api.app.models.job
import apps.api.app.models.manual
import apps.api.app.models.glossary

from apps.api.app.api import auth, projects, video, processing, manuals, translations, glossary, exports

# Initialize database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(projects.router, prefix=settings.API_V1_STR)
app.include_router(video.router, prefix=settings.API_V1_STR)
app.include_router(processing.router, prefix=settings.API_V1_STR)
app.include_router(manuals.router, prefix=settings.API_V1_STR)
app.include_router(translations.router, prefix=settings.API_V1_STR)
app.include_router(glossary.router, prefix=settings.API_V1_STR)
app.include_router(exports.router, prefix=settings.API_V1_STR)

@app.get("/api/health")
def health_check():
    return {"status": "ok", "app": settings.PROJECT_NAME}
