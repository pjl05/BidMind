from langgraph.graph import StateGraph, END
from app.agents.schemas import AgentState, AnalysisState
from app.agents.models import (
    ProjectInfo,
    QualificationItem,
    ScoringItem,
    ParsedDocument,
)
from app.services.deepseek import deepseek_service
from app.services.pdf_parser import pdf_parser
from app.agents.nodes import (
    document_parser_node,
    extract_requirements_node,
    analyze_scoring_node,
    generate_strategy_node,
    generate_report_node,
    qualification_checker_node,
)
import json


def create_analysis_graph() -> StateGraph:
    """Create the analysis workflow graph."""

    workflow = StateGraph(AgentState)

    workflow.add_node("parse_pdf", document_parser_node)
    workflow.add_node("extract_requirements", extract_requirements_node)
    workflow.add_node("analyze_scoring", analyze_scoring_node)
    workflow.add_node("generate_strategy", generate_strategy_node)
    workflow.add_node("generate_report", generate_report_node)
    workflow.add_node("qualification_checker", qualification_checker_node)

    workflow.set_entry_point("parse_pdf")

    workflow.add_edge("parse_pdf", "extract_requirements")
    workflow.add_edge("extract_requirements", "analyze_scoring")
    workflow.add_edge("analyze_scoring", "generate_strategy")
    workflow.add_edge("generate_strategy", "generate_report")
    workflow.add_edge("generate_report", "qualification_checker")
    workflow.add_edge("qualification_checker", END)

    return workflow.compile()


analysis_graph = create_analysis_graph()