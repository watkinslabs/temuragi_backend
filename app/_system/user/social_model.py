from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, Index, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.base.model import BaseModel


class SocialContact(BaseModel):
    """User social/messaging contact model"""
    __depends_on__ = ['User']
    __tablename__ = 'social_contacts'
    
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey('users.id', name='fk_social_contacts_user'),
        nullable=False
    )
    platform = Column(String(50), nullable=False)
    platform_user_id = Column(String(255), nullable=True)
    handle = Column(String(255), nullable=False)
    label = Column(String(100), nullable=True)
    profile_url = Column(String(500), nullable=True)
    is_primary = Column(Boolean, default=False, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="social_contacts")
    
    __table_args__ = (
        Index('idx_social_contacts_user', 'user_id'),
        Index('idx_social_contacts_platform', 'platform'),
        Index('idx_social_contacts_primary', 'user_id', 'is_primary'),
        Index('idx_social_contacts_handle', 'handle'),
        Index('idx_social_contacts_platform_id', 'platform_user_id'),
        CheckConstraint(
            "platform IN ('whatsapp', 'telegram', 'signal', 'discord', 'slack', "
            "'skype', 'icq', 'gchat', 'wechat', 'line', 'viber', 'facebook', "
            "'instagram', 'twitter', 'linkedin', 'github', 'gitlab', 'bluesky', "
            "'mastodon', 'threads', 'reddit', 'snapchat', 'tiktok', 'youtube', "
            "'twitch', 'matrix', 'keybase', 'other')", 
            name='ck_social_platform'
        ),
    )
    
    def to_dict(self):
        """Convert social contact to dictionary for API response"""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'platform': self.platform,
            'platform_user_id': self.platform_user_id,
            'handle': self.handle,
            'label': self.label,
            'profile_url': self.profile_url,
            'is_primary': self.is_primary,
            'is_verified': self.is_verified,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

