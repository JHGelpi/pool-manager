from uuid import UUID
from pydantic import BaseModel, ConfigDict


class InventoryBase(BaseModel):
    name: str
    quantity_on_hand: float
    unit: str
    reorder_threshold: float


class InventoryCreate(InventoryBase):
    pass


class InventoryUpdate(InventoryBase):
    pass


class InventoryResponse(InventoryBase):
    id: UUID
    user_id: UUID
    
    model_config = ConfigDict(from_attributes=True)
