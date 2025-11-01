import uuid
from sqlalchemy import Column, String, Integer, Date, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class MaintenanceTask(Base):
    __tablename__ = "maintenance_tasks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    frequency_days = Column(Integer, nullable=False)
    last_completed_date = Column(Date, nullable=True)
    next_due_date = Column(Date, nullable=False, index=True)
    last_completion_notes = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="tasks")
    completion_history = relationship("TaskCompletionHistory", back_populates="task", cascade="all, delete-orphan", order_by="desc(TaskCompletionHistory.completed_date)")
