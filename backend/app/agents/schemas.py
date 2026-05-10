from typing import Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime


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