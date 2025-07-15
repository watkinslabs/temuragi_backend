from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, Index, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.base.model import BaseModel



class Email(BaseModel):
    """User email model"""
    __depends_on__ = ['User']
    __tablename__ = 'emails'
    
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey('users.id', name='fk_emails_user'),
        nullable=False
    )
    email_type = Column(String(50), nullable=False, default='personal')
    email_address = Column(String(255), nullable=False)
    is_primary = Column(Boolean, default=False, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="emails")
    
    __table_args__ = (
        Index('idx_emails_user', 'user_id'),
        Index('idx_emails_type', 'email_type'),
        Index('idx_emails_primary', 'user_id', 'is_primary'),
        Index('idx_emails_address', 'email_address'),
        CheckConstraint("email_type IN ('personal', 'work', 'other')", name='ck_email_type'),
    )
    
    def to_dict(self):
        """Convert email to dictionary for API response"""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'email_type': self.email_type,
            'email_address': self.email_address,
            'is_primary': self.is_primary,
            'is_verified': self.is_verified,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }