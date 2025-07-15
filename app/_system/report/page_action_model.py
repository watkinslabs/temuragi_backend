import hashlib
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, func, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship, validates
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
import json

from app.base.model import BaseModel

class PageAction(BaseModel):
    """Model for page/report action definitions"""
    __tablename__ = 'page_actions'
    __depends_on__  = ['Report', 'RouteMapping']

    # Report relationship
    report_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey('reports.id', ondelete='CASCADE'),
        nullable=False
    )

    # Route relationship for navigate actions
    route_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey('route_mappings.id', ondelete='SET NULL'),
        nullable=True
    )

    name = Column(String(255), nullable=False)
    label = Column(String(255), nullable=False)
    mode = Column(String(50), nullable=True, default='row')
    action_type = Column(String(50), nullable=False, default='navigate')  # api, javascript, navigate, url
    icon = Column(String(100))
    color = Column(String(50))
    data_index = Column(Integer, default=0)

    url = Column(String(255), nullable=True)  # Made nullable since javascript/navigate actions won't need it
    url_for = Column(String(255))  # Template version with {{variables}}
    method = Column(String(10), default='GET', nullable=False)
    target = Column(String(20), default='_self', nullable=False)

    headers = Column(JSONB, default={})
    payload = Column(JSONB, default={})

    # JavaScript code for javascript action_type
    javascript_code = Column(Text)

    # Confirmation settings
    confirm = Column(Boolean, default=False, nullable=False)
    confirm_message = Column(Text)

    # Order for display
    order_index = Column(Integer, default=0, nullable=False)

    # Relationships
    report = relationship("Report", back_populates="page_actions")
    route = relationship("RouteMapping")

    # Indexes
    __table_args__ = (
        Index('idx_page_action_report_id', 'report_id'),
        Index('idx_page_action_report_order', 'report_id', 'order_index'),
        Index('idx_page_action_route_id', 'route_id'),
    )