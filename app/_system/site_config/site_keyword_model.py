import re
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, func, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship, validates
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB

from app.base.model import BaseModel




class SiteKeyword(BaseModel):
    """Model for storing site keywords"""
    __tablename__ = 'site_keywords'
    __depends_on__ = ['SiteConfig']
    
    # Core fields
    keyword = Column(String(255), nullable=False)
    site_config_id = Column(PG_UUID(as_uuid=True), ForeignKey('site_configs.id'), nullable=False)
    
    # Relationships
    site_config = relationship('SiteConfig', back_populates='keywords')
    
    # Indexes and constraints
    __table_args__ = (
        UniqueConstraint('site_config_id', 'keyword', 'is_active', name='uq_site_keyword'),
        Index('ix_site_keywords_site_config_id', 'site_config_id'),
        Index('ix_site_keywords_keyword', 'keyword'),
    )

