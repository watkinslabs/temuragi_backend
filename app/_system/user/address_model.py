from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, Index, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.base.model import BaseModel


class Address(BaseModel):
    """User address model"""
    __depends_on__ = ['User']
    __tablename__ = 'addresses'
    
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey('users.id', name='fk_addresses_user'),
        nullable=False
    )
    address_type = Column(String(50), nullable=False, default='home')
    address_line_1 = Column(String(255), nullable=False)
    address_line_2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=False)
    state_province = Column(String(100), nullable=False)
    postal_code = Column(String(20), nullable=False)
    country_code = Column(String(2), nullable=False, default='US')
    is_primary = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="addresses")
    
    __table_args__ = (
        Index('idx_addresses_user', 'user_id'),
        Index('idx_addresses_type', 'address_type'),
        Index('idx_addresses_primary', 'user_id', 'is_primary'),
        CheckConstraint("address_type IN ('home', 'work', 'billing', 'shipping', 'other')", name='ck_address_type'),
    )
    
    def to_dict(self):
        """Convert address to dictionary for API response"""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'address_type': self.address_type,
            'address_line_1': self.address_line_1,
            'address_line_2': self.address_line_2,
            'city': self.city,
            'state_province': self.state_province,
            'postal_code': self.postal_code,
            'country_code': self.country_code,
            'is_primary': self.is_primary,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

