from typing import TypedDict, Annotated, Optional, Literal
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


# ── Legacy state (Week 2 Pydantic model, kept for backward compat) ──


class AnalysisState(BaseModel):
    """State for the analysis workflow."""

    task_id: str
    user_id: str
    file_path: str
    file_name: str
    text_content: str = ""
    page_count: int = 0

    current_agent: Literal["pdf_parser", "requirement_extractor", "scoring_analyzer", "strategy_generator", "report_generator", "done"] = "pdf_parser"

    requirements: list[dict] = Field(default_factory=list)
    scoring_criteria: list[dict] = Field(default_factory=list)
    bid_strategy: dict = Field(default_factory=dict)
    final_report: str = ""

    progress: int = 0
    error_message: Optional[str] = None

    token_used: int = 0
    llm_cost: float = 0.0


class AgentResponse(BaseModel):
    """Response from an agent node."""

    success: bool
    message: str
    data: dict = Field(default_factory=dict)
    token_used: int = 0
    cost: float = 0.0