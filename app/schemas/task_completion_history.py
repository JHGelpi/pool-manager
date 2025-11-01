from datetime import date, datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class TaskCompletionHistoryBase(BaseModel):
    completed_date: date
    notes: Optional[str] = None


class TaskCompletionHistoryResponse(TaskCompletionHistoryBase):
    id: UUID
    task_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PaginatedTaskCompletionHistoryResponse(BaseModel):
    items: List[TaskCompletionHistoryResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
