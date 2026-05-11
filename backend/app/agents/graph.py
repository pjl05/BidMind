from langgraph.graph import StateGraph, END
from app.agents.schemas import AgentState
from app.agents.nodes import (
    document_parser_node,
    qualification_checker_node,
    bid_abort_advisor_node,
)


def qualification_router(state: AgentState) -> str:
    """Route based on qualification result."""
    overall = state.get("overall_qualification", "")
    if overall == "不建议投标":
        return "abort"
    return "continue"


def create_analysis_graph() -> StateGraph:
    """Create the analysis workflow graph with conditional edges."""

    workflow = StateGraph(AgentState)

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