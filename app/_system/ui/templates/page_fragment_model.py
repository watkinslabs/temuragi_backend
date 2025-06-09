import uuid
import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer, Text, Index, UniqueConstraint, JSON
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app._system._core.base import BaseModel


class PageFragment(BaseModel):
    """
    Page fragments model for storing content fragments for individual pages.

    Supports multiple content pieces per page (fragments) with versioning per fragment_key.
    Only one version of each fragment_key can be active at a time, but multiple different
    fragment_keys can be active simultaneously for a single page.

    Columns:
    - page_uuid: Foreign key to pages table
    - fragment_type: Semantic type (content, sidebar, hero, callout, etc.)
    - fragment_name: Human readable name for admin interface
    - fragment_key: Identifier for the content fragment (e.g., 'main_content', 'sidebar', 'hero')
    - content_type: MIME type (text/html, text/plain, text/markdown, etc.)
    - version_number: Version number for this specific fragment_key
    - version_label: Optional human-readable version label
    - is_active: Whether this version of this fragment_key is active
    - content_source: The actual content (HTML/Markdown/Text)
    - content_hash: SHA256 hash of content for change detection
    - variables_data: JSON data for template variables (if using template fragments)
    - template_fragment_key: Reference to TemplateFragment if using template-based content
    - description: What this fragment contains and its purpose
    - sort_order: Display order within fragment type
    - is_published: Whether this fragment should be shown to public
    - publish_date: When fragment was/will be published
    - expire_date: When fragment should be hidden
    - cache_duration: How long to cache this content (seconds)
    - last_rendered: When the content was last rendered
    """
    __depends_on__ = ['Page']  # Depends on Page
    __tablename__ = 'page_fragments'

    page_uuid = Column(UUID(as_uuid=True),
                      ForeignKey('pages.uuid', name='fk_page_fragments_page'),
                      nullable=False,
                      comment="Foreign key to pages table")
    
    # Fragment identification
    fragment_type = Column(String(50), nullable=False,
                          comment="Semantic fragment type (content, sidebar, hero, callout, widget, etc.)")
    fragment_name = Column(String(100), nullable=False,
                          comment="Human readable name for admin interface")
    fragment_key = Column(String(100), nullable=False,
                         comment="Identifier for the content fragment")
    
    content_type = Column(String(50), nullable=False, default='text/html',
                         comment="MIME type (text/html, text/plain, text/markdown)")

    # Enhanced versioning - version per fragment_key
    version_number = Column(Integer, nullable=False,
                           comment="Auto-incremented version number for this specific fragment_key")
    version_label = Column(String(20), nullable=True,
                          comment="Optional human-readable version label (e.g., 'v2.1', 'draft')")
    is_active = Column(Boolean, nullable=False, default=False,
                      comment="Whether this version of this fragment_key is currently active")

    # Store actual content
    content_source = Column(Text, nullable=False,
                           comment="The actual content (HTML/Markdown/Text)")
    content_hash = Column(String(64), nullable=True,
                         comment="SHA256 hash of content for change detection")
    
    # Template integration
    variables_data = Column(JSON, nullable=True,
                           comment="JSON data for template variables if using template fragments")
    template_fragment_key = Column(String(100), nullable=True,
                                  comment="Reference to TemplateFragment key if using template-based content")
    
    # Content metadata
    description = Column(Text, nullable=True,
                        comment="What this fragment contains and its purpose")
    sort_order = Column(Integer, nullable=False, default=0,
                       comment="Display order within fragment type")
    
    # Publishing control
    is_published = Column(Boolean, nullable=False, default=True,
                         comment="Whether this fragment should be shown to public")
    publish_date = Column(DateTime(timezone=True), nullable=True,
                         comment="When fragment was/will be published")
    expire_date = Column(DateTime(timezone=True), nullable=True,
                        comment="When fragment should be hidden")
    
    # Caching
    cache_duration = Column(Integer, nullable=False, default=3600,
                           comment="How long to cache this content (seconds)")
    last_rendered = Column(DateTime, nullable=True,
                          comment="When the content was last rendered")

    # Change tracking
    change_description = Column(Text, nullable=True,
                               comment="Description of changes in this version")
    created_by_user_uuid = Column(UUID(as_uuid=True), nullable=True,
                                 comment="UUID of user who created this version")

    # Relationships
    page = relationship("Page", back_populates="page_fragments")

    # Enhanced indexes and constraints
    __table_args__ = (
        Index('idx_page_fragments_page', 'page_uuid'),
        Index('idx_page_fragments_type', 'fragment_type'),
        Index('idx_page_fragments_key', 'fragment_key'),
        Index('idx_page_fragments_version_number', 'version_number'),
        Index('idx_page_fragments_hash', 'content_hash'),
        Index('idx_page_fragments_published', 'is_published'),
        Index('idx_page_fragments_sort_order', 'sort_order'),
        Index('idx_page_fragments_template_key', 'template_fragment_key'),

        # New indexes for versioning per fragment_key
        Index('idx_active_page_fragment_by_key', 'page_uuid', 'fragment_key', 'is_active'),
        Index('idx_page_fragment_version_lookup', 'page_uuid', 'fragment_key', 'version_number'),
        Index('idx_fragment_type_sort', 'page_uuid', 'fragment_type', 'sort_order'),
        Index('idx_page_fragments_publish_date', 'publish_date'),
        Index('idx_page_fragments_expire_date', 'expire_date'),

        # Ensure unique version numbers per page per fragment_key
        UniqueConstraint('page_uuid', 'fragment_key', 'version_number',
                        name='uq_page_fragments_page_fragment_version'),
        # Ensure unique fragment keys per page
        UniqueConstraint('page_uuid', 'fragment_key', 'is_active',
                        name='uq_page_fragments_key_active'),
    )

    def is_visible(self):
        """Check if fragment should be visible based on publish/expire dates"""
        now = datetime.datetime.now(datetime.timezone.utc)
        
        if not self.is_published:
            return False
            
        if self.publish_date and self.publish_date > now:
            return False
            
        if self.expire_date and self.expire_date <= now:
            return False
            
        return True

    @classmethod
    def get_next_version_number(cls, session, page_uuid, fragment_key):
        """Get the next version number for a given page and fragment_key"""
        from sqlalchemy import func
        max_version = session.query(func.max(cls.version_number))\
                           .filter_by(page_uuid=page_uuid,
                                    fragment_key=fragment_key)\
                           .scalar()
        return (max_version or 0) + 1

    @classmethod
    def get_active_version(cls, session, page_uuid, fragment_key):
        """Get the currently active version for a specific page and fragment_key"""
        return session.query(cls)\
                     .filter_by(page_uuid=page_uuid,
                               fragment_key=fragment_key,
                               is_active=True)\
                     .first()

    @classmethod
    def get_active_by_key(cls, session, page_uuid, fragment_key):
        """Get active fragment by page and fragment_key (includes visibility check)"""
        fragment = session.query(cls)\
                         .filter_by(page_uuid=page_uuid,
                                   fragment_key=fragment_key,
                                   is_active=True)\
                         .first()
        
        if fragment and fragment.is_visible():
            return fragment
        return None

    @classmethod
    def get_fragments_by_type(cls, session, page_uuid, fragment_type, include_hidden=False):
        """Get all active fragments of a specific type, ordered by sort_order"""
        fragments = session.query(cls)\
                          .filter_by(page_uuid=page_uuid,
                                    fragment_type=fragment_type,
                                    is_active=True)\
                          .order_by(cls.sort_order, cls.fragment_name)\
                          .all()
        
        if not include_hidden:
            fragments = [f for f in fragments if f.is_visible()]
            
        return fragments

    @classmethod
    def get_all_active_for_page(cls, session, page_uuid, include_hidden=False):
        """Get all active content pieces for a page (all active fragment_keys)"""
        fragments = session.query(cls)\
                          .filter_by(page_uuid=page_uuid, is_active=True)\
                          .order_by(cls.fragment_type, cls.sort_order)\
                          .all()
        
        if not include_hidden:
            fragments = [f for f in fragments if f.is_visible()]
            
        return fragments

    @classmethod
    def set_active_version(cls, session, fragment_uuid):
        """Set a specific version as active (deactivates other versions of same fragment_key)"""
        fragment = session.query(cls).filter_by(uuid=fragment_uuid).first()
        if not fragment:
            raise ValueError(f"Fragment with UUID {fragment_uuid} not found")

        # Deactivate all other versions for this page and fragment_key combination
        session.query(cls)\
               .filter_by(page_uuid=fragment.page_uuid,
                         fragment_key=fragment.fragment_key)\
               .update({'is_active': False})

        # Activate this version
        fragment.is_active = True
        session.commit()

        return fragment

    @classmethod
    def set_active_version_by_fragment_and_version(cls, session, page_uuid,
                                                  fragment_key, version_number):
        """Set active version by page, fragment_key, and version number"""
        fragment = session.query(cls)\
                         .filter_by(page_uuid=page_uuid,
                                   fragment_key=fragment_key,
                                   version_number=version_number)\
                         .first()

        if not fragment:
            raise ValueError(f"Fragment not found for page {page_uuid}, "
                           f"fragment_key {fragment_key}, version {version_number}")

        return cls.set_active_version(session, fragment.uuid)

    def activate(self, session):
        """Activate this version (convenience method)"""
        return self.__class__.set_active_version(session, self.uuid)

    def update_content_and_hash(self, new_content):
        """Update content source and recalculate hash"""
        import hashlib
        self.content_source = new_content
        self.content_hash = hashlib.sha256(new_content.encode('utf-8')).hexdigest()

    def get_display_version(self):
        """Get human-readable version string"""
        if self.version_label:
            return f"v{self.version_number} ({self.version_label})"
        return f"v{self.version_number}"

    def get_variables_data_dict(self):
        """Get variables data as a dict, handling None values"""
        return self.variables_data if self.variables_data else {}

    @classmethod
    def get_fragment_version_history(cls, session, page_uuid, fragment_key):
        """Get all versions for a specific page and fragment_key, ordered by version"""
        return session.query(cls)\
                     .filter_by(page_uuid=page_uuid,
                               fragment_key=fragment_key)\
                     .order_by(cls.version_number.desc())\
                     .all()

    @classmethod
    def get_page_fragment_structure(cls, session, page_uuid, include_hidden=False):
        """Get a summary of all fragment_keys and their active versions for a page"""
        fragments = session.query(
            cls.fragment_key,
            cls.fragment_type,
            cls.fragment_name,
            cls.version_number,
            cls.version_label,
            cls.content_type,
            cls.sort_order,
            cls.is_published,
            cls.publish_date,
            cls.expire_date,
            cls.created_at
        ).filter_by(
            page_uuid=page_uuid,
            is_active=True
        ).order_by(cls.fragment_type, cls.sort_order).all()

        if not include_hidden:
            now = datetime.datetime.now(datetime.timezone.utc)
            visible_fragments = []
            for f in fragments:
                if (f.is_published and 
                    (not f.publish_date or f.publish_date <= now) and 
                    (not f.expire_date or f.expire_date > now)):
                    visible_fragments.append(f)
            return visible_fragments

        return fragments