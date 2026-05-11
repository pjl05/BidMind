from sqlalchemy import Column, String, Integer, Boolean, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.sql import func
import uuid

from app.models.base import Base


class CompanyProfile(Base):
    __tablename__ = "company_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), unique=True, nullable=False)
    company_name = Column(String(200), nullable=True)
    qualification_types = Column(ARRAY(Text), nullable=True)
    established_years = Column(Integer, nullable=True)
    has_similar_projects = Column(Boolean, default=False)
    similar_project_desc = Column(Text, nullable=True)
    annual_revenue = Column(String(50), nullable=True)
    employee_count = Column(Integer, nullable=True)
    extra_notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())