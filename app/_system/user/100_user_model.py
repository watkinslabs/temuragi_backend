import uuid
import hashlib
import os
import binascii
from datetime import datetime, timedelta

from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app._system._core.base import BaseModel

class User(BaseModel):
    """User model"""
    __tablename__ = 'users'

    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    role_uuid = Column(
        UUID(as_uuid=True),
        ForeignKey('roles.uuid', name='fk_users_role'),
        nullable=False
    )
    password_hash = Column(String, nullable=False)
    salt = Column(String, nullable=False)
    last_login_date = Column(DateTime(timezone=True), nullable=True)

    # Account lockout columns
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    is_locked = Column(Boolean, default=False, nullable=False)
    locked_until = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    role = relationship("Role", back_populates="users")
    login_logs = relationship("LoginLog", back_populates="user", cascade="all, delete-orphan")
    quick_links = relationship("UserQuickLink", back_populates="user", cascade="all, delete-orphan")

    @property
    def is_currently_locked(self):
        """Check if account is currently locked"""
        if not self.is_locked:
            return False
        if self.locked_until and datetime.utcnow() > self.locked_until:
            return False
        return True

    @classmethod
    def find_by_identity(cls, db_session, identity):
        """Find a user by username or email"""
        return db_session.query(cls).filter(
            (cls.username == identity) | (cls.email == identity)
        ).first()

    @classmethod
    def find_by_email(cls, db_session, email):
        """Find a user by email"""
        return db_session.query(cls).filter(cls.email == email).first()

    @classmethod
    def find_by_id(cls, db_session, user_uuid):
        """Find a user by UUID"""
        return db_session.query(cls).filter(cls.uuid == user_uuid).first()

    def set_password(self, password):
        """Set user password with a new salt"""
        self.salt = binascii.hexlify(os.urandom(16)).decode()
        self.password_hash = self._hash_password(password, self.salt)

    def check_password(self, password):
        """Verify password against stored hash"""
        return self.password_hash == self._hash_password(password, self.salt)

    @staticmethod
    def _hash_password(password, salt):
        """Hash password with salt using SHA-256"""
        return hashlib.sha256((password + salt).encode()).hexdigest()

    def to_dict(self):
        """Convert user to dictionary for API response"""
        return {
            'uuid': str(self.uuid),
            'username': self.username,
            'email': self.email,
            'role_uuid': str(self.role_uuid),
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_login_date': self.last_login_date.isoformat() if self.last_login_date else None
        }

