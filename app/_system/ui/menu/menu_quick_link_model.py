import uuid
import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer, Text, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, backref

from app._system._core.base import BaseModel


class UserQuickLink(BaseModel):
    __depends_on__ = ['User']  # Add this line
    __tablename__ = 'user_quick_links'

    user_uuid = Column(UUID(as_uuid=True),
                    ForeignKey('users.uuid', name='fk_user_quick_links_user', ondelete='CASCADE'),
                    nullable=False)

    menu_link_uuid = Column(UUID(as_uuid=True),
                        ForeignKey('menu_links.uuid', name='fk_user_quick_links_link', ondelete='CASCADE'),
                        nullable=False)

    position = Column(Integer, default=0, nullable=False)

    user = relationship("User", back_populates="quick_links")
    link = relationship("MenuLink", back_populates="user_quick_links")

    __table_args__ = (
        UniqueConstraint('user_uuid', 'menu_link_uuid', name='uq_user_link'),
    )