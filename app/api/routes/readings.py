from datetime import date, timedelta
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User, ReadingType, Reading
from app.schemas import (
    ReadingTypeCreate, ReadingTypeResponse,
    ReadingCreate, ReadingResponse, ReadingChartPoint
)
from app.dependencies import get_current_user

router = APIRouter(prefix="/readings", tags=["readings"])


# Reading Types
@router.get("/types", response_model=List[ReadingTypeResponse])
async def list_reading_types(
    db: AsyncSession = Depends(get_db)
):
    """Get all active reading types"""
    result = await db.execute(
        select(ReadingType)
        .where(ReadingType.is_active == True)
        .order_by(ReadingType.slug)
    )
    return result.scalars().all()


@router.post("/types", response_model=ReadingTypeResponse, status_code=201)
async def create_reading_type(
    reading_type: ReadingTypeCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new reading type (admin feature)"""
    # Check if slug already exists
    result = await db.execute(
        select(ReadingType).where(ReadingType.slug == reading_type.slug)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Reading type with this slug already exists")
    
    db_reading_type = ReadingType(**reading_type.model_dump())
    db.add(db_reading_type)
    await db.commit()
    await db.refresh(db_reading_type)
    return db_reading_type


# Readings
@router.post("/", response_model=ReadingResponse, status_code=201)
async def create_reading(
    reading: ReadingCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new reading"""
    # Find reading type by slug
    result = await db.execute(
        select(ReadingType).where(ReadingType.slug == reading.reading_type_slug)
    )
    reading_type = result.scalar_one_or_none()
    
    if not reading_type:
        raise HTTPException(status_code=400, detail=f"Unknown reading type: {reading.reading_type_slug}")
    
    # Create reading
    db_reading = Reading(
        user_id=current_user.id,
        reading_type_id=reading_type.id,
        reading_value=reading.reading_value,
        reading_date=reading.reading_date,
        notes=reading.notes
    )
    db.add(db_reading)
    await db.commit()
    await db.refresh(db_reading)
    
    # Return with type info for frontend
    return ReadingResponse(
        id=db_reading.id,
        reading_value=db_reading.reading_value,
        reading_date=db_reading.reading_date,
        notes=db_reading.notes,
        reading_type_slug=reading_type.slug,
        reading_type_name=reading_type.name,
        unit=reading_type.unit,
        created_at=db_reading.created_at
    )


@router.get("/", response_model=List[ReadingChartPoint])
async def list_readings(
    slug: str,
    days: int = 90,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get readings for a specific type within date range"""
    # Find reading type
    result = await db.execute(
        select(ReadingType).where(ReadingType.slug == slug)
    )
    reading_type = result.scalar_one_or_none()
    
    if not reading_type:
        raise HTTPException(status_code=404, detail=f"Reading type not found: {slug}")
    
    # Get readings
    cutoff_date = date.today() - timedelta(days=days)
    result = await db.execute(
        select(Reading)
        .where(Reading.user_id == current_user.id)
        .where(Reading.reading_type_id == reading_type.id)
        .where(Reading.reading_date >= cutoff_date)
        .order_by(Reading.reading_date.asc())
    )
    readings = result.scalars().all()
    
    return [
        ReadingChartPoint(
            reading_date=r.reading_date.isoformat(),
            reading_value=float(r.reading_value)
        )
        for r in readings
    ]


@router.delete("/{reading_id}", status_code=204)
async def delete_reading(
    reading_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a reading"""
    result = await db.execute(
        select(Reading)
        .where(Reading.id == reading_id)
        .where(Reading.user_id == current_user.id)
    )
    reading = result.scalar_one_or_none()
    
    if not reading:
        raise HTTPException(status_code=404, detail="Reading not found")
    
    await db.delete(reading)
    await db.commit()
    return None