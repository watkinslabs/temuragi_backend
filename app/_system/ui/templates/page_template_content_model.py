import uuid
import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer, Text, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app._system._core.base import BaseModel


class PageTemplateContent(BaseModel):
    """
    Page template content model for storing Jinja2 template file references.
    
    Supports multiple content pieces per template (fragments) with versioning per filename.
    Only one version of each filename can be active at a time, but multiple different
    filenames can be active simultaneously for a single template.

    Columns:
    - page_template_uuid: Foreign key to page_templates table
    - template_file_path: Path to the actual Jinja2 template file
    - compiled_file_path: Path to the compiled template file (.pyc)
    - content_type: MIME type (text/html, text/plain, etc.)
    - version_number: Version number for this specific filename
    - version_label: Optional human-readable version label
    - is_active: Whether this version of this filename is active
    - template_hash: SHA256 hash of template content for change detection
    - cache_duration: How long to cache this template (seconds)
    - last_compiled: When the template was last compiled
    """
    __depends_on__ = ['PageTemplate']  # Depends on PageTemplate
    __tablename__ = 'page_template_contents'

    page_template_uuid = Column(UUID(as_uuid=True),
                               ForeignKey('page_templates.uuid', name='fk_page_template_contents_template'),
                               nullable=False,
                               comment="Foreign key to page_templates table")
    template_file_path = Column(String(500), nullable=False,
                               comment="Path to the actual Jinja2 template file")
    compiled_file_path = Column(String(500), nullable=True,
                               comment="Path to the compiled template file (.pyc)")
    content_type = Column(String(50), nullable=False, default='text/html',
                         comment="MIME type (text/html, text/plain, text/css)")

    # Enhanced versioning - version per filename
    version_number = Column(Integer, nullable=False,
                           comment="Auto-incremented version number for this specific filename")
    version_label = Column(String(20), nullable=True,
                          comment="Optional human-readable version label (e.g., 'v2.1', 'beta')")
    is_active = Column(Boolean, nullable=False, default=False,
                      comment="Whether this version of this filename is currently active")

    # Store actual template content
    template_source = Column(Text, nullable=False,
                            comment="Complete template source code content")
    template_hash = Column(String(64), nullable=True,
                          comment="SHA256 hash of template content for change detection")
    cache_duration = Column(Integer, nullable=False, default=3600,
                           comment="How long to cache this template (seconds)")
    last_compiled = Column(DateTime, nullable=True,
                          comment="When the template was last compiled")

    # Change tracking
    change_description = Column(Text, nullable=True,
                               comment="Description of changes in this version")
    created_by_user_uuid = Column(UUID(as_uuid=True), nullable=True,
                                 comment="UUID of user who created this version")

    # Relationships
    page_template = relationship("PageTemplate", back_populates="template_contents")

    # Enhanced indexes and constraints
    __table_args__ = (
        Index('idx_page_template_contents_template', 'page_template_uuid'),
        Index('idx_page_template_contents_version_number', 'version_number'),
        Index('idx_page_template_contents_file_path', 'template_file_path'),
        Index('idx_page_template_contents_hash', 'template_hash'),

        # New indexes for versioning per filename
        Index('idx_active_template_content_by_file', 'page_template_uuid', 'template_file_path', 'is_active'),
        Index('idx_template_file_version_lookup', 'page_template_uuid', 'template_file_path', 'version_number'),

        # Ensure unique version numbers per template per filename
        UniqueConstraint('page_template_uuid', 'template_file_path', 'version_number',
                        name='uq_page_template_contents_template_file_version'),
    )

    def get_template_file_path(self):
        """Get the full path to the template file"""
        return self.template_file_path

    def get_compiled_file_path(self):
        """Get the full path to the compiled template file"""
        return self.compiled_file_path

    def needs_compilation(self):
        """Check if template needs to be compiled or recompiled"""
        import os
        import hashlib

        # No compiled file path set
        if not self.compiled_file_path:
            return True

        # Compiled file doesn't exist
        if not os.path.exists(self.compiled_file_path):
            return True

        # If we have template_source, check against that instead of file
        if self.template_source:
            current_hash = hashlib.sha256(self.template_source.encode('utf-8')).hexdigest()
            if current_hash != self.template_hash:
                return True
            return False

        # Fallback to file-based checking
        # Source file doesn't exist
        if not os.path.exists(self.template_file_path):
            return False

        # Check if source is newer than compiled
        source_mtime = os.path.getmtime(self.template_file_path)
        compiled_mtime = os.path.getmtime(self.compiled_file_path)

        if source_mtime > compiled_mtime:
            return True

        # Check hash if available
        if self.template_hash:
            with open(self.template_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            current_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
            if current_hash != self.template_hash:
                return True

        return False

    @classmethod
    def get_next_version_number(cls, session, page_template_uuid, template_file_path):
        """Get the next version number for a given template and filename"""
        from sqlalchemy import func
        max_version = session.query(func.max(cls.version_number))\
                           .filter_by(page_template_uuid=page_template_uuid,
                                    template_file_path=template_file_path)\
                           .scalar()
        return (max_version or 0) + 1

    @classmethod
    def get_active_version(cls, session, page_template_uuid, template_file_path):
        """Get the currently active version for a specific template and filename"""
        return session.query(cls)\
                     .filter_by(page_template_uuid=page_template_uuid,
                               template_file_path=template_file_path,
                               is_active=True)\
                     .first()

    @classmethod
    def get_all_active_for_template(cls, session, page_template_uuid):
        """Get all active content pieces for a template (all active filenames)"""
        return session.query(cls)\
                     .filter_by(page_template_uuid=page_template_uuid, is_active=True)\
                     .all()

    @classmethod
    def set_active_version(cls, session, content_uuid):
        """Set a specific version as active (deactivates other versions of same filename)"""
        content = session.query(cls).filter_by(uuid=content_uuid).first()
        if not content:
            raise ValueError(f"Content with UUID {content_uuid} not found")

        # Deactivate all other versions for this template and filename combination
        session.query(cls)\
               .filter_by(page_template_uuid=content.page_template_uuid,
                         template_file_path=content.template_file_path)\
               .update({'is_active': False})

        # Activate this version
        content.is_active = True
        session.commit()

        return content

    @classmethod
    def set_active_version_by_file_and_version(cls, session, page_template_uuid, 
                                              template_file_path, version_number):
        """Set active version by template, filename, and version number"""
        content = session.query(cls)\
                        .filter_by(page_template_uuid=page_template_uuid,
                                  template_file_path=template_file_path,
                                  version_number=version_number)\
                        .first()
        
        if not content:
            raise ValueError(f"Content not found for template {page_template_uuid}, "
                           f"file {template_file_path}, version {version_number}")
        
        return cls.set_active_version(session, content.uuid)

    def activate(self, session):
        """Activate this version (convenience method)"""
        return self.__class__.set_active_version(session, self.uuid)

    def update_content_and_hash(self, new_content):
        """Update template source and recalculate hash"""
        import hashlib
        self.template_source = new_content
        self.template_hash = hashlib.sha256(new_content.encode('utf-8')).hexdigest()

    def get_display_version(self):
        """Get human-readable version string"""
        if self.version_label:
            return f"v{self.version_number} ({self.version_label})"
        return f"v{self.version_number}"

    def get_filename_only(self):
        """Extract just the filename from template_file_path"""
        import os
        return os.path.basename(self.template_file_path)

    @classmethod
    def get_file_version_history(cls, session, page_template_uuid, template_file_path):
        """Get all versions for a specific template and filename, ordered by version"""
        return session.query(cls)\
                     .filter_by(page_template_uuid=page_template_uuid,
                               template_file_path=template_file_path)\
                     .order_by(cls.version_number.desc())\
                     .all()

    @classmethod
    def get_template_structure(cls, session, page_template_uuid):
        """Get a summary of all files and their active versions for a template"""
        from sqlalchemy import func
        
        # Get all unique filenames with their active version info
        active_files = session.query(
            cls.template_file_path,
            cls.version_number,
            cls.version_label,
            cls.content_type,
            cls.created_date
        ).filter_by(
            page_template_uuid=page_template_uuid,
            is_active=True
        ).all()
        
        return active_files