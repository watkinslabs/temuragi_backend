import json
from sqlalchemy import Column, String, Boolean, Text, func, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.base.model import BaseModel

class Module(BaseModel):
    """Model for storing module configurations"""
    __tablename__ = 'modules'

    module_name = Column(String(100), nullable=False, unique=True, index=True)
    config_data = Column(Text, nullable=True)  # JSON blob for configuration

    # Relationships for templates and pages owned by this module
    templates = relationship("Template", back_populates="module", cascade="all, delete-orphan")
    pages = relationship("Page", back_populates="module", cascade="all, delete-orphan")

    def __repr__(self):
        """String representation of the module config"""
        return f"<ModuleConfig {self.module_name} (Active: {self.is_active})>"

