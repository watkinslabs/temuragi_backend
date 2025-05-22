import uuid
import hashlib
import os
import binascii
from datetime import datetime, timedelta

from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from app._system._core.base import Base



class LoginLog(Base):
    """Model for tracking login attempts"""
    __tablename__ = 'login_logs'

    uuid = Column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    user_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey('users.uuid'),
        nullable=True
    )
    username = Column(String, nullable=False)
    password = Column(String, nullable=False)
    login_time = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )
    successful = Column(Boolean, default=False, nullable=False)
    override = Column(Boolean, default=False, nullable=False)
    ip_address = Column(String, nullable=False)

    # Relationships
    user = relationship("User", back_populates="login_logs")

    @classmethod
    def record_login(cls, db_session, user_id, username, password, 
                   successful, override, ip_address):
        """Record a login attempt"""
        log = cls(
            user_id=user_id,
            username=username,
            password=password,
            successful=successful,
            override=override,
            ip_address=ip_address
        )
        db_session.add(log)
        db_session.commit()
        return log

