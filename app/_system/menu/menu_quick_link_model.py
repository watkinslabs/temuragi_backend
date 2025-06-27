from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer, Text, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, backref

from app.base.model import BaseModel


class UserQuickLink(BaseModel):
    __depends_on__ = ['User']  # Add this line
    __tablename__ = 'user_quick_links'

    user_id = Column(UUID(as_uuid=True),
                    ForeignKey('users.id', name='fk_user_quick_links_user', ondelete='CASCADE'),
                    nullable=False)

    menu_link_id = Column(UUID(as_uuid=True),
                        ForeignKey('menu_links.id', name='fk_user_quick_links_link', ondelete='CASCADE'),
                        nullable=False)

    position = Column(Integer, default=0, nullable=False)

    user = relationship("User", back_populates="quick_links")
    link = relationship("MenuLink", back_populates="user_quick_links")

    __table_args__ = (
        UniqueConstraint('user_id', 'menu_link_id', name='uq_user_link'),
    )