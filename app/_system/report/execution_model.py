import re
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, func, ForeignKey, Index, UniqueConstraint, event
from sqlalchemy.orm import relationship, validates
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB

from app.base.model import BaseModel


class ReportExecution(BaseModel):
    """Model for tracking report execution history"""
    __tablename__ = 'report_executions'
    __depends_on__ = ['Report','User']
    
    report_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey('reports.id', ondelete='CASCADE'),
        nullable=False
    )
    user_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True
    )
    
    # Execution details
    executed_at = Column(DateTime, default=func.now(), nullable=False)
    duration_ms = Column(Integer)  # Execution time in milliseconds
    row_count = Column(Integer)
    parameters_used = Column(JSONB)  # Parameters used for this execution
    
    # Status
    status = Column(String(50), default='success')  # success, error, timeout, cancelled
    error_message = Column(Text)
    
    # Export info
    export_format = Column(String(20))  # csv, xlsx, json, pdf
    file_size_bytes = Column(Integer)
    
    # Relationships
    report = relationship("Report", back_populates="executions")
    
    # Indexes
    __table_args__ = (
        Index('idx_execution_report_date', 'report_id', 'executed_at'),
        Index('idx_execution_user_date', 'user_id', 'executed_at'),
    )
    
    def __repr__(self):
        return f"<ReportExecution {self.report_id} at {self.executed_at}>"
