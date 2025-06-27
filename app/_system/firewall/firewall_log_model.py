import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text, func, desc
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.base.model import Base

class FirewallLog(Base):
    """Model for logging IP access requests"""
    __tablename__ = 'firewall_logs'
    __depends_on__=[]
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ip_address = Column(String(45), nullable=False)
    status = Column(Boolean, nullable=False)  # True = allowed, False = blocked
    request_path = Column(String(255), nullable=True)
    user_agent = Column(String(255), nullable=True)
    request_method = Column(String(10), nullable=True)  # GET, POST, etc.
    referer = Column(String(255), nullable=True)
    matched_rule = Column(String(50), nullable=True)  # Which rule triggered the allow/block
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    request_data = Column(Text, nullable=True)  # Optional: Store additional request data as JSON

    @classmethod
    def log_request(cls, db_session, ip_address, status, request_path=None, 
                   user_agent=None, request_method=None, referer=None, 
                   matched_rule=None, request_data=None):
        """Log an IP request with status and metadata"""
        log_entry = cls(
            ip_address=ip_address,
            status=status,
            request_path=request_path,
            user_agent=user_agent,
            request_method=request_method,
            referer=referer,
            matched_rule=matched_rule,
            request_data=request_data
        )
        
        try:
            db_session.add(log_entry)
            db_session.commit()
            return True, f'Logged {"allowed" if status else "blocked"} request from {ip_address}'
        except Exception as e:
            db_session.rollback()
            return False, f'Error logging request: {str(e)}'

    @classmethod
    def get_request_logs(cls, db_session, ip_address=None, status=None, days=7, 
                        path=None, limit=1000, offset=0):
        """Get IP request logs with filtering and pagination"""
        # Calculate date range
        end_date = datetime.datetime.utcnow()
        start_date = end_date - datetime.timedelta(days=days)
        
        # Start with base query
        query = db_session.query(cls).filter(cls.created_at.between(start_date, end_date))
        
        # Apply filters
        if ip_address:
            query = query.filter(cls.ip_address.like(f'%{ip_address}%'))
        
        if status is not None:  # Allow explicit False (0)
            query = query.filter(cls.status == status)
            
        if path:
            query = query.filter(cls.request_path.like(f'%{path}%'))
        
        # Count total before pagination (for UI pagination controls)
        total_count = query.count()
        
        # Apply pagination
        results = query.order_by(desc(cls.created_at)).limit(limit).offset(offset).all()
        
        return results, total_count

    @classmethod
    def get_top_blocked_ips(cls, db_session, days=7, limit=20):
        """Get top blocked IPs in the past days"""
        # Calculate date range
        end_date = datetime.datetime.utcnow()
        start_date = end_date - datetime.timedelta(days=days)
        
        # Query for blocked IPs with counts
        results = db_session.query(
            cls.ip_address,
            func.count(cls.id).label('count')
        ).filter(
            cls.created_at.between(start_date, end_date),
            cls.status == False
        ).group_by(
            cls.ip_address
        ).order_by(
            desc('count')
        ).limit(limit).all()
        
        return results

    @classmethod
    def get_top_allowed_ips(cls, db_session, days=7, limit=20):
        """Get top allowed IPs in the past days"""
        # Calculate date range
        end_date = datetime.datetime.utcnow()
        start_date = end_date - datetime.timedelta(days=days)
        
        # Query for allowed IPs with counts
        results = db_session.query(
            cls.ip_address,
            func.count(cls.id).label('count')
        ).filter(
            cls.created_at.between(start_date, end_date),
            cls.status == True
        ).group_by(
            cls.ip_address
        ).order_by(
            desc('count')
        ).limit(limit).all()
        
        return results

    @classmethod
    def get_daily_stats(cls, db_session, days=7):
        """Get daily statistics for allowed/blocked requests"""
        # Calculate date range
        end_date = datetime.datetime.utcnow()
        start_date = end_date - datetime.timedelta(days=days)
        
        # Query for daily counts by status
        results = db_session.query(
            func.date_trunc('day', cls.created_at).label('day'),
            cls.status,
            func.count(cls.id).label('count')
        ).filter(
            cls.created_at.between(start_date, end_date)
        ).group_by(
            'day', cls.status
        ).order_by(
            'day'
        ).all()
        
        return results
        
    @classmethod
    def get_path_stats(cls, db_session, days=7, limit=10):
        """Get statistics for most accessed paths"""
        # Calculate date range
        end_date = datetime.datetime.utcnow()
        start_date = end_date - datetime.timedelta(days=days)
        
        # Query for path counts
        results = db_session.query(
            cls.request_path,
            cls.status,
            func.count(cls.id).label('count')
        ).filter(
            cls.created_at.between(start_date, end_date),
            cls.request_path.isnot(None)
        ).group_by(
            cls.request_path, cls.status
        ).order_by(
            desc('count')
        ).limit(limit).all()
        
        return results
        
    @classmethod
    def clean_old_logs(cls, db_session, days_to_keep=30):
        """Delete logs older than the specified number of days"""
        cutoff_date = datetime.datetime.utcnow() - datetime.timedelta(days=days_to_keep)
        
        try:
            deleted_count = db_session.query(cls).filter(
                cls.created_at < cutoff_date
            ).delete()
            
            db_session.commit()
            return True, f'Deleted {deleted_count} old log entries'
        except Exception as e:
            db_session.rollback()
            return False, f'Error cleaning old logs: {str(e)}'