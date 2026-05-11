import asyncio
from datetime import datetime
from sqlalchemy import select
from app.tasks.celery_app import celery_app
from app.core.database import async_session_maker
from app.models.task import AnalysisTask
from app.agents.graph import analysis_graph
from app.agents.schemas import AgentState
from app.models.company import CompanyProfile


async def get_company_profile(user_id: str) -> dict:
    """Fetch company profile for user."""
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

        state = AgentState(
            task_id=task_id,
            user_id=user_id,
            file_path=file_path,
            company_profile=company_profile,
            raw_text="",
            extraction_quality_score=0.0,
            project_info={},
            qualification_requirements=[],
            scoring_criteria=[],
            technical_requirements=[],
            risk_clauses=[],
            qualification_results=[],
            overall_qualification="",
            abort_advice="",
            revision_count=0,
            current_step="",
            error=None,
            token_used=0,
            messages=[],
        )

        async for event in analysis_graph.astream(state):
            if isinstance(event, dict):
                for node_name, node_state in event.items():
                    if "progress" in node_state:
                        await update_task_progress(task_id, node_state.get("progress", 0), node_name)
                    if node_state.get("error"):
                        await update_task_error(task_id, node_state["error"])
                        return

        await finalize_task(task_id, state)

    asyncio.run(_run())


async def update_task_progress(task_id: str, progress: int, current_agent: str):
    async with async_session_maker() as session:
        result = await session.execute(
            select(AnalysisTask).where(AnalysisTask.id == task_id)
        )
        task = result.scalar_one_or_none()
        if task:
            task.progress = progress
            task.current_agent = current_agent
            task.status = "processing"
            await session.commit()


async def update_task_error(task_id: str, error_message: str):
    async with async_session_maker() as session:
        result = await session.execute(
            select(AnalysisTask).where(AnalysisTask.id == task_id)
        )
        task = result.scalar_one_or_none()
        if task:
            task.status = "failed"
            task.error_message = error_message
            await session.commit()


async def finalize_task(task_id: str, state: AgentState):
    async with async_session_maker() as session:
        result = await session.execute(
            select(AnalysisTask).where(AnalysisTask.id == task_id)
        )
        task = result.scalar_one_or_none()
        if task:
            task.status = "completed"
            task.progress = 100
            task.completed_at = datetime.utcnow()
            task.final_report = state.get("abort_advice") or state.get("overall_qualification", "")
            task.requirements = state.get("qualification_results", [])
            task.scoring_criteria = state.get("scoring_criteria", [])
            task.bid_strategy = {}
            await session.commit()