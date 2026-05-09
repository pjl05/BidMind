import uuid
from datetime import datetime

from sqlalchemy import Column, String, BigInteger, Integer, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class AnalysisTask(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "analysis_tasks"

    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    file_name = Column(String(500), nullable=False)
    file_url = Column(String(1000), nullable=False)
    file_size = Column(BigInteger, nullable=True)
    file_hash = Column(String(64), nullable=True, index=True)
    page_count = Column(Integer, nullable=True)

    status = Column(String(20), nullable=False, default="pending", index=True)
    current_agent = Column(String(50), nullable=True)
    progress = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)

    token_used = Column(Integer, default=0)
    llm_cost = Column(String(20), default="0")

    celery_task_id = Column(String(36), nullable=True)
    revision_count = Column(Integer, default=0)

    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)


class FileDedup(Base, TimestampMixin):
    __tablename__ = "file_dedup"

    file_hash = Column(String(64), primary_key=True)
    file_url = Column(String(1000), nullable=False)
    first_task_id = Column(UUID(as_uuid=True), nullable=True)