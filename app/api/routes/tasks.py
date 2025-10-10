from datetime import date, timedelta
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User, MaintenanceTask
from app.schemas import TaskCreate, TaskUpdate, TaskComplete, TaskResponse
from app.dependencies import get_current_user

router = APIRouter(prefix="/tasks", tags=["tasks"])


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
    next_due = task.next_due_date or (date.today() + timedelta(days=task.frequency_days))
    
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
    
    # Update completion info
    db_task.last_completed_date = date.today()
    db_task.last_completion_notes = completion.notes
    db_task.next_due_date = date.today() + timedelta(days=db_task.frequency_days)
    
    await db.commit()
    await db.refresh(db_task)
    return db_task


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
