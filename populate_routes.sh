#!/bin/bash
set -e

echo "📝 Populating API routes and remaining files..."

# =============================================================================
# app/api/__init__.py (empty file)
# =============================================================================
touch app/api/__init__.py

# =============================================================================
# app/api/routes/health.py
# =============================================================================
cat > app/api/routes/health.py << 'EOF'
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """Basic health check"""
    return {"status": "ok"}


@router.get("/readyz")
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """Check if app is ready (database connection)"""
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as e:
        return {"status": "not ready", "error": str(e)}
EOF

# =============================================================================
# app/api/routes/inventory.py
# =============================================================================
cat > app/api/routes/inventory.py << 'EOF'
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import User, ChemicalInventory
from app.schemas import InventoryCreate, InventoryUpdate, InventoryResponse
from app.dependencies import get_current_user

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.get("/", response_model=List[InventoryResponse])
async def list_inventory(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all inventory items for current user"""
    result = await db.execute(
        select(ChemicalInventory)
        .where(ChemicalInventory.user_id == current_user.id)
    )
    return result.scalars().all()


@router.post("/", response_model=InventoryResponse, status_code=201)
async def create_inventory_item(
    item: InventoryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new inventory item"""
    db_item = ChemicalInventory(**item.model_dump(), user_id=current_user.id)
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)
    return db_item


@router.get("/{item_id}", response_model=InventoryResponse)
async def get_inventory_item(
    item_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific inventory item"""
    result = await db.execute(
        select(ChemicalInventory)
        .where(ChemicalInventory.id == item_id)
        .where(ChemicalInventory.user_id == current_user.id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.put("/{item_id}", response_model=InventoryResponse)
async def update_inventory_item(
    item_id: UUID,
    item_update: InventoryUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update an inventory item"""
    result = await db.execute(
        select(ChemicalInventory)
        .where(ChemicalInventory.id == item_id)
        .where(ChemicalInventory.user_id == current_user.id)
    )
    db_item = result.scalar_one_or_none()
    if not db_item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    for key, value in item_update.model_dump().items():
        setattr(db_item, key, value)
    
    await db.commit()
    await db.refresh(db_item)
    return db_item


@router.delete("/{item_id}", status_code=204)
async def delete_inventory_item(
    item_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete an inventory item"""
    result = await db.execute(
        select(ChemicalInventory)
        .where(ChemicalInventory.id == item_id)
        .where(ChemicalInventory.user_id == current_user.id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    await db.delete(item)
    await db.commit()
    return None
EOF

# =============================================================================
# app/api/routes/tasks.py
# =============================================================================
cat > app/api/routes/tasks.py << 'EOF'
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
EOF

# =============================================================================
# app/api/routes/alerts.py
# =============================================================================
cat > app/api/routes/alerts.py << 'EOF'
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
EOF

# =============================================================================
# app/api/routes/readings.py
# =============================================================================
cat > app/api/routes/readings.py << 'EOF'
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
EOF

echo "✅ All API route files created successfully!"

