import re
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, func, ForeignKey, Index, UniqueConstraint, event
from sqlalchemy.orm import relationship, validates
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB

from app.base.model import BaseModel


class PageAction(BaseModel):
    """Model for page/report action definitions"""
    __tablename__ = 'page_actions'
    __depends_on__  = ['Report']

    # Report relationship
    report_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey('reports.id', ondelete='CASCADE'),
        nullable=False
    )

    name = Column(String(255), nullable=False)
    display = Column(String(255), nullable=False)
    mode = Column(String(50), nullable=True,default='row')
    icon = Column(String(100))
    color = Column(String(50))

    url = Column(String(500), nullable=False)
    url_for = Column(String(500))  # Template version with {{variables}}
    method = Column(String(10), default='GET', nullable=False)
    target = Column(String(20), default='_self', nullable=False)

    headers = Column(JSONB, default={})
    payload = Column(JSONB, default={})

    # Confirmation settings
    confirm = Column(Boolean, default=False, nullable=False)
    confirm_message = Column(Text)

    # Order for display
    order_index = Column(Integer, default=0, nullable=False)

    # Relationships
    report = relationship("Report", back_populates="page_actions")

    # Indexes
    __table_args__ = (
        Index('idx_page_action_report_id', 'report_id'),
        Index('idx_page_action_report_order', 'report_id', 'order_index'),
    )

    @validates('method')
    def validate_method(self, key, value):
        if value:
            value = value.upper()
            allowed_methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']
            if value not in allowed_methods:
                raise ValueError(f"Invalid HTTP method: {value}. Must be one of {allowed_methods}")
        return value

    @validates('target')
    def validate_target(self, key, value):
        if value:
            allowed_targets = ['_self', '_blank', '_parent', '_top']
            if value not in allowed_targets:
                raise ValueError(f"Invalid target: {value}. Must be one of {allowed_targets}")
        return value

    @validates('color')
    def validate_color(self, key, value):
        if value:
            allowed_colors = ['primary', 'secondary', 'success', 'danger', 'warning', 'info', 'light', 'dark']
            if value not in allowed_colors:
                raise ValueError(f"Invalid color: {value}. Must be one of {allowed_colors}")
        return value