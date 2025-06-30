import re
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, func, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship, validates
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB

from app.base.model import BaseModel


class SiteConfig(BaseModel):
    """Model for storing website configuration"""
    __tablename__ = 'site_configs'
    __depends_on__ = []
    
    # Internal fields
    name = Column(String(255), nullable=False)  # Internal name like "Holiday Theme"
    notes = Column(Text, nullable=True, default='')
    published = Column(Boolean, default=False, nullable=False)
    
    # Basic site information
    name = Column(String(255), nullable=False)
    tagline = Column(String(500), nullable=True, default='')
    description = Column(Text, nullable=True, default='')
    url = Column(String(500), nullable=False)
    admin_email = Column(String(255), nullable=False)
    
    # Branding/Visual
    logo_desktop_dark = Column(String(500), nullable=True)
    logo_mobile_dark = Column(String(500), nullable=True)
    logo_desktop = Column(String(500), nullable=True)
    logo_mobile = Column(String(500), nullable=True)
    favicon = Column(String(500), nullable=True)
    
    # Footer/Contact
    footer_text = Column(Text, nullable=True, default='')
    footer_links = Column(JSONB, nullable=True, default=dict)
    social_links = Column(JSONB, nullable=True, default=dict)
    
    # SEO/Analytics
    google_analytics_id = Column(String(50), nullable=True)
    other_tracking_codes = Column(JSONB, nullable=True, default=dict)
    
    # Feature flags/Settings
    maintenance_mode = Column(Boolean, default=False, nullable=False)
    maintenance_message = Column(Text, nullable=True, default='')
    allow_registration = Column(Boolean, default=True, nullable=False)
    require_email_verification = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    tags = relationship('SiteTag', back_populates='site_config', cascade='all, delete-orphan')
    keywords = relationship('SiteKeyword', back_populates='site_config', cascade='all, delete-orphan')
    prefixes = relationship('SitePrefix', back_populates='site_config', cascade='all, delete-orphan')
    
    # Indexes
    __table_args__ = (
        Index('ix_site_configs_published', 'published'),
        Index('ix_site_configs_name', 'name'),
    )
    
    
    #@validates('url', 'logo_desktop', 'logo_mobile', 'favicon')
    def validate(self, key, value):
        """Basic URL validation"""
        if value and not (value.startswith('http://') or value.startswith('https://') or value.startswith('/')):
            raise ValueError(f"{key} must be a valid URL or path")
        return value

