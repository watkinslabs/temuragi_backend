import re
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, func, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship, validates
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB

from app.base.model import BaseModel

class Model(BaseModel):
    """Model for storing model names and versions"""
    __tablename__ = 'models'
    __depends_on__ = [
    ]
    
    # Core fields
    name = Column(String(255), nullable=False)
    version = Column(String(255), nullable=False,default='1.0.0')
    description = Column(Text, nullable=True,default='')
    
    # Add unique constraint for name + version combination
    __table_args__ = (
        UniqueConstraint('name', 'version', name='uq_name_version'),
        Index('ix_models_name', 'name'),  
    )