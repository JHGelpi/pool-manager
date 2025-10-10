import uuid
from sqlalchemy import Column, String, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base


class ChemicalInventory(Base):
    __tablename__ = "chemical_inventory"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False, index=True)
    quantity_on_hand = Column(Float, nullable=False)
    unit = Column(String, nullable=False)
    reorder_threshold = Column(Float, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="inventory_items")
