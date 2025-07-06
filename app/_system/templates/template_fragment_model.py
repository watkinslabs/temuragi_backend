import os
import hashlib
import logging
import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer, Text, Index, UniqueConstraint, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from flask import current_app, has_app_context

from app.base.model import BaseModel
from app.register.database import db_registry

class TemplateFragment(BaseModel):
    """
    Template fragments model for storing Jinja2 template file references.

    Supports multiple content pieces per template (fragments) with versioning per template_file_path.
    Only one version of each template_file_path can be active at a time, but multiple different
    template_file_paths can be active simultaneously for a single template.

    """
    __depends_on__ = ['Template']  # Depends on Template
    __tablename__ = 'template_fragments'

    template_id = Column(UUID(as_uuid=True),
                          ForeignKey('templates.id', name='fk_template_fragments_template'),
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
    created_by_user_id = Column(UUID(as_uuid=True), nullable=True,
                                 comment="UUID of user who created this version")

    # Relationships
    template = relationship("Template", back_populates="template_fragments")

    # Enhanced indexes and constraints
    __table_args__ = (
        Index('idx_template_fragments_template', 'template_id'),
        Index('idx_template_fragments_type', 'fragment_type'),
        Index('idx_template_fragments_key', 'fragment_key'),
        Index('idx_template_fragments_version_number', 'version_number'),
        Index('idx_template_fragments_file_path', 'template_file_path'),
        Index('idx_template_fragments_hash', 'template_hash'),
        Index('idx_template_fragments_sort_order', 'sort_order'),

        # New indexes for versioning per template_file_path
        Index('idx_active_template_fragment_by_file', 'template_id', 'template_file_path', 'is_active'),
        Index('idx_template_file_version_lookup', 'template_id', 'template_file_path', 'version_number'),
        Index('idx_template_fragment_type_sort', 'template_id', 'fragment_type', 'sort_order'),

        # Ensure unique version numbers per template per template_file_path
        UniqueConstraint('template_id', 'template_file_path', 'version_number',
                        name='uq_template_fragments_template_file_version'),
        # Ensure unique fragment keys per template
        UniqueConstraint('template_id', 'fragment_key', 'is_active',
                        name='uq_template_fragments_key_active'),
    )

    @staticmethod
    def _get_logger():
        """Get logger from Flask app context or create fallback"""
        if has_app_context():
            return current_app.logger
        else:
            return logging.getLogger('template_fragment')

    def get_template_file_path(self):
        """Get the full path to the template file"""
        return self.template_file_path

    def get_compiled_file_path(self):
        """Get the full path to the compiled template file"""
        return self.compiled_file_path

    def needs_compilation(self):
        """Check if template needs to be compiled or recompiled"""
        logger = self._get_logger()
        logger.debug(f"Checking compilation status for fragment '{self.fragment_key}'")

        # No compiled file path set
        if not self.compiled_file_path:
            logger.debug(f"Fragment '{self.fragment_key}' needs compilation: no compiled path set")
            return True

        # Compiled file doesn't exist
        if not os.path.exists(self.compiled_file_path):
            logger.debug(f"Fragment '{self.fragment_key}' needs compilation: compiled file missing")
            return True

        # If we have template_source, check against that instead of file
        if self.template_source:
            current_hash = hashlib.sha256(self.template_source.encode('utf-8')).hexdigest()
            if current_hash != self.template_hash:
                logger.info(f"Fragment '{self.fragment_key}' needs compilation: hash mismatch")
                return True
            logger.debug(f"Fragment '{self.fragment_key}' compilation up to date")
            return False

        # Fallback to file-based checking
        # Source file doesn't exist
        if not os.path.exists(self.template_file_path):
            logger.warning(f"Fragment '{self.fragment_key}' source file missing: {self.template_file_path}")
            return False

        # Check if source is newer than compiled
        source_mtime = os.path.getmtime(self.template_file_path)
        compiled_mtime = os.path.getmtime(self.compiled_file_path)

        if source_mtime > compiled_mtime:
            logger.info(f"Fragment '{self.fragment_key}' needs compilation: source newer than compiled")
            return True

        # Check hash if available
        if self.template_hash:
            with open(self.template_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            current_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
            if current_hash != self.template_hash:
                logger.info(f"Fragment '{self.fragment_key}' needs compilation: file hash changed")
                return True

        logger.debug(f"Fragment '{self.fragment_key}' compilation up to date")
        return False

    @classmethod
    def get_next_version_number(cls, template_id, template_file_path):
        """Get the next version number for a given template and template_file_path"""
        logger = cls._get_logger()
        logger.debug(f"Getting next version number for template {template_id}, file {template_file_path}")
        db_session=db_registry._routing_session()

        from sqlalchemy import func
        max_version = db_session.query(func.max(cls.version_number))\
                           .filter_by(template_id=template_id,
                                    template_file_path=template_file_path)\
                           .scalar()
        
        next_version = (max_version or 0) + 1
        logger.debug(f"Next version number for {template_file_path}: {next_version}")
        return next_version

    @classmethod
    def get_active_version(cls, template_id, template_file_path):
        """Get the currently active version for a specific template and template_file_path"""
        db_session=db_registry._routing_session()
        fragment = db_session.query(cls)\
                         .filter_by(template_id=template_id,
                                   template_file_path=template_file_path,
                                   is_active=True)\
                         .first()
        
        return fragment

    @classmethod
    def get_active_by_key(cls, template_id, fragment_key):
        """Get active fragment by template and fragment_key"""
        db_session=db_registry._routing_session()
        
        fragment = db_session.query(cls)\
                         .filter_by(template_id=template_id,
                                   fragment_key=fragment_key,
                                   is_active=True)\
                         .first()
        
        
        return fragment

    @classmethod
    def get_fragments_by_type(cls, template_id, fragment_type):
        """Get all active fragments of a specific type, ordered by sort_order"""
        db_session=db_registry._routing_session()
        logger = cls._get_logger()
        logger.debug(f"Getting fragments by type '{fragment_type}' for template {template_id}")
        
        fragments = db_session.query(cls)\
                          .filter_by(template_id=template_id,
                                    fragment_type=fragment_type,
                                    is_active=True)\
                          .order_by(cls.sort_order, cls.fragment_name)\
                          .all()
        
        logger.debug(f"Found {len(fragments)} active fragments of type '{fragment_type}'")
        return fragments

    @classmethod
    def get_all_active_for_template(cls, template_id):
        """Get all active content pieces for a template (all active template_file_paths)"""
        db_session=db_registry._routing_session()
        logger = cls._get_logger()
        logger.debug(f"Getting all active fragments for template {template_id}")
        
        fragments = db_session.query(cls)\
                          .filter_by(template_id=template_id, is_active=True)\
                          .order_by(cls.fragment_type, cls.sort_order)\
                          .all()
        
        fragment_types = {}
        for fragment in fragments:
            if fragment.fragment_type not in fragment_types:
                fragment_types[fragment.fragment_type] = 0
            fragment_types[fragment.fragment_type] += 1
        
        logger.info(f"Retrieved {len(fragments)} active fragments for template {template_id}: {fragment_types}")
        return fragments

    @classmethod
    def set_active_version(cls, fragment_id):
        """Set a specific version as active (deactivates other versions of same template_file_path)"""
        db_session=db_registry._routing_session()
        logger = cls._get_logger()
        logger.info(f"Setting active version for fragment UUID {fragment_id}")
        
        fragment = db_session.query(cls).filter_by(id=fragment_id).first()
        if not fragment:
            logger.error(f"Fragment with UUID {fragment_id} not found")
            raise ValueError(f"Fragment with UUID {fragment_id} not found")

        # Deactivate all other versions for this template and template_file_path combination
        updated_count = db_session.query(cls)\
                              .filter_by(template_id=fragment.template_id,
                                        template_file_path=fragment.template_file_path)\
                              .update({'is_active': False})
        
        logger.debug(f"Deactivated {updated_count} versions of file {fragment.template_file_path}")

        # Activate this version
        fragment.is_active = True
        fragment.last_compiled = datetime.datetime.now(datetime.timezone.utc)
        db_session.commit()
        
        logger.info(f"Activated fragment '{fragment.fragment_key}' version {fragment.version_number}")
        return fragment

    @classmethod
    def set_active_version_by_file_and_version(cls, template_id,
                                              template_file_path, version_number):
        """Set active version by template, template_file_path, and version number"""
        db_session=db_registry._routing_session()
        logger = cls._get_logger()
        logger.info(f"Setting active version: template {template_id}, file {template_file_path}, version {version_number}")
        
        fragment = db_session.query(cls)\
                         .filter_by(template_id=template_id,
                                   template_file_path=template_file_path,
                                   version_number=version_number)\
                         .first()

        if not fragment:
            logger.error(f"Fragment not found for template {template_id}, file {template_file_path}, version {version_number}")
            raise ValueError(f"Fragment not found for template {template_id}, "
                           f"file {template_file_path}, version {version_number}")

        return cls.set_active_version(db_session, fragment.id)

    def activate(self):
        """Activate this version (convenience method)"""
        db_session=db_registry._routing_session()
        logger = self._get_logger()
        logger.info(f"Activating fragment '{self.fragment_key}' version {self.version_number}")
        return self.__class__.set_active_version(db_session, self.id)

    def update_content_and_hash(self, new_content):
        """Update template source and recalculate hash"""
        logger = self._get_logger()
        logger.debug(f"Updating content for fragment '{self.fragment_key}' (new length: {len(new_content)})")
        
        old_hash = self.template_hash
        self.template_source = new_content
        self.template_hash = hashlib.sha256(new_content.encode('utf-8')).hexdigest()
        
        logger.info(f"Updated content hash for fragment '{self.fragment_key}': {old_hash} -> {self.template_hash}")

    def get_display_version(self):
        """Get human-readable version string"""
        if self.version_label:
            return f"v{self.version_number} ({self.version_label})"
        return f"v{self.version_number}"

    def get_filename_only(self):
        """Extract just the filename from template_file_path"""
        return os.path.basename(self.template_file_path)

    def get_dependencies_list(self):
        """Get dependencies as a list, handling None values"""
        deps = self.dependencies if self.dependencies else []
        if deps:
            logger = self._get_logger()
            logger.debug(f"Fragment '{self.fragment_key}' has {len(deps)} dependencies: {deps}")
        return deps

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

    def validate_dependencies(self):
        """Validate that all declared dependencies exist"""
        db_session=db_registry._routing_session()
        logger = self._get_logger()
        dependencies = self.get_dependencies_list()
        
        if not dependencies:
            logger.debug(f"Fragment '{self.fragment_key}' has no dependencies to validate")
            return True
        
        logger.debug(f"Validating {len(dependencies)} dependencies for fragment '{self.fragment_key}'")
        
        missing_deps = []
        for dep_key in dependencies:
            dep_fragment = self.__class__.get_active_by_key(db_session, self.template_id, dep_key)
            if not dep_fragment:
                missing_deps.append(dep_key)
        
        if missing_deps:
            logger.warning(f"Fragment '{self.fragment_key}' has missing dependencies: {missing_deps}")
            return False
        
        logger.debug(f"All dependencies validated for fragment '{self.fragment_key}'")
        return True

    @classmethod
    def get_file_version_history(cls,  template_id, template_file_path):
        """Get all versions for a specific template and template_file_path, ordered by version"""
        db_session=db_registry._routing_session()
        logger = cls._get_logger()
        logger.debug(f"Getting version history for template {template_id}, file {template_file_path}")
        
        versions = db_session.query(cls)\
                         .filter_by(template_id=template_id,
                                   template_file_path=template_file_path)\
                         .order_by(cls.version_number.desc())\
                         .all()
        
        logger.debug(f"Found {len(versions)} versions of file {template_file_path}")
        return versions

    @classmethod
    def get_template_structure(cls, template_id):
        """Get a summary of all files and their active versions for a template"""
        db_session=db_registry._routing_session()
        logger = cls._get_logger()
        logger.debug(f"Getting template structure for template {template_id}")
        
        # Get all unique template_file_paths with their active version info
        active_files = db_session.query(
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
            template_id=template_id,
            is_active=True
        ).order_by(cls.fragment_type, cls.sort_order).all()

        # Log structure summary
        structure_summary = {}
        for file_info in active_files:
            if file_info.fragment_type not in structure_summary:
                structure_summary[file_info.fragment_type] = 0
            structure_summary[file_info.fragment_type] += 1
        
        logger.debug(f"Template structure for {template_id}: {len(active_files)} active files, types: {structure_summary}")
        return active_files

    @classmethod
    def find_circular_dependencies(cls, template_id):
        """Check for circular dependencies within template fragments"""
        db_session=db_registry._routing_session()
        logger = cls._get_logger()
        logger.debug(f"Checking for circular dependencies in template {template_id}")
        
        fragments = cls.get_all_active_for_template(db_session, template_id)
        
        # Build dependency graph
        dependency_graph = {}
        for fragment in fragments:
            dependencies = fragment.get_dependencies_list()
            dependency_graph[fragment.fragment_key] = dependencies
        
        # Check for cycles using DFS
        visited = set()
        rec_stack = set()
        
        def has_cycle(node, path):
            if node in rec_stack:
                cycle_path = path[path.index(node):] + [node]
                logger.warning(f"Circular dependency detected in template {template_id}: {' -> '.join(cycle_path)}")
                return True
            
            if node in visited:
                return False
            
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in dependency_graph.get(node, []):
                if has_cycle(neighbor, path):
                    return True
            
            rec_stack.remove(node)
            path.pop()
            return False
        
        cycles_found = []
        for fragment_key in dependency_graph:
            if fragment_key not in visited:
                if has_cycle(fragment_key, []):
                    cycles_found.append(fragment_key)
        
        if cycles_found:
            logger.error(f"Circular dependencies found in template {template_id}: {cycles_found}")
        else:
            logger.debug(f"No circular dependencies found in template {template_id}")
        
        return len(cycles_found) == 0

    def get_compilation_info(self):
        """Get compilation status information"""
        logger = self._get_logger()
        
        info = {
            'needs_compilation': self.needs_compilation(),
            'has_compiled_path': bool(self.compiled_file_path),
            'compiled_file_exists': bool(self.compiled_file_path and os.path.exists(self.compiled_file_path)),
            'template_hash': self.template_hash,
            'last_compiled': self.last_compiled,
            'source_length': len(self.template_source) if self.template_source else 0
        }
        
        logger.debug(f"Compilation info for fragment '{self.fragment_key}': {info}")
        return info

    def __repr__(self):
        return f"<TemplateFragment(key='{self.fragment_key}', type='{self.fragment_type}', version={self.version_number}, active={self.is_active})>"