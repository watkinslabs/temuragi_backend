from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timezone, timedelta
import secrets

from app.base.model import BaseModel


class UserToken(BaseModel):
    """
    API tokens for authentication
    Can be linked to users or service accounts with application context
    """
    __depends_on__ = ['User']
    __tablename__ = 'user_tokens'

    user_uuid = Column(
        UUID(as_uuid=True),
        ForeignKey('users.uuid', name='fk_user_tokens_user'),
        nullable=False  # Always tied to a user
    )
    token = Column(String(64), unique=True, nullable=False)
    name = Column(String(100), nullable=True)
    application = Column(String(100), nullable=True)  # App/service using token
    token_type = Column(String(20), default='user', nullable=False)  # 'user' or 'service'
    expires_at = Column(DateTime(timezone=True), nullable=True)
    ignore_expiration = Column(Boolean, default=False, nullable=False)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="tokens")

    __table_args__ = (
        Index('idx_user_tokens_token', 'token'),
        Index('idx_user_tokens_user', 'user_uuid'),
        Index('idx_user_tokens_type', 'token_type'),
        Index('idx_user_tokens_expires', 'expires_at'),
    )

    @classmethod
    def generate_token(cls):
        """Generate a secure random token"""
        return secrets.token_hex(32)

    @classmethod
    def create_user_token(cls, session, user_uuid, name=None, application=None, expires_in_days=None):
        """Create a new token for a user"""
        return cls._create_token(session, 'user', user_uuid, name, application, expires_in_days)

    @classmethod
    def create_service_token(cls, session, name=None, application=None, expires_in_days=None):
        """Create a new service token (no user)"""
        return cls._create_token(session, 'service', None, name, application, expires_in_days)

    @classmethod
    def _create_token(cls, session, token_type, user_uuid, name, application, expires_in_days):
        """Internal token creation"""
        token_value = cls.generate_token()
        
        expires_at = None
        if expires_in_days is not None:
            expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)
        
        user_token = cls(
            user_uuid=user_uuid,
            token=token_value,
            name=name,
            application=application,
            token_type=token_type,
            expires_at=expires_at
        )
        
        session.add(user_token)
        session.commit()
        
        return user_token

    @classmethod
    def find_by_token(cls, session, token):
        """Find token by token value"""
        return session.query(cls).filter(cls.token == token).first()

    @classmethod
    def validate_token(cls, session, token):
        """Validate token and return user/token info if valid"""
        user_token = cls.find_by_token(session, token)
        if not user_token or not user_token.is_active:
            return None
        
        # Check expiration unless ignored
        if not user_token.ignore_expiration and user_token.expires_at:
            if datetime.now(timezone.utc) > user_token.expires_at:
                return None
        
        # Update last used
        user_token.last_used_at = datetime.now(timezone.utc)
        session.commit()
        
        return user_token

    def get_auth_context(self):
        """Get authentication context for this token"""
        return {
            'token_uuid': str(self.uuid),
            'token_type': self.token_type,
            'user': self.user if self.user else None,
            'user_uuid': str(self.user_uuid) if self.user_uuid else None,
            'application': self.application
        }

    def is_expired(self):
        """Check if token is expired"""
        if self.ignore_expiration or not self.expires_at:
            return False
        return datetime.now(timezone.utc) > self.expires_at

    def revoke(self):
        """Revoke token (soft delete)"""
        self.soft_delete()

    def to_dict(self):
        """Convert token to dictionary (excluding sensitive token value)"""
        return {
            'uuid': str(self.uuid),
            'user_uuid': str(self.user_uuid) if self.user_uuid else None,
            'name': self.name,
            'application': self.application,
            'token_type': self.token_type,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'ignore_expiration': self.ignore_expiration,
            'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None,
            'is_expired': self.is_expired(),
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }