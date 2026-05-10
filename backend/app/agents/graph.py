from langgraph.graph import StateGraph, END
from app.agents.schemas import AnalysisState
from app.agents.nodes import (
    parse_pdf_node,
    extract_requirements_node,
    analyze_scoring_node,
    generate_strategy_node,
    generate_report_node,
)


def create_analysis_graph() -> StateGraph:
    """Create the analysis workflow graph."""

    workflow = StateGraph(AnalysisState)

    workflow.add_node("parse_pdf", parse_pdf_node)
    workflow.add_node("extract_requirements", extract_requirements_node)
    workflow.add_node("analyze_scoring", analyze_scoring_node)
    workflow.add_node("generate_strategy", generate_strategy_node)
    workflow.add_node("generate_report", generate_report_node)

    workflow.set_entry_point("parse_pdf")

    workflow.add_edge("parse_pdf", "extract_requirements")
    workflow.add_edge("extract_requirements", "analyze_scoring")
    workflow.add_edge("analyze_scoring", "generate_strategy")
    workflow.add_edge("generate_strategy", "generate_report")
    workflow.add_edge("generate_report", END)

    return workflow.compile()


analysis_graph = create_analysis_graph()