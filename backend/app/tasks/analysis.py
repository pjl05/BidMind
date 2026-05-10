import asyncio
from datetime import datetime
from sqlalchemy import select
from app.tasks.celery_app import celery_app
from app.core.database import async_session_maker
from app.models.task import AnalysisTask
from app.agents.graph import analysis_graph
from app.agents.schemas import AnalysisState


@celery_app.task(bind=True)
def run_analysis_task(self, task_id: str, user_id: str, file_path: str, file_name: str):
    """Run the analysis workflow for a task."""

    async def _run():
        state = AnalysisState(
            task_id=task_id,
            user_id=user_id,
            file_path=file_path,
            file_name=file_name,
        )

        async for event in analysis_graph.astream(state):
            if isinstance(event, dict):
                for node_name, node_state in event.items():
                    if hasattr(node_state, "progress"):
                        await update_task_progress(task_id, node_state.progress, node_name)
                    if hasattr(node_state, "error_message") and node_state.error_message:
                        await update_task_error(task_id, node_state.error_message)
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


async def finalize_task(task_id: str, state: AnalysisState):
    async with async_session_maker() as session:
        result = await session.execute(
            select(AnalysisTask).where(AnalysisTask.id == task_id)
        )
        task = result.scalar_one_or_none()
        if task:
            task.status = "completed"
            task.progress = 100
            task.completed_at = datetime.utcnow()
            task.final_report = state.final_report
            task.requirements = state.requirements
            task.scoring_criteria = state.scoring_criteria
            task.bid_strategy = state.bid_strategy
            await session.commit()