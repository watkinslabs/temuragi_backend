import uuid
from datetime import datetime, timezone, date
from decimal import Decimal
from sqlalchemy import Column, String, Text, Boolean, JSON, DateTime, inspect
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base

class SerializableMixin:
    def to_dict(self, exclude=None, include_relationships=False):
        exclude = exclude or []
        data = {}
        
        # Get columns
        for c in inspect(self).mapper.column_attrs:
            if c.key not in exclude:
                value = getattr(self, c.key)
                # Handle special types
                if isinstance(value, (datetime, date)):
                    value = value.isoformat()
                elif isinstance(value, Decimal):
                    value = float(value)
                elif isinstance(value, uuid.UUID):
                    value = str(value)
                data[c.key] = value
        
        # Optionally include relationships
        if include_relationships:
            for r in inspect(self).mapper.relationships:
                if r.key not in exclude:
                    value = getattr(self, r.key)
                    if value is None:
                        data[r.key] = None
                    elif isinstance(value, list):
                        data[r.key] = [v.to_dict() for v in value]
                    else:
                        data[r.key] = value.to_dict()
        
        return data
    
    def __iter__(self):
        # This makes the object behave like a dict for json serialization
        return iter(self.to_dict().items())
    
    def __getstate__(self):
        return self.to_dict()


# Create a base class that combines declarative base functionality with SerializableMixin
class DeclarativeBase:
    pass

# Create the Base with both declarative functionality and mixin methods
Base = declarative_base(cls=(DeclarativeBase, SerializableMixin))

class BaseModel(Base):
    __abstract__ = True
    __depends_on__ = []
    __readonly_fields__ = ['id', 'created_at']
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    
    is_active = Column(Boolean, default=True, nullable=False)
    
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    
    def soft_delete(self):
        """Mark record as inactive instead of deleting"""
        self.is_active = False