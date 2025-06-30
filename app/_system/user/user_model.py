import uuid
import hashlib
import os
import binascii
from datetime import datetime, timedelta

from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.base.model import BaseModel

from app.register.database import db_registry

class User(BaseModel):
    """User model"""
    __depends_on__ = ['Role'] 
    __tablename__ = 'users'

    landing_page = Column(String( 200), unique=False, nullable=False)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    role_id = Column(
        UUID(as_uuid=True),
        ForeignKey('roles.id', name='fk_users_role'),
        nullable=True
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
    quick_links = relationship("UserQuickLink", back_populates="user", cascade="all, delete-orphan")
    tokens = relationship("UserToken", back_populates="user", cascade="all, delete-orphan")
    rbac_audit_logs = relationship("RbacAuditLog", back_populates="user", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_users_email', 'email'),
        Index('idx_users_username', 'username'),
        Index('idx_users_role', 'role_id'),
    )
    
    @property
    def is_currently_locked(self):
        """Check if account is currently locked"""
        if not self.is_locked:
            return False
        if self.locked_until and datetime.utcnow() > self.locked_until:
            return False
        return True

    @classmethod
    def find_by_identity(cls,  identity):
        """Find a user by username or email"""
        db_session=db_registry._routing_session()

        return db_session.query(cls).filter(
            
            (cls.username == identity) | (cls.email == identity)
        ).first()

    @classmethod
    def find_by_email(cls,  email):
        """Find a user by email"""
        db_session=db_registry._routing_session()
        return db_session.query(cls).filter(cls.email == email).first()

    @classmethod
    def find_by_id(cls,  user_id):
        """Find a user by UUID"""
        db_session=db_registry._routing_session()
        return db_session.query(cls).filter(cls.id == user_id).first()

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
            'id': str(self.id),
            'username': self.username,
            'email': self.email,
            'role_id': str(self.role_id),
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_login_date': self.last_login_date.isoformat() if self.last_login_date else None
        }

