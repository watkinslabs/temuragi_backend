import re
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, func, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship, validates
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB

from app.base.model import BaseModel

class SiteTag(BaseModel):
    """Model for storing site tags"""
    __tablename__ = 'site_tags'
    __depends_on__ = ['SiteConfig']
    
    # Core fields
    tag_name = Column(String(100), nullable=False)
    tag_slug = Column(String(100), nullable=False)
    site_config_id = Column(PG_UUID(as_uuid=True), ForeignKey('site_configs.id'), nullable=False)
    
    # Relationships
    site_config = relationship('SiteConfig', back_populates='tags')
    
    # Indexes and constraints
    __table_args__ = (
        UniqueConstraint('site_config_id', 'tag_slug', 'is_active', name='uq_site_tag_slug'),
        Index('ix_site_tags_site_config_id', 'site_config_id'),
        Index('ix_site_tags_tag_slug', 'tag_slug'),
    )
    
    @validates('tag_slug')
    def validate_slug(self, key, value):
        """Ensure slug is lowercase and contains only valid characters"""
        if value:
            # Convert to lowercase and replace spaces with hyphens
            value = value.lower().strip()
            value = re.sub(r'[^a-z0-9-]', '-', value)
            value = re.sub(r'-+', '-', value).strip('-')
        return value