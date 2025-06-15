import re
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, func, ForeignKey, Index, UniqueConstraint, event
from sqlalchemy.orm import relationship, validates
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB

from app.base.model import BaseModel


class ReportSchedule(BaseModel):
    """Model for scheduled report executions"""
    __tablename__ = 'report_schedules'
    __depends_on__ = ['Report']
    
    report_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey('reports.uuid', ondelete='CASCADE'),
        nullable=False
    )
    
    # Schedule configuration
    schedule_type = Column(String(50), nullable=False)  # cron, interval, daily, weekly, monthly
    cron_expression = Column(String(255))  # For cron type
    interval_minutes = Column(Integer)  # For interval type
    time_of_day = Column(String(10))  # HH:MM for daily/weekly/monthly
    day_of_week = Column(Integer)  # 0-6 for weekly
    day_of_month = Column(Integer)  # 1-31 for monthly
    
    # Delivery configuration
    delivery_method = Column(String(50), default='email')  # email, slack, webhook
    recipient_emails = Column(Text)  # Comma-separated emails
    webhook_url = Column(String(500))
    include_attachment = Column(Boolean, default=True)
    attachment_format = Column(String(20), default='xlsx')  # csv, xlsx, pdf
    
    # Parameters
    parameters = Column(JSONB)  # Default parameters for scheduled runs
    
    # Status
    is_enabled = Column(Boolean, default=True)
    last_run_at = Column(DateTime)
    next_run_at = Column(DateTime)
    last_run_status = Column(String(50))
    last_error = Column(Text)
    
    # Relationships
    report = relationship("Report", back_populates="schedules")
    
    # Indexes
    __table_args__ = (
        Index('idx_schedule_next_run', 'is_enabled', 'next_run_at'),
    )
    
    def __repr__(self):
        return f"<ReportSchedule {self.schedule_type} for report {self.report_id}>"


    @classmethod
    def create_initial_data(cls, session):
        """Create sample report schedules"""
        # Get the user activity report
        user_report = session.query(Report).filter_by(name='user_activity_report').first()
        if not user_report:
            return
        
        # Check if we already have schedules
        existing = session.query(cls).first()
        if existing:
            return
        
        # Create a weekly schedule for the user activity report
        schedule = cls(
            report_id=user_report.uuid,
            schedule_type='weekly',
            day_of_week=1,  # Monday
            time_of_day='09:00',
            delivery_method='email',
            recipient_emails='admin@example.com',
            attachment_format='xlsx',
            parameters={
                'start_date': "CURRENT_DATE - INTERVAL '7 days'",
                'end_date': 'CURRENT_DATE'
            },
            is_enabled=False  # Disabled by default
        )
        session.add(schedule)
