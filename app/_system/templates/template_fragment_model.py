from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer, Text, Index, UniqueConstraint, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.base.model import BaseModel


class TemplateFragment(BaseModel):
    """
    Template fragments model for storing Jinja2 template file references.

    Supports multiple content pieces per template (fragments) with versioning per template_file_path.
    Only one version of each template_file_path can be active at a time, but multiple different
    template_file_paths can be active simultaneously for a single template.

    Columns:
    - template_uuid: Foreign key to templates table
    - fragment_type: Semantic type (base, header, footer, nav, loop, container, etc.)
    - fragment_name: Human readable name for admin interface
    - fragment_key: Unique programmatic identifier for code access
    - template_file_path: Path to the actual Jinja2 template file
    - compiled_file_path: Path to the compiled template file (.pyc)
    - content_type: MIME type (text/html, text/plain, etc.)
    - version_number: Version number for this specific template_file_path
    - version_label: Optional human-readable version label
    - is_active: Whether this version of this template_file_path is active
    - template_source: Complete template source code content
    - template_hash: SHA256 hash of template content for change detection
    - variables_schema: JSON schema of expected template variables
    - sample_data: Example data for testing/preview
    - required_context: Context variables this fragment needs
    - dependencies: Other fragments this depends on
    - css_dependencies: CSS files needed for this fragment
    - js_dependencies: JavaScript files needed for this fragment
    - description: What this fragment does
    - usage_notes: Implementation notes for developers
    - preview_template: How to render for preview/admin
    - sort_order: Display order within fragment type
    - is_partial: Can be included in other fragments
    - cache_strategy: Fragment-specific caching rules
    - cache_duration: How long to cache this template (seconds)
    - last_compiled: When the template was last compiled
    """
    __depends_on__ = ['Template']  # Depends on Template
    __tablename__ = 'template_fragments'

    template_uuid = Column(UUID(as_uuid=True),
                          ForeignKey('templates.uuid', name='fk_template_fragments_template'),
                          nullable=False,
                          comment="Foreign key to templates table")
    
    # Fragment identification
    fragment_type = Column(String(50), nullable=False,
                          comment="Semantic fragment type (base, header, footer, nav, loop, container, etc.)")
    fragment_name = Column(String(100), nullable=False,
                          comment="Human readable name for admin interface")
    fragment_key = Column(String(100), nullable=False,
                         comment="Unique programmatic identifier for code access")
    
    # Template file information
    template_file_path = Column(String(500), nullable=False,
                               comment="Path to the actual Jinja2 template file")
    compiled_file_path = Column(String(500), nullable=True,
                               comment="Path to the compiled template file (.pyc)")
    content_type = Column(String(50), nullable=False, default='text/html',
                         comment="MIME type (text/html, text/plain, text/css)")

    # Enhanced versioning - version per template_file_path
    version_number = Column(Integer, nullable=False,
                           comment="Auto-incremented version number for this specific template_file_path")
    version_label = Column(String(20), nullable=True,
                          comment="Optional human-readable version label (e.g., 'v2.1', 'beta')")
    is_active = Column(Boolean, nullable=False, default=False,
                      comment="Whether this version of this template_file_path is currently active")

    # Store actual template content
    template_source = Column(Text, nullable=False,
                            comment="Complete template source code content")
    template_hash = Column(String(64), nullable=True,
                          comment="SHA256 hash of template content for change detection")
    
    # Template metadata and dependencies
    variables_schema = Column(JSON, nullable=True,
                             comment="JSON schema of expected template variables")
    sample_data = Column(JSON, nullable=True,
                        comment="Example data for testing/preview")
    required_context = Column(JSON, nullable=True,
                             comment="Context variables this fragment needs")
    dependencies = Column(JSON, nullable=True,
                         comment="Other fragments this depends on (array of fragment_keys)")
    css_dependencies = Column(JSON, nullable=True,
                             comment="CSS files needed for this fragment (array of paths)")
    js_dependencies = Column(JSON, nullable=True,
                            comment="JavaScript files needed for this fragment (array of paths)")
    
    # Documentation and usage
    description = Column(Text, nullable=True,
                        comment="What this fragment does and its purpose")
    usage_notes = Column(Text, nullable=True,
                        comment="Implementation notes and usage instructions for developers")
    preview_template = Column(Text, nullable=True,
                             comment="Template code for rendering previews in admin interface")
    
    # Ordering and behavior
    sort_order = Column(Integer, nullable=False, default=0,
                       comment="Display order within fragment type")
    is_partial = Column(Boolean, nullable=False, default=True,
                       comment="Can be included in other fragments")
    cache_strategy = Column(String(50), nullable=False, default='standard',
                           comment="Fragment-specific caching rules (standard, aggressive, none)")
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
    template = relationship("Template", back_populates="template_fragments")

    # Enhanced indexes and constraints
    __table_args__ = (
        Index('idx_template_fragments_template', 'template_uuid'),
        Index('idx_template_fragments_type', 'fragment_type'),
        Index('idx_template_fragments_key', 'fragment_key'),
        Index('idx_template_fragments_version_number', 'version_number'),
        Index('idx_template_fragments_file_path', 'template_file_path'),
        Index('idx_template_fragments_hash', 'template_hash'),
        Index('idx_template_fragments_sort_order', 'sort_order'),

        # New indexes for versioning per template_file_path
        Index('idx_active_template_fragment_by_file', 'template_uuid', 'template_file_path', 'is_active'),
        Index('idx_template_file_version_lookup', 'template_uuid', 'template_file_path', 'version_number'),
        Index('idx_template_fragment_type_sort', 'template_uuid', 'fragment_type', 'sort_order'),

        # Ensure unique version numbers per template per template_file_path
        UniqueConstraint('template_uuid', 'template_file_path', 'version_number',
                        name='uq_template_fragments_template_file_version'),
        # Ensure unique fragment keys per template
        UniqueConstraint('template_uuid', 'fragment_key', 'is_active',
                        name='uq_template_fragments_key_active'),
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
    def get_next_version_number(cls, session, template_uuid, template_file_path):
        """Get the next version number for a given template and template_file_path"""
        from sqlalchemy import func
        max_version = session.query(func.max(cls.version_number))\
                           .filter_by(template_uuid=template_uuid,
                                    template_file_path=template_file_path)\
                           .scalar()
        return (max_version or 0) + 1

    @classmethod
    def get_active_version(cls, session, template_uuid, template_file_path):
        """Get the currently active version for a specific template and template_file_path"""
        return session.query(cls)\
                     .filter_by(template_uuid=template_uuid,
                               template_file_path=template_file_path,
                               is_active=True)\
                     .first()

    @classmethod
    def get_active_by_key(cls, session, template_uuid, fragment_key):
        """Get active fragment by template and fragment_key"""
        return session.query(cls)\
                     .filter_by(template_uuid=template_uuid,
                               fragment_key=fragment_key,
                               is_active=True)\
                     .first()

    @classmethod
    def get_fragments_by_type(cls, session, template_uuid, fragment_type):
        """Get all active fragments of a specific type, ordered by sort_order"""
        return session.query(cls)\
                     .filter_by(template_uuid=template_uuid,
                               fragment_type=fragment_type,
                               is_active=True)\
                     .order_by(cls.sort_order, cls.fragment_name)\
                     .all()

    @classmethod
    def get_all_active_for_template(cls, session, template_uuid):
        """Get all active content pieces for a template (all active template_file_paths)"""
        return session.query(cls)\
                     .filter_by(template_uuid=template_uuid, is_active=True)\
                     .order_by(cls.fragment_type, cls.sort_order)\
                     .all()

    @classmethod
    def set_active_version(cls, session, fragment_uuid):
        """Set a specific version as active (deactivates other versions of same template_file_path)"""
        fragment = session.query(cls).filter_by(uuid=fragment_uuid).first()
        if not fragment:
            raise ValueError(f"Fragment with UUID {fragment_uuid} not found")

        # Deactivate all other versions for this template and template_file_path combination
        session.query(cls)\
               .filter_by(template_uuid=fragment.template_uuid,
                         template_file_path=fragment.template_file_path)\
               .update({'is_active': False})

        # Activate this version
        fragment.is_active = True
        session.commit()

        return fragment

    @classmethod
    def set_active_version_by_file_and_version(cls, session, template_uuid,
                                              template_file_path, version_number):
        """Set active version by template, template_file_path, and version number"""
        fragment = session.query(cls)\
                         .filter_by(template_uuid=template_uuid,
                                   template_file_path=template_file_path,
                                   version_number=version_number)\
                         .first()

        if not fragment:
            raise ValueError(f"Fragment not found for template {template_uuid}, "
                           f"file {template_file_path}, version {version_number}")

        return cls.set_active_version(session, fragment.uuid)

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

    def get_dependencies_list(self):
        """Get dependencies as a list, handling None values"""
        return self.dependencies if self.dependencies else []

    def get_css_dependencies_list(self):
        """Get CSS dependencies as a list, handling None values"""
        return self.css_dependencies if self.css_dependencies else []

    def get_js_dependencies_list(self):
        """Get JS dependencies as a list, handling None values"""
        return self.js_dependencies if self.js_dependencies else []

    def get_required_context_dict(self):
        """Get required context as a dict, handling None values"""
        return self.required_context if self.required_context else {}

    def get_sample_data_dict(self):
        """Get sample data as a dict, handling None values"""
        return self.sample_data if self.sample_data else {}

    @classmethod
    def get_file_version_history(cls, session, template_uuid, template_file_path):
        """Get all versions for a specific template and template_file_path, ordered by version"""
        return session.query(cls)\
                    .filter_by(template_uuid=template_uuid,
                            template_file_path=template_file_path)\
                    .order_by(cls.version_number.desc())\
                    .all()

    @classmethod
    def get_template_structure(cls, session, template_uuid):
        """Get a summary of all files and their active versions for a template"""
        from sqlalchemy import func

        # Get all unique template_file_paths with their active version info
        active_files = session.query(
            cls.template_file_path,
            cls.fragment_type,
            cls.fragment_key,
            cls.fragment_name,
            cls.version_number,
            cls.version_label,
            cls.content_type,
            cls.sort_order,
            cls.created_at
        ).filter_by(
            template_uuid=template_uuid,
            is_active=True
        ).order_by(cls.fragment_type, cls.sort_order).all()

        return active_files