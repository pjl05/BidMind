from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.user import User
from app.models.task import AnalysisTask
from app.schemas.auth import ApiResponse
from app.tasks.analysis import run_analysis_task
from app.api.v1.auth import get_current_user_required

router = APIRouter(prefix="/analysis", tags=["Analysis"])


@router.post("/{task_id}/start")
async def start_analysis(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
) -> ApiResponse:
    result = await db.execute(
        select(AnalysisTask).where(
            AnalysisTask.id == task_id,
            AnalysisTask.user_id == str(current_user.id),
        )
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.status != "pending":
        raise HTTPException(status_code=400, detail="Task already started")

    task.status = "processing"
    await db.commit()

    run_analysis_task.delay(
        task_id=str(task.id),
        user_id=str(current_user.id),
        file_path=task.file_url,
        file_name=task.file_name,
    )

    return ApiResponse(
        code=0,
        data={"task_id": task_id, "status": "processing"},
        message="Analysis started",
    )


@router.get("/{task_id}/result")
async def get_analysis_result(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_required),
) -> ApiResponse:
    result = await db.execute(
        select(AnalysisTask).where(
            AnalysisTask.id == task_id,
            AnalysisTask.user_id == str(current_user.id),
        )
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return ApiResponse(
        code=0,
        data={
            "task_id": str(task.id),
            "status": task.status,
            "progress": task.progress,
            "final_report": task.final_report,
            "requirements": task.requirements,
            "scoring_criteria": task.scoring_criteria,
            "bid_strategy": task.bid_strategy,
        },
        message="ok",
    )