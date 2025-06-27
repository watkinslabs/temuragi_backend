import re
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, func, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship, validates
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB

from app.base.model import BaseModel

class SitePrefix(BaseModel):
    """Model for storing site URL prefixes"""
    __tablename__ = 'site_prefixes'
    __depends_on__ = ['SiteConfig']
    
    # Core fields
    prefix_type = Column(String(50), nullable=False)  # 'admin', 'api', 'cdn', etc.
    prefix_value = Column(String(100), nullable=False)  # The actual prefix like '/admin'
    prefix_url = Column(String(500), nullable=True)  # Full URL if different domain
    site_config_id = Column(PG_UUID(as_uuid=True), ForeignKey('site_configs.id'), nullable=False)
    
    # Relationships
    site_config = relationship('SiteConfig', back_populates='prefixes')
    
    # Indexes and constraints
    __table_args__ = (
        UniqueConstraint('site_config_id', 'prefix_type', 'is_active', name='uq_site_prefix_type'),
        Index('ix_site_prefixes_site_config_id', 'site_config_id'),
        Index('ix_site_prefixes_prefix_type', 'prefix_type'),
    )
    
    @validates('prefix_value')
    def validate_prefix_value(self, key, value):
        """Ensure prefix starts with /"""
        if value and not value.startswith('/'):
            value = '/' + value
        return value