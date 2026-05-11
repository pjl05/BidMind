from pydantic import BaseModel
from typing import Optional


class CompanyProfileBase(BaseModel):
    company_name: Optional[str] = None
    qualification_types: list[str] = []
    established_years: Optional[int] = None
    has_similar_projects: bool = False
    similar_project_desc: Optional[str] = None
    annual_revenue: Optional[str] = None
    employee_count: Optional[int] = None
    extra_notes: Optional[str] = None


class CompanyProfileCreate(CompanyProfileBase):
    pass


class CompanyProfileUpdate(CompanyProfileBase):
    pass


class CompanyProfileResponse(CompanyProfileBase):
    id: str
    user_id: str

    class Config:
        from_attributes = True