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
