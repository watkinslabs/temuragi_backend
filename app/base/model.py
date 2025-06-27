import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Boolean, JSON, DateTime, create_engine
from sqlalchemy.dialects.postgresql import UUID

from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class BaseModel(Base):
    __abstract__ = True  
    __depends_on__ =[]
    __readonly_fields__ = ['id', 'created_at']  

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=datetime.now(timezone.utc),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
        nullable=False
    )


    def soft_delete(self):
        """Mark record as inactive instead of deleting"""
        self.is_active = False