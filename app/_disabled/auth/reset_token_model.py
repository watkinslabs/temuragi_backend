import uuid
import hashlib
import os
import binascii
from datetime import datetime, timedelta

from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from app._system._core.base import BaseModel


class ResetToken(BaseModel):
    """Model for password reset tokens"""
    __tablename__ = 'reset_tokens'

    user_uuid = Column(
        PG_UUID(as_uuid=True),
        ForeignKey('users.uuid'),
        nullable=False
    )
    token = Column(String, unique=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used = Column(Boolean, default=False, nullable=False)

    # Relationships
    user = relationship("User", back_populates="reset_tokens")

    @classmethod
    def create_for_user(cls, db_session, user_uuid, expires_days=1):
        """Create a password reset token for a user"""
        # Generate random token
        token = binascii.hexlify(os.urandom(32)).decode()
        
        # Set expiry time
        expires_at = datetime.utcnow() + timedelta(days=expires_days)
        
        # Create token record
        reset_token = cls(
            user_uuid=user_uuid,
            token=token,
            expires_at=expires_at
        )
        
        db_session.add(reset_token)
        db_session.commit()
        return reset_token

    @classmethod
    def verify(cls, db_session, token):
        """Verify a reset token is valid"""
        reset_token = db_session.query(cls).filter(
            cls.token == token,
            cls.used == False,
            cls.expires_at > datetime.utcnow(),
            cls.active == True
        ).first()
        
        return reset_token

    def consume(self, db_session):
        """Mark a token as used"""
        self.used = True
        db_session.commit()
        return True