from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer, JSON, Index, Boolean, func, case
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timezone, timedelta
import json
from flask import g 

from app.base.model import BaseModel
from app.register.database import db_registry


        


class RbacAuditLog(BaseModel):
    """
    RBAC Audit Log - Records all permission checks across the entire system
    Triggered whenever RBAC permissions are checked, regardless of interface
    """
    __depends_on__ = ['User', 'UserToken','Permission']
    __tablename__ = 'rbac_audit_logs'

    # User context
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey('users.id', name='fk_rbac_audit_logs_user'),
        nullable=True  # Some operations might be system-level
    )
    token_id = Column(
        UUID(as_uuid=True),
        ForeignKey('user_tokens.id', name='fk_rbac_audit_logs_token'),
        nullable=True  # CLI operations might not have tokens
    )

    # Permission context
    permission_name = Column(String(100), nullable=False)  # "users:read", "admin:write", etc.
    permission_granted = Column(Boolean, nullable=False)
    access_denied_reason = Column(Text, nullable=True)

    # Access context - what was being accessed
    resource_type = Column(String(50), nullable=True)  # "model", "view", "cli", "api", "file", etc.
    resource_name = Column(String(100), nullable=True)  # "User", "admin_dashboard", "user_cli", etc.
    resource_id = Column(String(100), nullable=True)  # UUID, filename, etc.
    action_attempted = Column(String(50), nullable=True)  # "read", "write", "delete", "execute", etc.

    # Request context - how the access was attempted
    interface_type = Column(String(20), nullable=False)  # "api", "web", "cli", "system"
    endpoint = Column(String(200), nullable=True)  # "/api/data", "/admin/users", "user_cli list", etc.
    request_method = Column(String(10), nullable=True)  # "POST", "GET", "CLI", etc.
    ip_address = Column(String(45), nullable=True)  # IPv4/IPv6
    user_agent = Column(Text, nullable=True)

    request_id = Column(String(100), nullable=True)  # Unique request identifier

    # Additional context data
    context_data = Column(JSON, nullable=True)  # Extra context (filters, params, etc.)

    # Performance tracking
    check_duration_ms = Column(Integer, nullable=True)  # How long the permission check took

    # Relationships
    user = relationship("User", back_populates="rbac_audit_logs")
    token = relationship("UserToken", back_populates="rbac_audit_logs")

    __table_args__ = (
        Index('idx_rbac_audit_logs_user', 'user_id'),
        Index('idx_rbac_audit_logs_permission', 'permission_name'),
        Index('idx_rbac_audit_logs_granted', 'permission_granted'),
        Index('idx_rbac_audit_logs_created', 'created_at'),
        Index('idx_rbac_audit_logs_interface', 'interface_type'),
        Index('idx_rbac_audit_logs_resource', 'resource_type', 'resource_name'),
        # Composite indexes for common queries
        Index('idx_rbac_audit_logs_user_permission', 'user_id', 'permission_name'),
        Index('idx_rbac_audit_logs_denied', 'permission_granted', 'created_at'),
        Index('idx_rbac_audit_logs_user_denied', 'user_id', 'permission_granted', 'created_at'),
    )

    @classmethod
    def log_permission_check(cls, **kwargs):
        """
        Log a permission check

        Usage:
        RbacAuditLog.log_permission_check(
            user_id=user.id,
            permission_name="users:read",
            permission_granted=True,
            resource_type="model",
            resource_name="User",
            interface_type="api",
            endpoint="/api/data"
        )
        """
        try:
            audit_entry = cls(**kwargs)
            db_session=db_registry._routing_session()

            db_session.add(audit_entry)
            db_session.commit()
            return audit_entry
        except Exception as e:
            db_session.rollback()
            # Don't let audit logging break the main request
            print(f"RBAC audit logging failed: {e}")
            return None

    @classmethod
    def log_api_permission_check(cls, user_id, permission_name, granted,
                                resource_name=None, action=None, context=None,
                                token_id=None, ip_address=None, user_agent=None):
        """Log permission check from API"""
        return cls.log_permission_check(
            user_id=user_id,
            token_id=token_id,
            permission_name=permission_name,
            permission_granted=granted,
            resource_type="model",
            resource_name=resource_name,
            action_attempted=action,
            interface_type="api",
            endpoint="/api/data",
            ip_address=ip_address,
            user_agent=user_agent,
            context_data=context
        )

    @classmethod
    def log_web_permission_check(cls, user_id, permission_name, granted,
                                endpoint=None, method=None, ip_address=None,
                                user_agent=None,  context=None):
        """Log permission check from web interface"""
        return cls.log_permission_check(
            user_id=user_id,
            permission_name=permission_name,
            permission_granted=granted,
            resource_type="view",
            interface_type="web",
            endpoint=endpoint,
            request_method=method,
            ip_address=ip_address,
            user_agent=user_agent,
            context_data=context
        )

    @classmethod
    def log_cli_permission_check(cls, user_id, permission_name, granted,
                                cli_command=None, resource_name=None, action=None, context=None):
        """Log permission check from CLI"""
        return cls.log_permission_check(
            user_id=user_id,
            permission_name=permission_name,
            permission_granted=granted,
            resource_type="cli",
            resource_name=resource_name,
            action_attempted=action,
            interface_type="cli",
            endpoint=cli_command,
            request_method="CLI",
            context_data=context
        )

    @classmethod
    def get_recent_activity(cls, hours=24, limit=50):
        """Get recent RBAC activity"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        db_session=db_registry._routing_session()

        return db_session.query(cls)\
            .filter(cls.created_at >= cutoff_date)\
            .order_by(cls.created_at.desc())\
            .limit(limit).all()

    @classmethod
    def get_security_alerts(cls, hours=24):
        """Get recent permission denials and security events"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        db_session=db_registry._routing_session()

        return db_session.query(cls).filter(
            cls.created_at >= cutoff_date,
            cls.permission_granted == False  # Only denied permissions
        ).order_by(cls.created_at.desc()).all()

    @classmethod
    def get_performance_stats(cls, interface_type=None, hours=24):
        """Get permission check performance statistics"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(hours=hours)

        db_session=db_registry._routing_session()

        query = db_session.query(
            cls.interface_type,
            cls.permission_name,
            func.count(cls.id).label('total_checks'),
            func.avg(cls.check_duration_ms).label('avg_duration'),
            func.max(cls.check_duration_ms).label('max_duration'),
            func.sum(case((cls.permission_granted == True, 1), else_=0)).label('granted'),
            func.sum(case((cls.permission_granted == False, 1), else_=0)).label('denied')
        ).filter(
            cls.created_at >= cutoff_date,
            cls.check_duration_ms.isnot(None)
        )

        if interface_type:
            query = query.filter(cls.interface_type == interface_type)

        return query.group_by(
            cls.interface_type,
            cls.permission_name
        ).order_by(
            cls.interface_type,
            func.count(cls.id).desc()
        ).all()

    @classmethod
    def get_user_permission_activity(cls, user_id, days=30):
        """Get user permission activity summary"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

        db_session=db_registry._routing_session()
        
        return db_session.query(
            cls.permission_name,
            cls.interface_type,
            cls.resource_type,
            func.count(cls.id).label('attempts'),
            func.sum(case((cls.permission_granted == True, 1), else_=0)).label('granted'),
            func.sum(case((cls.permission_granted == False, 1), else_=0)).label('denied')
        ).filter(
            cls.user_id == user_id,
            cls.created_at >= cutoff_date
        ).group_by(
            cls.permission_name, cls.interface_type, cls.resource_type
        ).all()

    @classmethod
    def get_user_recent_activity(cls, user_id, days=1, limit=10):
        """Get recent detailed activity for a user"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

        db_session=db_registry._routing_session()

        return db_session.query(cls)\
            .filter(
                cls.user_id == user_id,
                cls.created_at >= cutoff_date
            )\
            .order_by(cls.created_at.desc())\
            .limit(limit).all()

    @classmethod
    def get_permission_usage_stats(cls, days=7):
        """Get permission usage statistics"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        db_session=db_registry._routing_session()

        return db_session.query(
            cls.permission_name,
            cls.interface_type,
            func.count(cls.id).label('total_checks'),
            func.sum(case((cls.permission_granted == True, 1), else_=0)).label('granted'),
            func.sum(case((cls.permission_granted == False, 1), else_=0)).label('denied'),
            func.count(func.distinct(cls.user_id)).label('unique_users')
        ).filter(
            cls.created_at >= cutoff_date
        ).group_by(
            cls.permission_name,
            cls.interface_type
        ).order_by(
            func.count(cls.id).desc()
        ).all()

    @classmethod
    def get_denial_analysis(cls, hours=24):
        """Get permission denial analysis"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        db_session=db_registry._routing_session()

        denial_summary = db_session.query(
            cls.permission_name,
            cls.interface_type,
            cls.access_denied_reason,
            func.count(cls.id).label('count')
        ).filter(
            cls.created_at >= cutoff_date,
            cls.permission_granted == False
        ).group_by(
            cls.permission_name,
            cls.interface_type,
            cls.access_denied_reason
        ).order_by(
            func.count(cls.id).desc()
        ).all()

        recent_denials = db_session.query(cls)\
            .filter(
                cls.created_at >= cutoff_date,
                cls.permission_granted == False
            )\
            .order_by(cls.created_at.desc())\
            .limit(10).all()

        return denial_summary, recent_denials

    @classmethod
    def get_suspicious_activity(cls, hours=24, min_denials=5):
        """Get users with suspicious activity (many permission denials)"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        db_session=db_registry._routing_session()

        return db_session.query(
            cls.user_id,
            func.count(cls.id).label('total_denials'),
            func.count(func.distinct(cls.permission_name)).label('unique_permissions'),
            func.count(func.distinct(cls.ip_address)).label('unique_ips'),
            func.max(cls.created_at).label('last_denial')
        ).filter(
            cls.created_at >= cutoff_date,
            cls.permission_granted == False,
            cls.user_id.isnot(None)
        ).group_by(
            cls.user_id
        ).having(
            func.count(cls.id) >= min_denials
        ).order_by(
            func.count(cls.id).desc()
        ).all()

    @classmethod
    def cleanup_old_logs(cls, days=90):
        """Clean up old audit logs and return count"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        db_session=db_registry._routing_session()

        # Count logs to be deleted
        old_count = db_session.query(func.count(cls.id))\
            .filter(cls.created_at < cutoff_date).scalar()

        return old_count, cutoff_date

    @classmethod
    def delete_old_logs(cls, cutoff_date):
        """Actually delete old logs"""
        db_session=db_registry._routing_session()

        deleted = db_session.query(cls)\
            .filter(cls.created_at < cutoff_date)\
            .delete()

        db_session.commit()
        return deleted

    def to_dict(self):
        """Convert audit log to dictionary for API responses"""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id) if self.user_id else None,
            'token_id': str(self.token_id) if self.token_id else None,
            'permission_name': self.permission_name,
            'permission_granted': self.permission_granted,
            'access_denied_reason': self.access_denied_reason,
            'resource_type': self.resource_type,
            'resource_name': self.resource_name,
            'resource_id': self.resource_id,
            'action_attempted': self.action_attempted,
            'interface_type': self.interface_type,
            'endpoint': self.endpoint,
            'request_method': self.request_method,
            'ip_address': self.ip_address,
            'context_data': self.context_data,
            'check_duration_ms': self.check_duration_ms,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }