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