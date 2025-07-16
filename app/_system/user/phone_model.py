from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, Index, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.base.model import BaseModel


class PhoneNumber(BaseModel):
    """User phone number model"""
    __depends_on__ = []
    __tablename__ = 'phone_numbers'
    
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey('users.id', name='fk_phone_numbers_user'),
        nullable=False
    )
    phone_type = Column(String(50), nullable=False, default='mobile')
    country_code = Column(String(5), nullable=False, default='+1')
    phone_number = Column(String(20), nullable=False)
    extension = Column(String(10), nullable=True)
    is_primary = Column(Boolean, default=False, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="phone_numbers")
    
    __table_args__ = (
        Index('idx_phone_numbers_user', 'user_id'),
        Index('idx_phone_numbers_type', 'phone_type'),
        Index('idx_phone_numbers_primary', 'user_id', 'is_primary'),
        Index('idx_phone_numbers_number', 'phone_number'),
        CheckConstraint("phone_type IN ('mobile', 'home', 'work', 'fax', 'other')", name='ck_phone_type'),
    )
    
    @property
    def full_number(self):
        """Get formatted full phone number"""
        base = f"{self.country_code} {self.phone_number}"
        if self.extension:
            base += f" x{self.extension}"
        return base
    
    def to_dict(self):
        """Convert phone number to dictionary for API response"""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'phone_type': self.phone_type,
            'country_code': self.country_code,
            'phone_number': self.phone_number,
            'extension': self.extension,
            'is_primary': self.is_primary,
            'is_verified': self.is_verified,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

