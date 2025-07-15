import re
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, func, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship, validates
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB

from app.base.model import BaseModel


class ReportTemplate(BaseModel):
    """Model for report-specific template configurations"""
    __tablename__ = 'report_templates'
    __depends_on__ = []
    
    # Link to actual template
    template_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey('templates.id', ondelete='RESTRICT'),
        nullable=False
    )
    
    # Report template metadata
    name = Column(String(255), nullable=False, unique=True)
    label = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Report-specific layout options
    show_filters = Column(Boolean, default=True)
    filter_position = Column(String(50), default='top')  # top, left, right
    show_export_buttons = Column(Boolean, default=True)
    show_pagination = Column(Boolean, default=True)
    pagination_position = Column(String(50), default='bottom')  # top, bottom, both
    
    # DataTable configuration
    datatable_options = Column(JSONB, nullable=True)
    
    # Custom CSS/JS for reports
    custom_css = Column(Text)
    custom_js = Column(Text)
    
    # Relationship
    template = relationship("Template", foreign_keys=[template_id])