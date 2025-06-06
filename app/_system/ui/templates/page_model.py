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
    - content: Main page content (HTML/Markdown)
    - page_template_uuid: Foreign key to page_templates table
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
    __depends_on__ = ['PageTemplate']  # Depends on PageTemplate
    __tablename__ = 'pages'

    name = Column(String(200), nullable=False,
                  comment="Name for page for internal use")
    title = Column(String(200), nullable=False,
                  comment="Page title for display and SEO")
    slug = Column(String(100), unique=True, nullable=False,
                 comment="URL-friendly identifier")
    content = Column(Text, nullable=True,
                    comment="Main page content (HTML/Markdown)")
    page_template_uuid = Column(UUID(as_uuid=True),
                               ForeignKey('page_templates.uuid', name='fk_pages_template'),
                               nullable=False,
                               comment="Foreign key to page_templates table")
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

    # Relationships
    page_template = relationship("PageTemplate", back_populates="pages")

    # Indexes
    __table_args__ = (
        Index('idx_pages_name', 'name'),
        Index('idx_pages_slug', 'slug'),
        Index('idx_pages_template', 'page_template_uuid'),
        Index('idx_pages_published', 'published'),
        Index('idx_pages_featured', 'featured'),
        Index('idx_pages_publish_date', 'publish_date'),
        Index('idx_pages_expire_date', 'expire_date'),
        Index('idx_pages_auth', 'requires_auth'),
        Index('idx_pages_sort', 'sort_order'),
        UniqueConstraint('slug', name='uq_pages_slug'),
    )

    @classmethod
    def create_initial_data(cls, session):
        """Create initial page data"""
        from app.models import PageTemplate
        
        # Get required foreign key values
        ops_template = session.query(PageTemplate).filter_by(name='ops-default').first()
        public_template = session.query(PageTemplate).filter_by(name='public-default').first()
        admin_template = session.query(PageTemplate).filter_by(name='admin-default').first()

        if not all([public_template, admin_template]):
            print("Warning: Required page templates not found for page creation")
            return

        initial_pages = [
            {
                'name': 'ops-default',
                'title': 'Welcome to the System',
                'slug': 'home',
                'content': '<h1>Welcome</h1><p>This is the home page of your application.</p>',
                'page_template_uuid': public_template.uuid,
                'meta_description': 'Welcome to our application home page',
                'meta_keywords': 'home, welcome, application',
                'published': True,
                'featured': True,
                'sort_order': 1,
                'publish_date': datetime.datetime.now(datetime.timezone.utc),
                'requires_auth': False,
                'cache_duration': 3600
            },
            {
                'name': 'public-default',
                'title': 'Welcome to the System',
                'slug': 'home',
                'content': '<h1>Welcome</h1><p>This is the home page of your application.</p>',
                'page_template_uuid': public_template.uuid,
                'meta_description': 'Welcome to our application home page',
                'meta_keywords': 'home, welcome, application',
                'published': True,
                'featured': True,
                'sort_order': 1,
                'publish_date': datetime.datetime.now(datetime.timezone.utc),
                'requires_auth': False,
                'cache_duration': 3600
            },
            {
                'name': 'admin-default',
                'title': 'Admin Dashboard',
                'slug': 'admin-dashboard',
                'content': '<h1>Admin Dashboard</h1><p>Administrative overview and controls.</p>',
                'page_template_uuid': admin_template.uuid,
                'meta_description': 'Administrative dashboard and system controls',
                'meta_keywords': 'admin, dashboard, administration',
                'published': True,
                'featured': False,
                'sort_order': 1,
                'publish_date': datetime.datetime.now(datetime.timezone.utc),
                'requires_auth': True,
                'cache_duration': 0
            }
        ]

        for page_data in initial_pages:
            existing = session.query(cls).filter_by(slug=page_data['slug']).first()
            if not existing:
                page = cls(**page_data)
                session.add(page)

    def validate_template_exists(self, session):
        """Ensure referenced template exists"""
        if not session.query(PageTemplate).filter_by(uuid=self.page_template_uuid).first():
            raise ValueError("Referenced page template does not exist")                