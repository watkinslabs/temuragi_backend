from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, Index, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.base.model import BaseModel


class Name(BaseModel):
    """User name model"""
    __depends_on__ = ['User']
    __tablename__ = 'names'
    
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey('users.id', name='fk_user_names_user'),
        nullable=False
    )
    name_type = Column(String(50), nullable=False, default='legal')
    first_name = Column(String(100), nullable=True)
    middle_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    full_name = Column(String(255), nullable=True)
    display_name = Column(String(100), nullable=True)
    prefix = Column(String(20), nullable=True)
    suffix = Column(String(20), nullable=True)
    is_current = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="names")
    
    __table_args__ = (
        Index('idx_user_names_user', 'user_id'),
        Index('idx_user_names_type', 'name_type'),
        Index('idx_user_names_current', 'user_id', 'is_current'),
        CheckConstraint("name_type IN ('legal', 'preferred', 'maiden', 'nickname', 'professional', 'other')", name='ck_name_type'),
    )
    
    @property
    def formatted_full_name(self):
        """Get formatted full name with prefix/suffix"""
        parts = []
        if self.prefix:
            parts.append(self.prefix)
        if self.first_name:
            parts.append(self.first_name)
        if self.middle_name:
            parts.append(self.middle_name)
        if self.last_name:
            parts.append(self.last_name)
        if self.suffix:
            parts.append(self.suffix)
        return ' '.join(parts) if parts else self.full_name
    
    def to_dict(self):
        """Convert name to dictionary for API response"""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'name_type': self.name_type,
            'first_name': self.first_name,
            'middle_name': self.middle_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'display_name': self.display_name,
            'prefix': self.prefix,
            'suffix': self.suffix,
            'is_current': self.is_current,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
