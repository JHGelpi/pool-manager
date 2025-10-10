from datetime import date
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class TaskBase(BaseModel):
    name: str
    description: Optional[str] = None
    frequency_days: int = Field(ge=1)


class TaskCreate(TaskBase):
    next_due_date: Optional[date] = None  # Auto-calculated if not provided


class TaskUpdate(TaskBase):
    next_due_date: date


class TaskComplete(BaseModel):
    notes: Optional[str] = None


class TaskResponse(TaskBase):
    id: UUID
    user_id: UUID
    next_due_date: date
    last_completed_date: Optional[date] = None
    last_completion_notes: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)
