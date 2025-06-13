from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timezone, timedelta
import secrets

from app.base.model import BaseModel


class UserToken(BaseModel):
    """
    API tokens for authentication
    Supports access tokens (15 min) and refresh tokens (1 day)
    Can be linked to users or service accounts with application context
    """
    __depends_on__ = ['User']
    __tablename__ = 'user_tokens'

    user_uuid = Column(
        UUID(as_uuid=True),
        ForeignKey('users.uuid', name='fk_user_tokens_user'),
        nullable=False
    )
    token = Column(String(64), unique=True, nullable=False)
    name = Column(String(100), nullable=True)
    application = Column(String(100), nullable=True)
    token_type = Column(String(20), default='access', nullable=False)  # 'access', 'refresh', 'service'
    expires_at = Column(DateTime(timezone=True), nullable=True)
    ignore_expiration = Column(Boolean, default=False, nullable=False)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    is_system_temporary = Column(Boolean, default=False, nullable=False)
    refresh_token_uuid = Column(
        UUID(as_uuid=True),
        ForeignKey('user_tokens.uuid', name='fk_user_tokens_refresh'),
        nullable=True
    )

    rbac_audit_logs = relationship("RbacAuditLog", back_populates="token", cascade="all, delete-orphan")
    user = relationship("User", back_populates="tokens")
    access_tokens = relationship(
        "UserToken", 
        remote_side="UserToken.refresh_token_uuid", 
        cascade="all, delete-orphan",
        back_populates="refresh_token"
    )
    refresh_token = relationship(
        "UserToken", 
        remote_side="UserToken.uuid",
        back_populates="access_tokens"
    )

    __table_args__ = (
        Index('idx_user_tokens_token', 'token'),
        Index('idx_user_tokens_user', 'user_uuid'),
        Index('idx_user_tokens_type', 'token_type'),
        Index('idx_user_tokens_expires', 'expires_at'),
        Index('idx_user_tokens_refresh', 'refresh_token_uuid'),
    )

    # Token lifetime constants
    ACCESS_TOKEN_LIFETIME_MINUTES = 15
    REFRESH_TOKEN_LIFETIME_DAYS = 1

    @classmethod
    def generate_token(cls):
        return secrets.token_hex(32)

    @classmethod
    def create_access_token(cls, session, user_uuid, name=None, application=None, refresh_token_uuid=None, is_system_temporary=False):
        """Create access token with 15 minute expiration"""
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=cls.ACCESS_TOKEN_LIFETIME_MINUTES)
        
        token_value = cls.generate_token()
        user_token = cls(
            user_uuid=user_uuid,
            token=token_value,
            name=name,
            application=application,
            token_type='access',
            expires_at=expires_at,
            refresh_token_uuid=refresh_token_uuid,
            is_system_temporary=is_system_temporary
        )

        session.add(user_token)
        session.commit()
        return user_token

    @classmethod
    def create_refresh_token(cls, session, user_uuid, name=None, application=None, is_system_temporary=False):
        """Create refresh token with 1 day expiration"""
        expires_at = datetime.now(timezone.utc) + timedelta(days=cls.REFRESH_TOKEN_LIFETIME_DAYS)
        
        token_value = cls.generate_token()
        user_token = cls(
            user_uuid=user_uuid,
            token=token_value,
            name=name,
            application=application,
            token_type='refresh',
            expires_at=expires_at,
            is_system_temporary=is_system_temporary
        )

        session.add(user_token)
        session.commit()
        return user_token

    @classmethod
    def create_token_pair(cls, session, user_uuid, name=None, application=None, is_system_temporary=False):
        """Create both access and refresh tokens linked together"""
        # Create refresh token first
        refresh_token = cls.create_refresh_token(session, user_uuid, name, application, is_system_temporary)
        
        # Create access token linked to refresh token
        access_token = cls.create_access_token(
            session, user_uuid, name, application, 
            refresh_token_uuid=refresh_token.uuid, 
            is_system_temporary=is_system_temporary
        )
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token
        }

    @classmethod
    def create_user_token(cls, session, user_uuid, name=None, application=None, expires_in_days=None, is_system_temporary=False):
        """Legacy method - creates access token for backward compatibility"""
        return cls.create_access_token(session, user_uuid, name, application, is_system_temporary=is_system_temporary)

    @classmethod
    def create_service_token(cls, session, name=None, application=None, expires_in_days=None, is_system_temporary=False):
        """Create service token with custom expiration (defaults to no expiration)"""
        token_value = cls.generate_token()
        expires_at = None
        if expires_in_days is not None:
            expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)

        user_token = cls(
            user_uuid=None,
            token=token_value,
            name=name,
            application=application,
            token_type='service',
            expires_at=expires_at,
            is_system_temporary=is_system_temporary
        )

        session.add(user_token)
        session.commit()
        return user_token

    @classmethod
    def find_by_token(cls, session, token):
        return session.query(cls).filter(cls.token == token).first()

    @classmethod
    def validate_token(cls, session, token):
        """Validate any token type"""
        user_token = cls.find_by_token(session, token)
        if not user_token or not user_token.is_active:
            return None

        if not user_token.ignore_expiration and user_token.expires_at:
            if datetime.now(timezone.utc) > user_token.expires_at:
                return None

        user_token.last_used_at = datetime.now(timezone.utc)
        session.commit()
        return user_token

    @classmethod
    def validate_access_token(cls, session, token):
        """Validate specifically access tokens"""
        user_token = cls.validate_token(session, token)
        if user_token and user_token.token_type == 'access':
            return user_token
        return None

    @classmethod
    def validate_refresh_token(cls, session, token):
        """Validate specifically refresh tokens"""
        user_token = cls.validate_token(session, token)
        if user_token and user_token.token_type == 'refresh':
            return user_token
        return None

    def refresh_access_token(self, session):
        """Create new access token from refresh token"""
        if self.token_type != 'refresh':
            raise ValueError("Can only refresh from refresh tokens")
        
        if self.is_expired():
            raise ValueError("Refresh token is expired")
        
        # Revoke existing access tokens for this refresh token
        existing_access_tokens = session.query(UserToken).filter(
            UserToken.refresh_token_uuid == self.uuid,
            UserToken.is_active == True
        ).all()
        
        for token in existing_access_tokens:
            token.soft_delete()
        
        # Create new access token
        return self.__class__.create_access_token(
            session=session,
            user_uuid=self.user_uuid,
            name=self.name,
            application=self.application,
            refresh_token_uuid=self.uuid,
            is_system_temporary=self.is_system_temporary
        )

    def get_auth_context(self):
        return {
            'token_uuid': str(self.uuid),
            'token_type': self.token_type,
            'user': self.user if self.user else None,
            'user_uuid': str(self.user_uuid) if self.user_uuid else None,
            'application': self.application,
            'refresh_token_uuid': str(self.refresh_token_uuid) if self.refresh_token_uuid else None
        }

    def is_expired(self):
        if self.ignore_expiration or not self.expires_at:
            return False
        return datetime.now(timezone.utc) > self.expires_at

    def expires_in_seconds(self):
        """Get seconds until expiration"""
        if self.ignore_expiration or not self.expires_at:
            return None
        
        now = datetime.now(timezone.utc)
        if now >= self.expires_at:
            return 0
        
        return int((self.expires_at - now).total_seconds())

    def revoke(self):
        """Revoke token and any linked tokens"""
        self.soft_delete()
        
        # If this is a refresh token, revoke all linked access tokens
        if self.token_type == 'refresh':
            from sqlalchemy.orm import sessionmaker
            session = sessionmaker.object_session(self)
            if session:
                linked_tokens = session.query(UserToken).filter(
                    UserToken.refresh_token_uuid == self.uuid,
                    UserToken.is_active == True
                ).all()
                
                for token in linked_tokens:
                    token.soft_delete()

    def to_dict(self):
        return {
            'uuid': str(self.uuid),
            'user_uuid': str(self.user_uuid) if self.user_uuid else None,
            'name': self.name,
            'application': self.application,
            'token_type': self.token_type,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'expires_in_seconds': self.expires_in_seconds(),
            'ignore_expiration': self.ignore_expiration,
            'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None,
            'is_expired': self.is_expired(),
            'is_active': self.is_active,
            'is_system_temporary': self.is_system_temporary,
            'refresh_token_uuid': str(self.refresh_token_uuid) if self.refresh_token_uuid else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }