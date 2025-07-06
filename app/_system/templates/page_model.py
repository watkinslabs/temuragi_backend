import datetime
import logging
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer, Text, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from flask import current_app, has_app_context

from app.base.model import BaseModel

from app.register.database import db_registry

class Page(BaseModel):
    """
    Page model for individual pages that use templates and themes.

    Columns:
    - title: Page title for display and SEO
    - slug: URL-friendly identifier (unique)
    - template_id: Foreign key to templates table
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
    __depends_on__ = ['Template','Module']
    __tablename__ = 'pages'

    name = Column(String(200), nullable=False,
                  comment="Name for page for internal use")
    title = Column(String(200), nullable=False,
                  comment="Page title for display and SEO")
    slug = Column(String(100), unique=True, nullable=False,
                 comment="URL-friendly identifier")
    template_id = Column(UUID(as_uuid=True),
                          ForeignKey('templates.id', name='fk_pages_template'),
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

    module_id = Column(UUID(as_uuid=True),
                    ForeignKey('modules.id', name='fk_pages_module'),
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
        Index('idx_pages_template', 'template_id'),
        Index('idx_pages_published', 'published'),
        Index('idx_pages_featured', 'featured'),
        Index('idx_pages_publish_date', 'publish_date'),
        Index('idx_pages_expire_date', 'expire_date'),
        Index('idx_pages_auth', 'requires_auth'),
        Index('idx_pages_sort', 'sort_order'),
        Index('idx_pages_module', 'module_id'),

        UniqueConstraint('module_id', 'slug', name='uq_pages_module_slug'),
    )

    @staticmethod
    def _get_logger():
        """Get logger from Flask app context or create fallback"""
        if has_app_context():
            return current_app.logger
        else:
            return logging.getLogger('page')

    def is_visible(self):
        """Check if page should be visible based on publish/expire dates and auth requirements"""
        logger = self._get_logger()
        
        if not self.published:
            logger.debug(f"Page '{self.slug}' not published")
            return False
        
        now = datetime.datetime.now(datetime.timezone.utc)
        
        if self.publish_date and self.publish_date > now:
            logger.debug(f"Page '{self.slug}' not yet published (publish date: {self.publish_date})")
            return False
        
        if self.expire_date and self.expire_date <= now:
            logger.debug(f"Page '{self.slug}' expired (expire date: {self.expire_date})")
            return False
        
        return True

    def increment_view_count(self):
        """Increment the view count for this page"""
        logger = self._get_logger()
        old_count = self.view_count
        self.view_count += 1
        
        try:
            db_session=db_registry._routing_session()

            db_session.commit()
        except Exception as e:
            logger.error(f"Failed to increment view count for page '{self.slug}': {e}")
            db_session.rollback()
            raise

    def update_seo_metadata(self, meta_description=None, meta_keywords=None, 
                           og_title=None, og_description=None, og_image=None):
        """Update SEO metadata for the page"""
        logger = self._get_logger()
        logger.info(f"Updating SEO metadata for page '{self.slug}'")
        
        updates = []
        if meta_description is not None:
            self.meta_description = meta_description
            updates.append(f"meta_description: {len(meta_description) if meta_description else 0} chars")
        
        if meta_keywords is not None:
            self.meta_keywords = meta_keywords
            updates.append(f"meta_keywords: {len(meta_keywords.split(',')) if meta_keywords else 0} keywords")
        
        if og_title is not None:
            self.og_title = og_title
            updates.append("og_title")
        
        if og_description is not None:
            self.og_description = og_description
            updates.append("og_description")
        
        if og_image is not None:
            self.og_image = og_image
            updates.append("og_image")
        
        logger.info(f"Updated SEO metadata for page '{self.slug}': {', '.join(updates)}")

    def publish(self, publish_date=None):
        """Publish the page with optional future publish date"""
        logger = self._get_logger()
        db_session=db_registry._routing_session()

        if publish_date:
            self.publish_date = publish_date
            self.published = True
            logger.info(f"Page '{self.slug}' scheduled for publishing on {publish_date}")
        else:
            self.publish_date = datetime.datetime.now(datetime.timezone.utc)
            self.published = True
            logger.info(f"Page '{self.slug}' published immediately")
        
        try:
            db_session.commit()
            logger.info(f"Page '{self.slug}' publish status committed to database")
        except Exception as e:
            logger.error(f"Failed to publish page '{self.slug}': {e}")
            db_session.rollback()
            raise

    def unpublish(self):
        """Unpublish the page"""
        logger = self._get_logger()
        logger.info(f"Unpublishing page '{self.slug}'")

        db_session=db_registry._routing_session()
        
        self.published = False
        
        try:
            db_session.commit()
            logger.info(f"Page '{self.slug}' unpublished successfully")
        except Exception as e:
            logger.error(f"Failed to unpublish page '{self.slug}': {e}")
            db_session.rollback()
            raise

    def set_expiration(self, expire_date):
        """Set expiration date for the page"""
        logger = self._get_logger()
        
        old_expire = self.expire_date
        self.expire_date = expire_date
        
        db_session=db_registry._routing_session()
        
        try:
            db_session.commit()
        except Exception as e:
            logger.error(f"Failed to set expiration for page '{self.slug}': {e}")
            db_session.rollback()
            raise

    def validate_template_exists(self):
        """Ensure referenced template exists"""
        logger = self._get_logger()

        db_session=db_registry._routing_session()
        
        if not self.template_id:
            logger.warning(f"Page '{self.slug}' has no template assigned")
            return True
        
        logger.debug(f"Validating template {self.template_id} for page '{self.slug}'")
        
        from app.models import Template
        template = db_session.query(Template).filter_by(id=self.template_id).first()
        
        if not template:
            logger.error(f"Template {self.template_id} not found for page '{self.slug}'")
            raise ValueError("Referenced template does not exist")
        
        logger.debug(f"Template validation successful for page '{self.slug}': {template.name}")
        return True

    @classmethod
    def get_by_slug(cls, slug, include_unpublished=False):
        """Get page by slug with optional unpublished inclusion"""
        logger = cls._get_logger()
        logger.debug(f"Getting page by slug: '{slug}', include_unpublished={include_unpublished}")

        db_session=db_registry._routing_session()
        
        query = db_session.query(cls).filter_by(slug=slug)
        
        if not include_unpublished:
            query = query.filter_by(published=True)
        
        page = query.first()
        
        if page:
            logger.debug(f"Found page '{slug}': {page.title}")
            if not include_unpublished and not page.is_visible():
                logger.info(f"Page '{slug}' found but not visible")
                return None
        else:
            logger.warning(f"Page with slug '{slug}' not found")
        
        return page

    @classmethod
    def get_published_pages(cls, module_id=None, featured_only=False, limit=None):
        """Get published pages with optional filtering"""
        logger = cls._get_logger()
        logger.debug(f"Getting published pages: module={module_id}, featured_only={featured_only}, limit={limit}")

        db_session=db_registry._routing_session()
        
        query = db_session.query(cls).filter_by(published=True)
        
        if module_id:
            query = query.filter_by(module_id=module_id)
        
        if featured_only:
            query = query.filter_by(featured=True)
        
        query = query.order_by(cls.sort_order, cls.created_at.desc())
        
        if limit:
            query = query.limit(limit)
        
        pages = query.all()
        
        # Filter by visibility
        visible_pages = [p for p in pages if p.is_visible()]
        
        logger.info(f"Retrieved {len(visible_pages)} visible published pages (total found: {len(pages)})")
        return visible_pages

    @classmethod
    def get_featured_pages(cls, limit=5):
        """Get featured pages"""
        db_session=db_registry._routing_session()

        return cls.get_published_pages(db_session, featured_only=True, limit=limit)

    @classmethod
    def search_pages(cls, search_term, published_only=True):
        """Search pages by title, name, or slug"""
        db_session=db_registry._routing_session()

        logger = cls._get_logger()
        logger.debug(f"Searching pages for term: '{search_term}', published_only={published_only}")
        
        search_pattern = f"%{search_term}%"
        query = db_session.query(cls).filter(
            (cls.title.ilike(search_pattern)) |
            (cls.name.ilike(search_pattern)) |
            (cls.slug.ilike(search_pattern))
        )
        
        if published_only:
            query = query.filter_by(published=True)
        
        pages = query.order_by(cls.sort_order, cls.title).all()
        
        if published_only:
            # Filter by visibility
            visible_pages = [p for p in pages if p.is_visible()]
            logger.info(f"Search for '{search_term}': {len(visible_pages)} visible results (total: {len(pages)})")
            return visible_pages
        
        logger.info(f"Search for '{search_term}': {len(pages)} results")
        return pages

    @classmethod
    def get_pages_by_template(cls, template_id, published_only=True):
        """Get all pages using a specific template"""
        db_session=db_registry._routing_session()
        logger = cls._get_logger()
        logger.debug(f"Getting pages by template: {template_id}, published_only={published_only}")
        
        query = db_session.query(cls).filter_by(template_id=template_id)
        
        if published_only:
            query = query.filter_by(published=True)
        
        pages = query.order_by(cls.sort_order, cls.title).all()
        
        if published_only:
            visible_pages = [p for p in pages if p.is_visible()]
            logger.info(f"Found {len(visible_pages)} visible pages using template {template_id} (total: {len(pages)})")
            return visible_pages
        
        logger.info(f"Found {len(pages)} pages using template {template_id}")
        return pages

    def get_fragment_count(self):
        """Get count of active fragments for this page"""
        from app.models import PageFragment
        db_session=db_registry._routing_session()
        
        count = db_session.query(PageFragment).filter_by(
            page_id=self.id,
            is_active=True
        ).count()
        
        logger = self._get_logger()
        logger.debug(f"Page '{self.slug}' has {count} active fragments")
        return count

    def has_required_fragments(self, required_fragments=None):
        """Check if page has all required fragments"""
        db_session=db_registry._routing_session()

        if not required_fragments:
            return True
        
        logger = self._get_logger()
        from app.models import PageFragment
        
        existing_fragments = db_session.query(PageFragment.fragment_key).filter_by(
            page_id=self.id,
            is_active=True
        ).all()
        
        existing_keys = {f.fragment_key for f in existing_fragments}
        missing_fragments = set(required_fragments) - existing_keys
        
        if missing_fragments:
            logger.warning(f"Page '{self.slug}' missing required fragments: {missing_fragments}")
            return False
        
        logger.debug(f"Page '{self.slug}' has all required fragments")
        return True

    def __repr__(self):
        return f"<Page(slug='{self.slug}', title='{self.title}', published={self.published})>"