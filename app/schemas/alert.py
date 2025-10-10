from datetime import time, datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class AlertBase(BaseModel):
    name: str
    cadence: str  # 'daily' or 'weekly'
    alert_time: time
    days_of_week: List[int] = []  # 0=Sunday, 6=Saturday
    alert_on_low_inventory: bool = False
    alert_on_due_tasks: bool = False


class AlertCreate(AlertBase):
    pass


class AlertUpdate(AlertBase):
    pass


class AlertResponse(AlertBase):
    id: UUID
    user_id: UUID
    last_sent: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)
