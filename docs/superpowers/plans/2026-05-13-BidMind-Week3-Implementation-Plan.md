# BidMind Week 3 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现 Agent 1（文档解析）和 Agent 2（资格评估），能解析出结构化信息，并给出资格评估结论。

**Architecture:** 基于 FastAPI + LangGraph + DeepSeek API + 企业画像注入的条件判断流程。

---

## File Structure Overview

```
BidMind/
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   │   ├── __init__.py
│   │   │   ├── graph.py              # Updated with conditional edges
│   │   │   ├── nodes.py              # Updated with revised nodes
│   │   │   ├── schemas.py           # Updated with full AgentState
│   │   │   └── models.py            # NEW: Pydantic models
│   │   ├── api/v1/
│   │   │   ├── company.py            # NEW: Company profile endpoints
│   │   │   └── tasks.py              # Updated
│   │   ├── models/
│   │   │   ├── company.py           # NEW: Company profile model
│   │   │   └── task.py              # Updated
│   │   └── schemas/
│   │       ├── company.py           # NEW: Company profile schemas
│   │       └── analysis.py          # NEW: Analysis result schemas
│   └── alembic/versions/
│       └── 004_add_company_profiles.py  # NEW
└── frontend/
    └── src/
        └── app/
            └── company/
                └── page.tsx          # NEW: Company profile page
```

---

## Day 13: DeepSeek API Optimization & Pydantic Models (Monday)

### Task 64: Create Pydantic Models

**Files:**
- Create: `backend/app/agents/models.py`

- [ ] **Step 1: Create Pydantic models for Agent outputs**

Create: `D:/person_ai_projects/BidMind/backend/app/agents/models.py`

```python
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
```

- [ ] **Step 2: Update agents/__init__.py**

Modify: `D:/person_ai_projects/BidMind/backend/app/agents/__init__.py`

```python
from app.agents.models import (
    ProjectInfo,
    QualificationItem,
    ScoringItem,
    ParsedDocument,
    QualificationResult,
    QualificationAssessment,
    AbortAdvice,
)

__all__ = [
    "ProjectInfo",
    "QualificationItem",
    "ScoringItem",
    "ParsedDocument",
    "QualificationResult",
    "QualificationAssessment",
    "AbortAdvice",
]
```

---

### Task 65: Update DeepSeek Service with Structured Output

**Files:**
- Modify: `backend/app/services/deepseek.py`

- [ ] **Step 1: Add structured output support to DeepSeek service**

Modify: `D:/person_ai_projects/BidMind/backend/app/services/deepseek.py`

```python
from typing import Type, TypeVar
from pydantic import BaseModel
import json

T = TypeVar("T", bound=BaseModel)

class DeepSeekService:
    # ... existing code ...

    async def chat(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """Send chat completion request to DeepSeek API."""
        # ... existing implementation ...

    async def structured_chat(
        self,
        messages: list[dict],
        response_model: Type[T],
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> T:
        """Send chat completion request with structured output."""
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"},
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            return response_model.model_validate(parsed)
```

---

### Task 66: Commit Day 13 Changes

- [ ] **Step 1: Commit all Day 13 changes**

```bash
git add .
git commit -m "feat(day13): Pydantic models and DeepSeek structured output

- add ProjectInfo, QualificationItem, ScoringItem models
- add ParsedDocument, QualificationAssessment models
- add AbortAdvice model
- update DeepSeek service with structured_chat method"
```

---

## Day 14: Agent 1 - Document Parser Node (Tuesday)

### Task 67: Update Agent State with Full Schema

**Files:**
- Modify: `backend/app/agents/schemas.py`

- [ ] **Step 1: Expand AgentState with full fields from tech design**

Modify: `D:/person_ai_projects/BidMind/backend/app/agents/schemas.py`

```python
from typing import TypedDict, Annotated, Optional
from pydantic import BaseModel, Field
from langgraph.graph import add_messages


class AgentState(TypedDict):
    # ── 任务元信息 ──────────────────────────────────
    task_id: str
    user_id: str
    file_path: str

    # ── 企业画像（从DB注入）──────────────────────────────
    company_profile: Optional[dict]

    # ── 文档解析层输出 ────────────────────────────────
    raw_text: str
    extraction_quality_score: float
    project_info: dict
    qualification_requirements: list
    scoring_criteria: list
    technical_requirements: list
    risk_clauses: list

    # ── 资格评估输出 ────────────────────────────────
    qualification_results: list
    overall_qualification: str
    abort_advice: str

    # ── 控制流 ──────────────────────────────────────
    revision_count: int
    current_step: str
    error: Optional[str]
    token_used: int
    messages: Annotated[list, add_messages]
```

---

### Task 68: Implement Document Parser Node

**Files:**
- Modify: `backend/app/agents/nodes.py`

- [ ] **Step 1: Rewrite document_parser node with improved prompts**

Modify: `D:/person_ai_projects/BidMind/backend/app/agents/nodes.py`

```python
from app.agents.schemas import AnalysisState
from app.agents.models import (
    ProjectInfo,
    QualificationItem,
    ScoringItem,
    ParsedDocument,
)
from app.services.deepseek import deepseek_service
from app.services.pdf_parser import pdf_parser
import json


async def document_parser_node(state: AnalysisState) -> AnalysisState:
    """Parse PDF document and extract structured information."""
    try:
        # Extract text from PDF
        text = pdf_parser.extract_text(state.file_path)
        state.raw_text = text

        # Quality check: Chinese character density
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        total_chars = len(text)
        density = chinese_chars / total_chars if total_chars > 0 else 0
        state.extraction_quality_score = min(density * 2, 1.0) if density > 0.3 else 0.5

        # Extract key sections
        prompt = f"""从以下招投标文档中提取结构化信息。

请提取以下内容（如果文档中不存在，请填写空字符串）：
1. 项目基本信息（项目名称、项目编号、预算金额、投标截止时间、开标时间、项目实施地点、采购人、代理机构联系方式）
2. 资格要求（逐条拆分，分类别：资质证书/业绩案例/人员配置/财务指标/其他，标注是否为否决性条件）
3. 评分标准（评分维度、满分、评分方法、权重）
4. 技术要求（列表）
5. 风险条款（列表）

文档内容：
{text[:15000]}

请以JSON格式返回，包含以下字段：
- project_info: 项目基本信息对象
- qualification_requirements: 资格要求列表
- scoring_criteria: 评分标准列表
- technical_requirements: 技术要求列表
- risk_clauses: 风险条款列表
- extraction_quality_score: 提取质量评分(0-1)

确保返回的是有效的JSON格式。
"""

        system_msg = {"role": "system", "content": "你是一个专业的招投标分析助手，擅长从招标文档中提取结构化信息。"}
        user_msg = {"role": "user", "content": prompt}

        response = await deepseek_service.chat([system_msg, user_msg])

        # Parse JSON response
        data = json.loads(response)
        state.project_info = data.get("project_info", {})
        state.qualification_requirements = data.get("qualification_requirements", [])
        state.scoring_criteria = data.get("scoring_criteria", [])
        state.technical_requirements = data.get("technical_requirements", [])
        state.risk_clauses = data.get("risk_clauses", [])
        state.extraction_quality_score = data.get("extraction_quality_score", 0.5)

        state.current_step = "document_parser"
        state.progress = 20
        return state

    except Exception as e:
        state.error = str(e)
        state.current_step = "done"
        return state
```

---

### Task 69: Commit Day 14 Changes

- [ ] **Step 1: Commit all Day 14 changes**

```bash
git add .
git commit -m "feat(day14): document parser node with improved extraction

- update AgentState with full schema from tech design
- implement document_parser node with structured extraction
- add quality scoring for text extraction"
```

---

## Day 15: Agent 2 - Qualification Checker (Wednesday)

### Task 70: Create Company Profile Model and API

**Files:**
- Create: `backend/app/models/company.py`
- Create: `backend/app/schemas/company.py`
- Create: `backend/app/api/v1/company.py`

- [ ] **Step 1: Create company profile model**

Create: `D:/person_ai_projects/BidMind/backend/app/models/company.py`

```python
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
```

- [ ] **Step 2: Create company profile schemas**

Create: `D:/person_ai_projects/BidMind/backend/app/schemas/company.py`

```python
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
```

- [ ] **Step 3: Create company profile API router**

Create: `D:/person_ai_projects/BidMind/backend/app/api/v1/company.py`

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.user import User
from app.models.company import CompanyProfile
from app.schemas.company import (
    CompanyProfileCreate,
    CompanyProfileUpdate,
    CompanyProfileResponse,
)
from app.schemas.auth import ApiResponse
from app.api.v1.auth import get_current_user_required

router = APIRouter(prefix="/company-profile", tags=["Company"])


@router.put("", response_model=ApiResponse)
async def update_company_profile(
    profile_data: CompanyProfileUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
) -> ApiResponse:
    result = await db.execute(
        select(CompanyProfile).where(CompanyProfile.user_id == str(current_user.id))
    )
    profile = result.scalar_one_or_none()

    if profile:
        for key, value in profile_data.model_dump(exclude_unset=True).items():
            setattr(profile, key, value)
    else:
        profile = CompanyProfile(
            user_id=str(current_user.id),
            **profile_data.model_dump(exclude_unset=True),
        )
        db.add(profile)

    await db.commit()
    return ApiResponse(code=0, data={"profile_id": str(profile.id)}, message="ok")


@router.get("", response_model=ApiResponse)
async def get_company_profile(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
) -> ApiResponse:
    result = await db.execute(
        select(CompanyProfile).where(CompanyProfile.user_id == str(current_user.id))
    )
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(status_code=404, detail="Company profile not found")

    return ApiResponse(code=0, data=CompanyProfileResponse.model_validate(profile).model_dump(), message="ok")
```

- [ ] **Step 4: Update main.py to include company router**

Modify: `D:/person_ai_projects/BidMind/backend/app/main.py`

```python
from app.api.v1.company import router as company_router
app.include_router(company_router, prefix="/api/v1")
```

---

### Task 71: Implement Qualification Checker Node

**Files:**
- Modify: `backend/app/agents/nodes.py`

- [ ] **Step 1: Add qualification_checker node**

Append to: `D:/person_ai_projects/BidMind/backend/app/agents/nodes.py`

```python
from app.agents.models import QualificationResult, QualificationAssessment


async def qualification_checker_node(state: AnalysisState) -> AnalysisState:
    """Check if user qualifies for the tender based on company profile."""
    try:
        company = state.get("company_profile", {})
        requirements = state.get("qualification_requirements", [])

        if not company:
            state.error = "Company profile not found"
            state.current_step = "done"
            return state

        prompt = f"""基于以下企业信息和资格要求，进行资格评估。

企业信息：
- 公司名称：{company.get('company_name', '未知')}
- 资质类型：{', '.join(company.get('qualification_types', []) or ['无'])}
- 成立年限：{company.get('established_years', '未知')}年
- 类似项目经验：{'有' if company.get('has_similar_projects') else '无'}
- 年营业额：{company.get('annual_revenue', '未知')}
- 员工人数：{company.get('employee_count', '未知')}人
- 其他说明：{company.get('extra_notes', '无')}

资格要求（{len(requirements)}条）：
{chr(10).join([f"- {r.get('requirement', '')} [{r.get('category', '')}]" for r in requirements[:15]])}

请逐条评估企业是否满足要求，返回JSON格式：
{{
  "results": [
    {{
      "requirement": "要求原文",
      "category": "类别",
      "is_mandatory": true/false,
      "is_met": true/false,
      "evidence": "满足/不满足的依据",
      "risk_level": "low/medium/high",
      "suggestion": "建议"
    }}
  ],
  "overall_qualification": "建议投标/有风险/不建议投标",
  "high_risk_count": 0,
  "summary": "总体评估摘要"
}}
"""

        system_msg = {"role": "system", "content": "你是一个专业的招投标资格评估专家。"}
        user_msg = {"role": "user", "content": prompt}

        response = await deepseek_service.chat([system_msg, user_msg])
        data = json.loads(response)

        state.qualification_results = data.get("results", [])
        state.overall_qualification = data.get("overall_qualification", "有风险")
        state.current_step = "qualification_checker"
        state.progress = 50

        return state

    except Exception as e:
        state.error = str(e)
        state.current_step = "done"
        return state
```

---

### Task 72: Commit Day 15 Changes

- [ ] **Step 1: Commit all Day 15 changes**

```bash
git add .
git commit -m "feat(day15): company profile API and qualification checker

- add CompanyProfile model
- add company profile API endpoints (PUT/GET /company-profile)
- implement qualification_checker node with company profile injection"
```

---

## Day 16: Agent 2b - Bid Abort Advisor & Conditional Edge (Thursday)

### Task 73: Implement Bid Abort Advisor Node

**Files:**
- Modify: `backend/app/agents/nodes.py`

- [ ] **Step 1: Add bid_abort_advisor node**

Append to: `D:/person_ai_projects/BidMind/backend/app/agents/nodes.py`

```python
from app.agents.models import AbortAdvice


async def bid_abort_advisor_node(state: AnalysisState) -> AnalysisState:
    """Generate abort advice when qualification fails."""
    try:
        qualification_results = state.get("qualification_results", [])
        failed_requirements = [r for r in qualification_results if not r.get("is_met")]

        if not failed_requirements:
            state.current_step = "done"
            return state

        failed_list = "\n".join([
            f"- {r.get('requirement', '')} ({r.get('category', '')})"
            for r in failed_requirements
        ])

        prompt = f"""由于以下资格要求不满足，建议投标方考虑放弃本次投标：

不满足的要求：
{failed_list}

请分析：
1. 主要不满足原因
2. 是否可以采用联合体投标方式弥补
3. 如何为下次投标做准备（资质补齐建议）

请以JSON格式返回：
{{
  "main_reasons": ["原因1", "原因2"],
  "joint_venture_possible": true/false,
  "joint_venture_advice": "联合体建议",
  "remediation_suggestions": ["建议1", "建议2"]
}}
"""

        system_msg = {"role": "system", "content": "你是一个专业的招投标策略顾问。"}
        user_msg = {"role": "user", "content": prompt}

        response = await deepseek_service.chat([system_msg, user_msg])
        data = json.loads(response)

        state.abort_advice = data
        state.current_step = "bid_abort_advisor"
        state.progress = 60

        return state

    except Exception as e:
        state.error = str(e)
        state.current_step = "done"
        return state
```

---

### Task 74: Update LangGraph with Conditional Edge

**Files:**
- Modify: `backend/app/agents/graph.py`

- [ ] **Step 1: Add conditional edge for qualification check**

Modify: `D:/person_ai_projects/BidMind/backend/app/agents/graph.py`

```python
from langgraph.graph import StateGraph, END
from app.agents.schemas import AnalysisState
from app.agents.nodes import (
    document_parser_node,
    qualification_checker_node,
    bid_abort_advisor_node,
)


def qualification_router(state: AnalysisState) -> str:
    """Route based on qualification result."""
    overall = state.get("overall_qualification", "")
    if overall == "不建议投标":
        return "abort"
    return "continue"


def create_analysis_graph() -> StateGraph:
    """Create the analysis workflow graph with conditional edges."""

    workflow = StateGraph(AnalysisState)

    workflow.add_node("document_parser", document_parser_node)
    workflow.add_node("qualification_checker", qualification_checker_node)
    workflow.add_node("bid_abort_advisor", bid_abort_advisor_node)

    workflow.set_entry_point("document_parser")
    workflow.add_edge("document_parser", "qualification_checker")

    workflow.add_conditional_edges(
        "qualification_checker",
        qualification_router,
        {
            "abort": "bid_abort_advisor",
            "continue": END,
        }
    )

    workflow.add_edge("bid_abort_advisor", END)

    return workflow.compile()


analysis_graph = create_analysis_graph()
```

---

### Task 75: Commit Day 16 Changes

- [ ] **Step 1: Commit all Day 16 changes**

```bash
git add .
git commit -m "feat(day16): bid abort advisor and conditional edge

- add bid_abort_advisor node for failed qualification
- add qualification_router conditional edge logic
- update LangGraph with conditional flow"
```

---

## Day 17: Database Migration & Testing (Friday)

### Task 76: Create Company Profile Migration

**Files:**
- Create: `backend/alembic/versions/004_add_company_profiles.py`

- [ ] **Step 1: Create migration for company profiles table**

Create: `D:/person_ai_projects/BidMind/backend/alembic/versions/004_add_company_profiles.py`

```python
"""add company profiles table

Revision ID: 004
Revises: 003
Create Date: 2026-05-13
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'company_profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('company_name', sa.String(200), nullable=True),
        sa.Column('qualification_types', postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column('established_years', sa.Integer(), nullable=True),
        sa.Column('has_similar_projects', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('similar_project_desc', sa.Text(), nullable=True),
        sa.Column('annual_revenue', sa.String(50), nullable=True),
        sa.Column('employee_count', sa.Integer(), nullable=True),
        sa.Column('extra_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )


def downgrade() -> None:
    op.drop_table('company_profiles')
```

---

### Task 77: Update Celery Task with Company Profile Injection

**Files:**
- Modify: `backend/app/tasks/analysis.py`

- [ ] **Step 1: Inject company profile into analysis state**

Modify: `D:/person_ai_projects/BidMind/backend/app/tasks/analysis.py`

```python
async def get_company_profile(user_id: str) -> dict:
    """Fetch company profile for user."""
    from app.models.company import CompanyProfile
    async with async_session_maker() as session:
        result = await session.execute(
            select(CompanyProfile).where(CompanyProfile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()
        if profile:
            return {
                "company_name": profile.company_name,
                "qualification_types": profile.qualification_types or [],
                "established_years": profile.established_years,
                "has_similar_projects": profile.has_similar_projects,
                "similar_project_desc": profile.similar_project_desc,
                "annual_revenue": profile.annual_revenue,
                "employee_count": profile.employee_count,
                "extra_notes": profile.extra_notes,
            }
        return {}


@celery_app.task(bind=True)
def run_analysis_task(self, task_id: str, user_id: str, file_path: str, file_name: str):
    """Run the analysis workflow for a task."""

    async def _run():
        company_profile = await get_company_profile(user_id)

        state = AnalysisState(
            task_id=task_id,
            user_id=user_id,
            file_path=file_path,
            file_name=file_name,
            company_profile=company_profile,
        )

        async for event in analysis_graph.astream(state):
            if isinstance(event, dict):
                for node_name, node_state in event.items():
                    if hasattr(node_state, "progress"):
                        await update_task_progress(task_id, node_state.progress, node_name)
                    if hasattr(node_state, "error") and node_state.error:
                        await update_task_error(task_id, node_state.error)
                        return

        await finalize_task(task_id, state)

    asyncio.run(_run())
```

---

### Task 78: Commit Day 17 Changes

- [ ] **Step 1: Commit all Day 17 changes**

```bash
git add .
git commit -m "feat(day17): company profile migration and workflow integration

- add 004_add_company_profiles migration
- update Celery task to inject company profile into analysis
- fix qualification checker to use company profile data"
```

---

## Day 18: E2E Testing and Integration (Saturday)

### Task 79: Full Stack E2E Testing

- [ ] **Step 1: Run database migrations**

```bash
cd backend
alembic upgrade head
```

- [ ] **Step 2: Test complete flow**

```bash
# Register and login
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"week3@test.com","password":"Test1234","nickname":"Week3 Test"}'

# Create company profile
curl -X PUT http://localhost:8000/api/v1/company-profile \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"company_name":"Test Company","qualification_types":["系统集成三级","ISO9001"],"established_years":5}'

# Upload PDF
curl -X POST http://localhost:8000/api/v1/tasks \
  -H "Authorization: Bearer <token>" \
  -F "file=@test.pdf"

# Start analysis
curl -X POST http://localhost:8000/api/v1/analysis/<task_id>/start \
  -H "Authorization: Bearer <token>"

# Check results
curl http://localhost:8000/api/v1/analysis/<task_id>/result \
  -H "Authorization: Bearer <token>"
```

---

### Task 80: Push All Week 3 Changes to Remote

- [ ] **Step 1: Commit all remaining changes**

```bash
git add .
git commit -m "feat: complete week 3 implementation

Week 3 deliverables:
- Pydantic models for Agent outputs
- DeepSeek structured output support
- Company profile model and API
- Document parser node with improved extraction
- Qualification checker with company profile injection
- Bid abort advisor for failed qualification
- Conditional edge logic in LangGraph
- Database migration for company profiles"
```

- [ ] **Step 2: Push to remote**

```bash
git push origin main
```

---

## Self-Review Checklist

### Spec Coverage
- [ ] Pydantic models match tech design doc Section 5
- [ ] DeepSeek service supports structured output
- [ ] Company profile CRUD API working
- [ ] Document parser extracts all required fields
- [ ] Qualification checker uses company profile
- [ ] Bid abort advisor triggered when "不建议投标"
- [ ] Conditional edge routes correctly
- [ ] Database migration runs successfully

### Placeholder Scan
- [ ] No TBD or TODO entries
- [ ] All file paths are concrete
- [ ] All code snippets are complete
- [ ] All commands have expected outputs

### Type Consistency
- [ ] Backend: All Python use correct types
- [ ] Frontend: All TypeScript interfaces match API responses
- [ ] API: All endpoints return consistent ApiResponse format
