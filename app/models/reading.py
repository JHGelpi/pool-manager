import uuid
import sqlalchemy as sa
from sqlalchemy import Column, String, Float, Date, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class ReadingType(Base):
    __tablename__ = "reading_types"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    unit = Column(String, nullable=True)
    low = Column(Float, nullable=True)  # Recommended low range
    high = Column(Float, nullable=True)  # Recommended high range
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    readings = relationship("Reading", back_populates="reading_type", cascade="all, delete-orphan")


class Reading(Base):
    __tablename__ = "readings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    reading_type_id = Column(UUID(as_uuid=True), ForeignKey("reading_types.id"), nullable=False)
    reading_value = Column(Float, nullable=False)
    reading_date = Column(Date, nullable=False, index=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=sa.func.now())
    
    # Relationships
    user = relationship("User", back_populates="readings")
    reading_type = relationship("ReadingType", back_populates="readings")
