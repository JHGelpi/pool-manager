from datetime import date, timedelta, datetime
from typing import List
from uuid import UUID
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from math import ceil

from app.database import get_db
from app.models import User, MaintenanceTask, TaskCompletionHistory
from app.schemas import (
    TaskCreate, TaskUpdate, TaskComplete, TaskResponse,
    PaginatedTaskCompletionHistoryResponse
)
from app.dependencies import get_current_user
from app.config import settings

router = APIRouter(prefix="/tasks", tags=["tasks"])


def get_today_in_timezone() -> date:
    """Get today's date in the configured timezone"""
    tz = ZoneInfo(settings.TIMEZONE)
    return datetime.now(tz).date()


@router.get("/", response_model=List[TaskResponse])
async def list_tasks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all tasks for current user"""
    result = await db.execute(
        select(MaintenanceTask)
        .where(MaintenanceTask.user_id == current_user.id)
        .order_by(MaintenanceTask.next_due_date)
    )
    return result.scalars().all()


@router.post("/", response_model=TaskResponse, status_code=201)
async def create_task(
    task: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new maintenance task"""
    # Calculate next_due_date if not provided
    next_due = task.next_due_date or (get_today_in_timezone() + timedelta(days=task.frequency_days))
    
    db_task = MaintenanceTask(
        **task.model_dump(exclude={"next_due_date"}),
        next_due_date=next_due,
        user_id=current_user.id
    )
    db.add(db_task)
    await db.commit()
    await db.refresh(db_task)
    return db_task


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific task"""
    result = await db.execute(
        select(MaintenanceTask)
        .where(MaintenanceTask.id == task_id)
        .where(MaintenanceTask.user_id == current_user.id)
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: UUID,
    task_update: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a task"""
    result = await db.execute(
        select(MaintenanceTask)
        .where(MaintenanceTask.id == task_id)
        .where(MaintenanceTask.user_id == current_user.id)
    )
    db_task = result.scalar_one_or_none()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    for key, value in task_update.model_dump().items():
        setattr(db_task, key, value)
    
    await db.commit()
    await db.refresh(db_task)
    return db_task


@router.post("/{task_id}/complete", response_model=TaskResponse)
async def complete_task(
    task_id: UUID,
    completion: TaskComplete,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Mark a task as complete"""
    result = await db.execute(
        select(MaintenanceTask)
        .where(MaintenanceTask.id == task_id)
        .where(MaintenanceTask.user_id == current_user.id)
    )
    db_task = result.scalar_one_or_none()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Update completion info using configured timezone
    today = get_today_in_timezone()
    db_task.last_completed_date = today
    db_task.last_completion_notes = completion.notes
    db_task.next_due_date = today + timedelta(days=db_task.frequency_days)

    # Create completion history record
    history_entry = TaskCompletionHistory(
        task_id=task_id,
        completed_date=today,
        notes=completion.notes
    )
    db.add(history_entry)

    await db.commit()
    await db.refresh(db_task)
    return db_task


@router.get("/{task_id}/history", response_model=PaginatedTaskCompletionHistoryResponse)
async def get_task_completion_history(
    task_id: UUID,
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(15, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get paginated completion history for a task"""
    # Verify task exists and belongs to current user
    result = await db.execute(
        select(MaintenanceTask)
        .where(MaintenanceTask.id == task_id)
        .where(MaintenanceTask.user_id == current_user.id)
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Get total count
    count_result = await db.execute(
        select(func.count(TaskCompletionHistory.id))
        .where(TaskCompletionHistory.task_id == task_id)
    )
    total = count_result.scalar()

    # Calculate pagination
    total_pages = ceil(total / page_size) if total > 0 else 1
    offset = (page - 1) * page_size

    # Get paginated history
    history_result = await db.execute(
        select(TaskCompletionHistory)
        .where(TaskCompletionHistory.task_id == task_id)
        .order_by(TaskCompletionHistory.completed_date.desc())
        .limit(page_size)
        .offset(offset)
    )
    history_items = history_result.scalars().all()

    return PaginatedTaskCompletionHistoryResponse(
        items=history_items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.delete("/{task_id}", status_code=204)
async def delete_task(
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a task"""
    result = await db.execute(
        select(MaintenanceTask)
        .where(MaintenanceTask.id == task_id)
        .where(MaintenanceTask.user_id == current_user.id)
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    await db.delete(task)
    await db.commit()
    return None
