import uuid
from sqlalchemy import Column, String, Time, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from app.database import Base


class Alert(Base):
    __tablename__ = "alerts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    cadence = Column(String, nullable=False)  # 'daily' or 'weekly'
    _days_of_week = Column('days_of_week', String, nullable=True)  # Comma-separated: "0,2,4"
    alert_time = Column(Time, nullable=False)
    alert_on_low_inventory = Column(Boolean, default=False, nullable=False)
    alert_on_due_tasks = Column(Boolean, default=False, nullable=False)
    last_sent = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="alerts")
    
    @hybrid_property
    def days_of_week(self):
        """Convert comma-separated string to list of integers"""
        if self._days_of_week:
            return [int(d) for d in self._days_of_week.split(',')]
        return []
    
    @days_of_week.setter
    def days_of_week(self, days_list):
        """Convert list of integers to comma-separated string"""
        if days_list:
            unique_days = sorted(list(set(int(d) for d in days_list)))
            self._days_of_week = ",".join(map(str, unique_days))
        else:
            self._days_of_week = None
