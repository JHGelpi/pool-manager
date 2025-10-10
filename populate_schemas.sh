#!/bin/bash
set -e

echo "📝 Creating all schema files..."

# =============================================================================
# app/schemas/user.py
# =============================================================================
cat > app/schemas/user.py << 'EOF'
from uuid import UUID
from pydantic import BaseModel, EmailStr, ConfigDict


class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: UUID
    is_active: bool
    
    model_config = ConfigDict(from_attributes=True)
EOF

# =============================================================================
# app/schemas/inventory.py
# =============================================================================
cat > app/schemas/inventory.py << 'EOF'
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
EOF

# =============================================================================
# app/schemas/task.py
# =============================================================================
cat > app/schemas/task.py << 'EOF'
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
EOF

# =============================================================================
# app/schemas/alert.py
# =============================================================================
cat > app/schemas/alert.py << 'EOF'
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
EOF

# =============================================================================
# app/schemas/reading.py
# =============================================================================
cat > app/schemas/reading.py << 'EOF'
from datetime import date, datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict


# ReadingType Schemas
class ReadingTypeBase(BaseModel):
    slug: str
    name: str
    unit: Optional[str] = None
    low: Optional[float] = None
    high: Optional[float] = None


class ReadingTypeCreate(ReadingTypeBase):
    is_active: bool = True


class ReadingTypeResponse(ReadingTypeBase):
    id: UUID
    is_active: bool
    
    model_config = ConfigDict(from_attributes=True)


# Reading Schemas
class ReadingBase(BaseModel):
    reading_value: float
    reading_date: date
    notes: Optional[str] = None


class ReadingCreate(ReadingBase):
    reading_type_slug: str  # e.g., "ph", "fc"


class ReadingUpdate(BaseModel):
    reading_value: Optional[float] = None
    reading_date: Optional[date] = None
    notes: Optional[str] = None


class ReadingResponse(ReadingBase):
    id: UUID
    reading_type_slug: str
    reading_type_name: str
    unit: Optional[str] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# For chart data
class ReadingChartPoint(BaseModel):
    reading_date: str  # ISO format
    reading_value: float
EOF

echo "✅ All schema files created!"
echo ""
echo "Restarting API..."

