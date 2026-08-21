import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from apps.api.app.db.base import Base

class Glossary(Base):
    __tablename__ = "glossaries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), unique=True, nullable=False)
    
    project: Mapped["Project"] = relationship("Project", back_populates="glossary")
    terms: Mapped[list["GlossaryTerm"]] = relationship("GlossaryTerm", back_populates="glossary", cascade="all, delete-orphan")

class GlossaryTerm(Base):
    __tablename__ = "glossary_terms"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    glossary_id: Mapped[str] = mapped_column(String(36), ForeignKey("glossaries.id", ondelete="CASCADE"), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    translations: Mapped[dict] = mapped_column(JSON, default=dict) # {"vi": "...", "id": "..."}
    translate: Mapped[bool] = mapped_column(Boolean, default=True)

    glossary: Mapped["Glossary"] = relationship("Glossary", back_populates="terms")

class ExportAsset(Base):
    __tablename__ = "export_assets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(36), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    format: Mapped[str] = mapped_column(String(10), nullable=False) # html, md, pdf
    language: Mapped[str] = mapped_column(String(10), nullable=False) # ja, vi, id
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
