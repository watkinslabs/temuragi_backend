import uuid
import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer, Text, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app._system._core.base import BaseModel


class Page(BaseModel):
    """
    Page model for individual pages that use templates and themes.

    Columns:
    - title: Page title for display and SEO
    - slug: URL-friendly identifier (unique)
    - template_uuid: Foreign key to templates table
    - meta_description: SEO meta description
    - meta_keywords: SEO meta keywords (comma-separated)
    - og_title: Open Graph title for social sharing
    - og_description: Open Graph description for social sharing
    - og_image: Open Graph image URL for social sharing
    - canonical_url: Canonical URL for SEO
    - published: Whether page is published and visible
    - featured: Whether page is featured/highlighted
    - sort_order: Manual sorting order for page lists
    - publish_date: When page was/will be published
    - expire_date: When page should be hidden (optional)
    - view_count: Number of times page has been viewed
    - requires_auth: Whether page requires user authentication
    - cache_duration: How long to cache page in seconds (0 = no cache)
    """
    __depends_on__ = ['Template']
    __tablename__ = 'pages'

    name = Column(String(200), nullable=False,
                  comment="Name for page for internal use")
    title = Column(String(200), nullable=False,
                  comment="Page title for display and SEO")
    slug = Column(String(100), unique=True, nullable=False,
                 comment="URL-friendly identifier")
    template_uuid = Column(UUID(as_uuid=True),
                          ForeignKey('templates.uuid', name='fk_pages_template'),
                          nullable=True,
                          comment="Foreign key to templates table")
    meta_description = Column(String(255), nullable=True,
                             comment="SEO meta description")
    meta_keywords = Column(String(500), nullable=True,
                          comment="SEO meta keywords (comma-separated)")
    og_title = Column(String(200), nullable=True,
                     comment="Open Graph title for social sharing")
    og_description = Column(String(300), nullable=True,
                           comment="Open Graph description for social sharing")
    og_image = Column(String(500), nullable=True,
                     comment="Open Graph image URL for social sharing")
    canonical_url = Column(String(500), nullable=True,
                          comment="Canonical URL for SEO")
    published = Column(Boolean, default=False, nullable=False,
                      comment="Whether page is published and visible")
    featured = Column(Boolean, default=False, nullable=False,
                     comment="Whether page is featured/highlighted")
    sort_order = Column(Integer, default=0, nullable=False,
                       comment="Manual sorting order for page lists")
    publish_date = Column(DateTime(timezone=True), nullable=True,
                         comment="When page was/will be published")
    expire_date = Column(DateTime(timezone=True), nullable=True,
                        comment="When page should be hidden (optional)")
    view_count = Column(Integer, default=0, nullable=False,
                       comment="Number of times page has been viewed")
    requires_auth = Column(Boolean, default=False, nullable=False,
                          comment="Whether page requires user authentication")
    cache_duration = Column(Integer, default=300, nullable=False,
                           comment="Cache duration in seconds (0 = no cache)")

    module_uuid = Column(UUID(as_uuid=True),
                    ForeignKey('modules.uuid', name='fk_pages_module'),
                    nullable=True,
                    comment="Module that owns this page (NULL for system)")

    is_system = Column(Boolean, default=False, nullable=False,
                    comment="System-level template/page vs module-owned")

    # Relationships - FIXED
    template = relationship("Template", back_populates="pages")
    page_fragments = relationship("PageFragment", back_populates="page", cascade="all, delete-orphan")
    module = relationship("Module", back_populates="pages")

    # Indexes
    __table_args__ = (
        Index('idx_pages_name', 'name'),
        Index('idx_pages_slug', 'slug'),
        Index('idx_pages_template', 'template_uuid'),
        Index('idx_pages_published', 'published'),
        Index('idx_pages_featured', 'featured'),
        Index('idx_pages_publish_date', 'publish_date'),
        Index('idx_pages_expire_date', 'expire_date'),
        Index('idx_pages_auth', 'requires_auth'),
        Index('idx_pages_sort', 'sort_order'),
        Index('idx_pages_module', 'module_uuid'),

        UniqueConstraint('module_uuid', 'slug', name='uq_pages_module_slug'),
    )

    def validate_template_exists(self, session):
        """Ensure referenced template exists"""
        from app.models import Template
        if not session.query(Template).filter_by(uuid=self.template_uuid).first():
            raise ValueError("Referenced template does not exist")