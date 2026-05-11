from pydantic import BaseModel, Field
from typing import Optional, Literal


class ProjectInfo(BaseModel):
    project_name: str = Field(default="", description="项目名称")
    project_code: str = Field(default="", description="项目编号")
    budget: str = Field(default="", description="预算金额")
    bid_deadline: str = Field(default="", description="投标截止时间")
    bid_opening_time: str = Field(default="", description="开标时间")
    project_location: str = Field(default="", description="项目实施地点")
    purchaser: str = Field(default="", description="采购人/招标人")
    agent_contact: str = Field(default="", description="代理机构联系方式")


class QualificationItem(BaseModel):
    requirement: str = Field(description="要求原文")
    category: Literal["资质证书", "业绩案例", "人员配置", "财务指标", "其他"]
    is_mandatory: bool = Field(default=True)
    risk_level: Literal["low", "medium", "high"] = "low"


class ScoringItem(BaseModel):
    dimension: str = Field(description="评分维度名称")
    max_score: float = Field(description="该维度满分", gt=0)
    scoring_method: str = Field(description="评分方法")
    weight: float = Field(default=0.0, description="权重占比 0~1")


class ParsedDocument(BaseModel):
    project_info: ProjectInfo
    qualification_requirements: list[QualificationItem]
    scoring_criteria: list[ScoringItem]
    technical_requirements: list[str]
    risk_clauses: list[str]
    extraction_quality_score: float = Field(ge=0.0, le=1.0)


class QualificationResult(BaseModel):
    requirement: str
    category: str
    is_mandatory: bool
    is_met: bool
    evidence: str = Field(default="")
    risk_level: Literal["low", "medium", "high"] = "low"
    suggestion: str = Field(default="")


class QualificationAssessment(BaseModel):
    results: list[QualificationResult]
    overall_qualification: Literal["建议投标", "有风险", "不建议投标"]
    high_risk_count: int
    summary: str


class AbortAdvice(BaseModel):
    main_reasons: list[str]
    joint_venture_possible: bool
    joint_venture_advice: str = Field(default="")
    remediation_suggestions: list[str]