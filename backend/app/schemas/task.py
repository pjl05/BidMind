from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class TaskCreateResponse(BaseModel):
    task_id: str
    status: str
    file_name: str
    file_size: int
    duplicated: bool = False


class TaskListItem(BaseModel):
    task_id: str
    file_name: str
    status: str
    progress: int
    llm_cost: float
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    total: int
    page: int
    items: list[TaskListItem]