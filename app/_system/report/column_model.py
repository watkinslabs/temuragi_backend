import re
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, func, ForeignKey, Index, UniqueConstraint, event
from sqlalchemy.orm import relationship, validates
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB

from app.base.model import BaseModel


class ReportColumn(BaseModel):
    """Model for report column definitions"""
    __tablename__ = 'report_columns'
    __depends_on__ = ['Report', 'DataType']
    
    report_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey('reports.uuid', ondelete='CASCADE'),
        nullable=False
    )
    name = Column(String(255), nullable=False)
    display_name = Column(String(255))
    
    # Link to data type
    data_type_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey('data_types.uuid', ondelete='RESTRICT'),
        nullable=False
    )
    
    # Search configuration
    is_searchable = Column(Boolean, default=True)
    search_type = Column(String(50), default='contains')  # exact, contains, starts, ends, range, list
    
    # Display configuration
    is_visible = Column(Boolean, default=True)
    is_sortable = Column(Boolean, default=True)
    format_string = Column(String(255))  # Python format string like "${:,.2f}"
    width = Column(Integer)  # Column width in pixels
    alignment = Column(String(20), default='left')  # left, center, right
    
    # Advanced options stored in JSON
    options = Column(JSONB, nullable=True)  # aggregation, link_template, css_class, etc.
    
    # Order
    order_index = Column(Integer, default=0)
    
    # Validation
    validation_regex = Column(String(500))
    validation_message = Column(String(500))
    
    # Relationships
    report = relationship("Report", back_populates="columns")
    data_type = relationship("DataType", foreign_keys=[data_type_id])
    
    # Indexes and constraints
    __table_args__ = (
        Index('idx_report_columns', 'report_id', 'order_index'),
        UniqueConstraint('report_id', 'name', name='uq_report_column_name'),
    )
    
    def __init__(self, **kwargs):
        if 'options' not in kwargs or kwargs['options'] is None:
            kwargs['options'] = {}
        super(ReportColumn, self).__init__(**kwargs)
    
    def __repr__(self):
        return f"<ReportColumn {self.name} for report {self.report_id}>"


