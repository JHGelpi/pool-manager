from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User, Alert
from app.schemas import AlertCreate, AlertResponse
from app.dependencies import get_current_user

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("/", response_model=List[AlertResponse])
async def list_alerts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all alerts for current user"""
    result = await db.execute(
        select(Alert).where(Alert.user_id == current_user.id)
    )
    return result.scalars().all()


@router.post("/", response_model=AlertResponse, status_code=201)
async def create_alert(
    alert: AlertCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new alert"""
    alert_data = alert.model_dump()
    days_list = alert_data.pop("days_of_week", [])
    
    db_alert = Alert(**alert_data, user_id=current_user.id)
    db_alert.days_of_week = days_list
    
    db.add(db_alert)
    await db.commit()
    await db.refresh(db_alert)
    return db_alert


@router.delete("/{alert_id}", status_code=204)
async def delete_alert(
    alert_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete an alert"""
    result = await db.execute(
        select(Alert)
        .where(Alert.id == alert_id)
        .where(Alert.user_id == current_user.id)
    )
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    await db.delete(alert)
    await db.commit()
    return None
