import hashlib
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, func, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship, validates
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
import json

from app.base.model import BaseModel


class ComponentBundle(BaseModel):
    """Store compiled React component bundles"""
    __tablename__ = 'component_bundles'
    __depends_on__ = []

    # Component identification
    name = Column(String(255), nullable=False, unique=True)  # Component name
    version = Column(String(50), nullable=False, default='1.0.0')
    
    # Source and compiled code
    source_code = Column(Text, nullable=False)  # Original source for reference
    compiled_code = Column(Text, nullable=False)  # Webpack bundle
    source_hash = Column(String(64))  # SHA256 of source for change detection
    
    # Component metadata
    description = Column(Text)
    props_schema = Column(JSONB, default=dict)  # Expected props
    default_props = Column(JSONB, default=dict)
    dependencies = Column(JSONB, default=list)  # NPM dependencies used
    
    # Routes this component can handle
    routes = Column(JSONB, default=list)  # List of route patterns
    
    # Build information
    build_timestamp = Column(DateTime, default=func.now())
    build_number = Column(Integer, default=1)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_system = Column(Boolean, default=False)
    
    # Relationships
    route_mappings = relationship("RouteMapping", back_populates="component", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        UniqueConstraint('name', 'version', name='uq_component_version'),
        Index('idx_component_name', 'name'),
        Index('idx_component_active', 'is_active'),
    )
    
    def __repr__(self):
        return f"<ComponentBundle {self.name}@{self.version}>"
    
    @validates('source_code')
    def validate_source_code(self, key, value):
        """Calculate hash when source code is set"""
        if value:
            self.source_hash = hashlib.sha256(value.encode()).hexdigest()
        return value
    
    def get_bundle_url(self):
        """Get URL where bundle can be accessed"""
        # You could also store bundles in S3/CDN and return that URL
        return f"/v2/api/components/{self.name}/bundle.js?v={self.version}"


