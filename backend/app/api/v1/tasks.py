import os
import hashlib
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.config import get_settings
from app.core.security import decode_access_token
from app.models.user import User
from app.models.task import AnalysisTask, FileDedup
from app.schemas.auth import ApiResponse
from app.schemas.task import TaskCreateResponse, TaskListItem, TaskListResponse

router = APIRouter(prefix="/tasks", tags=["Tasks"])
settings = get_settings()

MAX_FILE_SIZE = settings.MAX_FILE_SIZE_MB * 1024 * 1024  # 50MB


async def get_current_user(
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    token = authorization[7:]
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user


@router.post("", response_model=ApiResponse)
async def create_task(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    # Validate file type
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    # Read file content
    content = await file.read()
    file_size = len(content)

    # Validate file size
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail=f"File size exceeds {settings.MAX_FILE_SIZE_MB}MB limit")

    # Calculate SHA-256 hash
    file_hash = hashlib.sha256(content).hexdigest()

    # Check for duplicates
    result = await db.execute(select(FileDedup).where(FileDedup.file_hash == file_hash))
    existing_file = result.scalar_one_or_none()
    duplicated = existing_file is not None

    # Create task
    task_id = str(uuid.uuid4())
    user_id = str(current_user.id)

    # Create upload directory
    upload_dir = os.path.join(settings.UPLOAD_DIR, user_id, task_id)
    os.makedirs(upload_dir, exist_ok=True)

    # Save file
    file_path = os.path.join(upload_dir, file.filename)
    with open(file_path, "wb") as f:
        f.write(content)

    # Create task record
    task = AnalysisTask(
        id=task_id,
        user_id=user_id,
        file_name=file.filename,
        file_url=file_path,
        file_size=file_size,
        file_hash=file_hash,
        status="pending",
        progress=0,
    )
    db.add(task)

    # Save dedup record if new file
    if not duplicated:
        dedup = FileDedup(
            file_hash=file_hash,
            file_url=file_path,
            first_task_id=task_id,
        )
        db.add(dedup)

    await db.commit()

    return ApiResponse(
        code=0,
        data={
            "task_id": task_id,
            "status": "pending",
            "file_name": file.filename,
            "file_size": file_size,
            "duplicated": duplicated,
        },
        message="ok",
    )


@router.get("", response_model=ApiResponse)
async def list_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApiResponse:
    # Build query
    query = select(AnalysisTask).where(AnalysisTask.user_id == str(current_user.id))
    count_query = select(func.count()).select_from(AnalysisTask).where(
        AnalysisTask.user_id == str(current_user.id)
    )

    if status_filter:
        query = query.where(AnalysisTask.status == status_filter)
        count_query = count_query.where(AnalysisTask.status == status_filter)

    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Get paginated results
    offset = (page - 1) * page_size
    query = query.order_by(AnalysisTask.created_at.desc()).offset(offset).limit(page_size)
    result = await db.execute(query)
    tasks = result.scalars().all()

    items = [
        TaskListItem(
            task_id=str(t.id),
            file_name=t.file_name,
            status=t.status,
            progress=t.progress or 0,
            llm_cost=float(t.llm_cost or 0),
            created_at=t.created_at,
            completed_at=t.completed_at,
        )
        for t in tasks
    ]

    return ApiResponse(
        code=0,
        data={"total": total, "page": page, "items": [i.model_dump() for i in items]},
        message="ok",
    )
