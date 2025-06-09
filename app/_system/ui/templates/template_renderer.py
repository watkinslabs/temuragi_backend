import os
import yaml
import uuid
import hashlib
import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional, Union, List
from dataclasses import dataclass
from jinja2 import Environment, BaseLoader, Template as Jinja2Template
from jinja2.exceptions import TemplateError, TemplateNotFound
from sqlalchemy.orm import Session

from app._system._core.base import BaseModel
from .template_model import Template
from .template_fragment_model import TemplateFragment
from .page_model import Page
from .page_fragment_model import PageFragment


@dataclass
class RenderResult:
    """Result of a template render operation"""
    content: str
    template_uuid: str
    template_name: str
    fragments_rendered: List[str]
    render_time_ms: float
    cache_key: Optional[str] = None
    cache_hit: bool = False
    errors: List[str] = None
    warnings: List[str] = None


@dataclass
class CacheEntry:
    """Cache entry for rendered content"""
    content: str
    timestamp: float
    template_hash: str
    data_hash: str
    fragments_hash: str
    cache_duration: int


class DatabaseTemplateLoader(BaseLoader):
    """Custom Jinja2 loader that loads templates from database fragments"""
    
    def __init__(self, session: Session, template_uuid: uuid.UUID):
        self.session = session
        self.template_uuid = template_uuid
        self._fragment_cache = {}
        
        # Get template's module info for scoping
        template = session.query(Template).filter_by(uuid=template_uuid).first()
        self.template_module_uuid = template.module_uuid if template else None
        self.is_system_template = template.is_system if template else False
    
    def get_source(self, environment, template):
        """Load template source from database with module scoping"""
        fragment = None
        
        # Try by fragment_key first (within module scope)
        if self.is_system_template or self.template_module_uuid is None:
            # System template - can access system fragments
            fragment = self.session.query(TemplateFragment).filter_by(
                template_uuid=self.template_uuid,
                fragment_key=template,
                is_active=True
            ).first()
        else:
            # Module template - only access fragments from same module
            fragment = self.session.query(TemplateFragment)\
                .join(Template, TemplateFragment.template_uuid == Template.uuid)\
                .filter(
                    TemplateFragment.fragment_key == template,
                    TemplateFragment.is_active == True,
                    Template.module_uuid == self.template_module_uuid
                ).first()
        
        # If not found by key, try by template_file_path (with module scoping)
        if not fragment:
            if self.is_system_template or self.template_module_uuid is None:
                # System template - search all system fragments
                fragments = self.session.query(TemplateFragment)\
                    .join(Template, TemplateFragment.template_uuid == Template.uuid)\
                    .filter(
                        TemplateFragment.is_active == True,
                        Template.is_system == True
                    ).all()
            else:
                # Module template - only search within same module
                fragments = self.session.query(TemplateFragment)\
                    .join(Template, TemplateFragment.template_uuid == Template.uuid)\
                    .filter(
                        TemplateFragment.is_active == True,
                        Template.module_uuid == self.template_module_uuid
                    ).all()
            
            for frag in fragments:
                if frag.template_file_path == template or frag.template_file_path.endswith(f"/{template}"):
                    fragment = frag
                    break
        
        if not fragment or not fragment.template_source:
            raise TemplateNotFound(template)
        
        # Use fragment's updated_at for cache invalidation
        mtime = fragment.updated_at.timestamp() if fragment.updated_at else time.time()
        
        # Create uptodate function
        def uptodate():
            current_fragment = self.session.query(TemplateFragment).filter_by(
                uuid=fragment.uuid, is_active=True
            ).first()
            if not current_fragment:
                return False
            current_mtime = current_fragment.updated_at.timestamp() if current_fragment.updated_at else 0
            return current_mtime <= mtime
        
        return fragment.template_source, template, uptodate


class TemplateRenderer:
    """
    Template rendering engine for the template system.
    Supports rendering templates with template fragments and page fragments.
    Includes intelligent caching with invalidation.
    """
    
    def __init__(self, session: Session, templates_base_path: str = "templates",
                 compiled_templates_path: str = "compiled_templates",
                 cache_enabled: bool = True, default_cache_duration: int = 3600,
                 logger: Optional[logging.Logger] = None):
        """
        Initialize the template renderer
        
        Args:
            session: SQLAlchemy session for database access
            templates_base_path: Base path for template files (fallback)
            compiled_templates_path: Path for compiled template cache
            cache_enabled: Whether to enable template caching
            default_cache_duration: Default cache duration in seconds
            logger: Optional logger instance
        """
        self.session = session
        self.templates_base_path = Path(templates_base_path)
        self.compiled_templates_path = Path(compiled_templates_path)
        self.cache_enabled = cache_enabled
        self.default_cache_duration = default_cache_duration
        self.logger = logger or self._setup_logger()
        
        # Template cache - stores compiled Jinja2 templates
        self._template_cache: Dict[str, Jinja2Template] = {}
        # Content cache - stores rendered output
        self._content_cache: Dict[str, CacheEntry] = {}
        # Environment cache - stores Jinja2 environments per template
        self._env_cache: Dict[str, Environment] = {}
        
        self.logger.info(f"TemplateRenderer initialized - cache_enabled: {cache_enabled}")

    def _setup_logger(self) -> logging.Logger:
        """Setup default logger if none provided"""
        logger = logging.getLogger('template_renderer')
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

    def _get_jinja_environment(self, template_uuid: uuid.UUID) -> Environment:
        """Get or create Jinja2 environment for a template"""
        cache_key = f"env_{template_uuid}"
        
        if cache_key in self._env_cache:
            return self._env_cache[cache_key]
        
        # Create environment with custom loader
        env = Environment(
            loader=DatabaseTemplateLoader(self.session, template_uuid),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Register custom functions
        self._register_template_functions(env, template_uuid)
        
        if self.cache_enabled:
            self._env_cache[cache_key] = env
        
        return env

    def _register_template_functions(self, env: Environment, template_uuid: uuid.UUID):
        """Register custom Jinja2 functions and filters"""
        
        def render_page_fragment(fragment_key: str, page_uuid: str = None) -> str:
            """Render a page fragment by key"""
            if not page_uuid:
                return f"<!-- Page fragment '{fragment_key}' requires page_uuid -->"
                
            try:
                fragment = PageFragment.get_active_by_key(
                    self.session, page_uuid, fragment_key
                )
                if fragment and fragment.is_visible():
                    return fragment.content_source
                return f"<!-- Page fragment '{fragment_key}' not found or not visible -->"
            except Exception as e:
                self.logger.error(f"Error rendering page fragment {fragment_key}: {e}")
                return f"<!-- Error rendering page fragment '{fragment_key}' -->"
        
        def get_template_fragment_content(fragment_key: str) -> str:
            """Get template fragment content by key"""
            try:
                fragment = TemplateFragment.get_active_by_key(
                    self.session, template_uuid, fragment_key
                )
                if fragment:
                    return fragment.template_source
                return f"<!-- Template fragment '{fragment_key}' not found -->"
            except Exception as e:
                self.logger.error(f"Error getting template fragment {fragment_key}: {e}")
                return f"<!-- Error getting template fragment '{fragment_key}' -->"
        
        def include_fragment(fragment_key: str, **kwargs) -> str:
            """Include and render a template fragment with optional data"""
            try:
                fragment = TemplateFragment.get_active_by_key(
                    self.session, template_uuid, fragment_key
                )
                if not fragment or not fragment.template_source:
                    return f"<!-- Fragment '{fragment_key}' not found -->"
                
                # Create mini-environment for fragment
                fragment_template = env.from_string(fragment.template_source)
                return fragment_template.render(**kwargs)
            except Exception as e:
                self.logger.error(f"Error including fragment {fragment_key}: {e}")
                return f"<!-- Error including fragment '{fragment_key}' -->"
        
        # Register functions
        env.globals['render_page_fragment'] = render_page_fragment
        env.globals['get_template_fragment_content'] = get_template_fragment_content
        env.globals['include_fragment'] = include_fragment

    def render_template_by_uuid(self, template_uuid: Union[str, uuid.UUID], 
                               data: Union[Dict[str, Any], str, Path] = None,
                               page_uuid: Union[str, uuid.UUID] = None,
                               force_refresh: bool = False) -> RenderResult:
        """
        Render a template by UUID with provided data
        
        Args:
            template_uuid: UUID of template to render
            data: Data for template (dict, YAML file path, or None)
            page_uuid: Optional page UUID for page-specific rendering
            force_refresh: Force cache refresh even if cache is valid
            
        Returns:
            RenderResult with rendered content and metadata
        """
        start_time = time.time()
        
        self.logger.info(f"Rendering template {template_uuid} (force_refresh={force_refresh})")
        
        # Convert UUID strings
        if isinstance(template_uuid, str):
            template_uuid = uuid.UUID(template_uuid)
        if isinstance(page_uuid, str):
            page_uuid = uuid.UUID(page_uuid)
        
        errors = []
        warnings = []
        fragments_rendered = []
        cache_hit = False
        
        try:
            # Get template from database
            template = self.session.query(Template).filter_by(uuid=template_uuid).first()
            if not template:
                raise ValueError(f"Template with UUID {template_uuid} not found")
            
            # Load and prepare data
            template_data = self._prepare_data(data)
            
            # Generate cache key
            cache_key = self._generate_cache_key(template_uuid, template_data, page_uuid)
            
            # Check cache first (if enabled and not forcing refresh)
            if self.cache_enabled and not force_refresh and cache_key:
                cached_result = self._get_cached_content(cache_key, template_uuid, template_data, page_uuid)
                if cached_result:
                    render_time_ms = (time.time() - start_time) * 1000
                    self.logger.info(f"Cache hit for template {template.name} ({render_time_ms:.2f}ms)")
                    
                    return RenderResult(
                        content=cached_result.content,
                        template_uuid=str(template_uuid),
                        template_name=template.name,
                        fragments_rendered=cached_result.content.count('fragment_key='),  # Rough estimate
                        render_time_ms=render_time_ms,
                        cache_key=cache_key,
                        cache_hit=True
                    )
            
            # Add template and page context
            template_data['template'] = template
            template_data['template_uuid'] = str(template_uuid)
            
            if page_uuid:
                page = self.session.query(Page).filter_by(uuid=page_uuid).first()
                if page:
                    template_data['page'] = page
                    template_data['page_uuid'] = str(page_uuid)
                    
                    # Load page fragments
                    page_fragments = PageFragment.get_all_active_for_page(
                        self.session, page_uuid, include_hidden=False
                    )
                    template_data['page_fragments'] = page_fragments
                    fragments_rendered.extend([f.fragment_key for f in page_fragments])
                else:
                    warnings.append(f"Page with UUID {page_uuid} not found")
            
            # Get active template fragments
            template_fragments = TemplateFragment.get_all_active_for_template(
                self.session, template_uuid
            )
            template_data['template_fragments'] = template_fragments
            fragments_rendered.extend([f.fragment_key for f in template_fragments])
            
            # Render template
            rendered_content = self._render_template_file(template, template_data)
            
            # Cache the result if caching is enabled
            if self.cache_enabled and cache_key:
                self._cache_content(cache_key, rendered_content, template_uuid, template_data, page_uuid)
            
            # Calculate render time
            render_time_ms = (time.time() - start_time) * 1000
            
            result = RenderResult(
                content=rendered_content,
                template_uuid=str(template_uuid),
                template_name=template.name,
                fragments_rendered=fragments_rendered,
                render_time_ms=render_time_ms,
                cache_key=cache_key,
                cache_hit=cache_hit,
                errors=errors if errors else None,
                warnings=warnings if warnings else None
            )
            
            self.logger.info(f"Template {template.name} rendered successfully in {render_time_ms:.2f}ms")
            return result
            
        except Exception as e:
            self.logger.error(f"Error rendering template {template_uuid}: {e}")
            render_time_ms = (time.time() - start_time) * 1000
            
            return RenderResult(
                content=f"<div class='error'>Template rendering failed: {str(e)}</div>",
                template_uuid=str(template_uuid),
                template_name="ERROR",
                fragments_rendered=[],
                render_time_ms=render_time_ms,
                cache_hit=False,
                errors=[str(e)]
            )

    def render_page_by_uuid(self, page_uuid: Union[str, uuid.UUID],
                           data: Union[Dict[str, Any], str, Path] = None,
                           force_refresh: bool = False) -> RenderResult:
        """
        Render a page by UUID (uses the page's assigned template)
        
        Args:
            page_uuid: UUID of page to render
            data: Additional data for template
            force_refresh: Force cache refresh even if cache is valid
            
        Returns:
            RenderResult with rendered content and metadata
        """
        if isinstance(page_uuid, str):
            page_uuid = uuid.UUID(page_uuid)
        
        self.logger.info(f"Rendering page {page_uuid}")
        
        # Get page from database
        page = self.session.query(Page).filter_by(uuid=page_uuid).first()
        if not page:
            raise ValueError(f"Page with UUID {page_uuid} not found")
        
        if not page.template_uuid:
            raise ValueError(f"Page {page.name} has no template assigned")
        
        # Render using the page's template
        return self.render_template_by_uuid(
            template_uuid=page.template_uuid,
            data=data,
            page_uuid=page_uuid,
            force_refresh=force_refresh
        )

    def _get_cached_content(self, cache_key: str, template_uuid: uuid.UUID, 
                           data: Dict[str, Any], page_uuid: Optional[uuid.UUID] = None) -> Optional[CacheEntry]:
        """Check if cached content is still valid"""
        if cache_key not in self._content_cache:
            return None
        
        cache_entry = self._content_cache[cache_key]
        current_time = time.time()
        
        # Check if cache has expired
        if current_time - cache_entry.timestamp > cache_entry.cache_duration:
            self.logger.debug(f"Cache expired for key {cache_key}")
            del self._content_cache[cache_key]
            return None
        
        # Check if template or fragments have been updated
        if not self._is_cache_valid(cache_entry, template_uuid, data, page_uuid):
            self.logger.debug(f"Cache invalidated for key {cache_key}")
            del self._content_cache[cache_key]
            return None
        
        return cache_entry

    def _is_cache_valid(self, cache_entry: CacheEntry, template_uuid: uuid.UUID,
                       data: Dict[str, Any], page_uuid: Optional[uuid.UUID] = None) -> bool:
        """Check if cache is still valid by comparing hashes"""
        # Check data hash
        current_data_hash = self._hash_data(data)
        if current_data_hash != cache_entry.data_hash:
            return False
        
        # Check template and fragments hash
        current_fragments_hash = self._get_fragments_hash(template_uuid, page_uuid)
        if current_fragments_hash != cache_entry.fragments_hash:
            return False
        
        return True

    def _cache_content(self, cache_key: str, content: str, template_uuid: uuid.UUID,
                      data: Dict[str, Any], page_uuid: Optional[uuid.UUID] = None):
        """Cache rendered content with metadata"""
        # Get cache duration from template fragments
        template_fragments = TemplateFragment.get_all_active_for_template(
            self.session, template_uuid
        )
        
        # Use minimum cache duration from all fragments, or default
        cache_duration = self.default_cache_duration
        for fragment in template_fragments:
            if fragment.cache_duration and fragment.cache_duration < cache_duration:
                cache_duration = fragment.cache_duration
        
        cache_entry = CacheEntry(
            content=content,
            timestamp=time.time(),
            template_hash="",  # Not used currently but could be added
            data_hash=self._hash_data(data),
            fragments_hash=self._get_fragments_hash(template_uuid, page_uuid),
            cache_duration=cache_duration
        )
        
        self._content_cache[cache_key] = cache_entry
        self.logger.debug(f"Cached content for key {cache_key} (duration: {cache_duration}s)")

    def _get_fragments_hash(self, template_uuid: uuid.UUID, 
                           page_uuid: Optional[uuid.UUID] = None) -> str:
        """Generate hash of all relevant fragments for cache validation"""
        hash_components = []
        
        # Template fragments
        template_fragments = TemplateFragment.get_all_active_for_template(
            self.session, template_uuid
        )
        for fragment in template_fragments:
            hash_components.append(f"{fragment.uuid}:{fragment.template_hash}:{fragment.updated_at}")
        
        # Page fragments if page_uuid provided
        if page_uuid:
            page_fragments = PageFragment.get_all_active_for_page(
                self.session, page_uuid, include_hidden=False
            )
            for fragment in page_fragments:
                hash_components.append(f"{fragment.uuid}:{fragment.content_hash}:{fragment.updated_at}")
        
        combined = "|".join(sorted(hash_components))
        return hashlib.md5(combined.encode()).hexdigest()

    def _hash_data(self, data: Dict[str, Any]) -> str:
        """Generate hash of template data for cache validation"""
        # Remove non-hashable items like model instances
        hashable_data = {}
        for key, value in data.items():
            if key in ['template', 'page', 'template_fragments', 'page_fragments']:
                continue  # Skip model instances
            try:
                # Try to convert to string for hashing
                hashable_data[key] = str(value)
            except:
                continue
        
        data_str = str(sorted(hashable_data.items()))
        return hashlib.md5(data_str.encode()).hexdigest()

    def _prepare_data(self, data: Union[Dict[str, Any], str, Path]) -> Dict[str, Any]:
        """
        Prepare template data from various input formats
        
        Args:
            data: Data as dict, YAML file path, or None
            
        Returns:
            Dictionary of template data
        """
        if data is None:
            return {}
        
        if isinstance(data, dict):
            return data.copy()
        
        # Handle file path (string or Path object)
        file_path = Path(data)
        
        if not file_path.exists():
            self.logger.warning(f"Data file not found: {file_path}")
            return {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if file_path.suffix.lower() in ['.yaml', '.yml']:
                    return yaml.safe_load(f) or {}
                elif file_path.suffix.lower() == '.json':
                    import json
                    return json.load(f)
                else:
                    self.logger.warning(f"Unsupported data file format: {file_path.suffix}")
                    return {}
        except Exception as e:
            self.logger.error(f"Error loading data file {file_path}: {e}")
            return {}

    def _render_template_file(self, template: Template, data: Dict[str, Any]) -> str:
        """
        Render a template using base fragment
        
        Args:
            template: Template model instance
            data: Template data dictionary
            
        Returns:
            Rendered template content
        """
        # Get Jinja2 environment for this template
        env = self._get_jinja_environment(template.uuid)
        
        # Find the base fragment for this template
        base_fragment = self.session.query(TemplateFragment).filter_by(
            template_uuid=template.uuid,
            fragment_type='base',
            is_active=True
        ).first()
        
        if not base_fragment or not base_fragment.template_source:
            raise TemplateError(f"Base fragment not found for template {template.name}")
        
        try:
            # Use the base fragment's key as the template name for the loader
            jinja_template = env.get_template(base_fragment.fragment_key)
            return jinja_template.render(**data)
        except TemplateNotFound as e:
            # Fallback: try to render directly from source
            self.logger.warning(f"Template not found via loader, using direct rendering: {e}")
            jinja_template = env.from_string(base_fragment.template_source)
            return jinja_template.render(**data)
        except Exception as e:
            self.logger.error(f"Error rendering template {template.name}: {e}")
            raise TemplateError(f"Template rendering failed: {str(e)}")

    def _generate_cache_key(self, template_uuid: uuid.UUID, data: Dict[str, Any], 
                           page_uuid: Optional[uuid.UUID] = None) -> str:
        """Generate cache key for rendered content"""
        if not self.cache_enabled:
            return None
        
        # Create a hash of the data for cache key
        data_hash = self._hash_data(data)
        
        key_parts = [str(template_uuid), data_hash]
        if page_uuid:
            key_parts.append(str(page_uuid))
        
        return "_".join(key_parts)

    def render_fragment_by_key(self, fragment_key: str, template_uuid: Union[str, uuid.UUID],
                              data: Dict[str, Any] = None) -> str:
        """
        Render a specific template fragment by key
        
        Args:
            fragment_key: Fragment key to render
            template_uuid: UUID of template containing the fragment
            data: Template data
            
        Returns:
            Rendered fragment content
        """
        if isinstance(template_uuid, str):
            template_uuid = uuid.UUID(template_uuid)
        
        fragment = TemplateFragment.get_active_by_key(
            self.session, template_uuid, fragment_key
        )
        
        if not fragment:
            return f"<!-- Template fragment '{fragment_key}' not found -->"
        
        if not fragment.template_source:
            return f"<!-- Template fragment '{fragment_key}' has no content -->"
        
        try:
            env = self._get_jinja_environment(template_uuid)
            jinja_template = env.from_string(fragment.template_source)
            return jinja_template.render(**(data or {}))
        except Exception as e:
            self.logger.error(f"Error rendering fragment {fragment_key}: {e}")
            return f"<!-- Error rendering fragment '{fragment_key}': {str(e)} -->"

    def render_page_fragment_by_key(self, fragment_key: str, page_uuid: Union[str, uuid.UUID],
                                   data: Dict[str, Any] = None) -> str:
        """
        Render a specific page fragment by key
        
        Args:
            fragment_key: Fragment key to render
            page_uuid: UUID of page containing the fragment
            data: Template data (for processing if fragment uses template syntax)
            
        Returns:
            Rendered fragment content
        """
        if isinstance(page_uuid, str):
            page_uuid = uuid.UUID(page_uuid)
        
        fragment = PageFragment.get_active_by_key(
            self.session, page_uuid, fragment_key
        )
        
        if not fragment or not fragment.is_visible():
            return f"<!-- Page fragment '{fragment_key}' not found or not visible -->"
        
        content = fragment.content_source
        
        # If content contains template syntax and data provided, render it
        if data and ('{{' in content or '{%' in content):
            try:
                # Create a basic environment for page fragments
                env = Environment(autoescape=True)
                jinja_template = env.from_string(content)
                return jinja_template.render(**data)
            except Exception as e:
                self.logger.error(f"Error rendering page fragment {fragment_key}: {e}")
                return content  # Return raw content if template rendering fails
        
        return content

    def render_base_template(self, template_uuid: Union[str, uuid.UUID], 
                           data: Union[Dict[str, Any], str, Path] = None,
                           page_uuid: Union[str, uuid.UUID] = None,
                           force_refresh: bool = False) -> RenderResult:
        """Render template using base fragment_type as root"""
        if isinstance(template_uuid, str):
            template_uuid = uuid.UUID(template_uuid)
        
        base_fragment = self.session.query(TemplateFragment).filter_by(
            template_uuid=template_uuid, fragment_type='base', is_active=True
        ).first()
        
        if not base_fragment:
            raise ValueError(f"No base fragment found for template {template_uuid}")
        
        template_data = self._prepare_data(data)
        env = self._get_jinja_environment(template_uuid)
        jinja_template = env.from_string(base_fragment.template_source)
        
        rendered_content = jinja_template.render(**template_data)
        return RenderResult(
            content=rendered_content,
            template_uuid=str(template_uuid),
            template_name=base_fragment.fragment_name or "base",
            fragments_rendered=[base_fragment.fragment_key],
            render_time_ms=0.0,
            cache_hit=False
        )

    def invalidate_cache(self, template_uuid: Union[str, uuid.UUID] = None,
                        page_uuid: Union[str, uuid.UUID] = None):
        """
        Invalidate cache entries for specific template/page or all cache
        
        Args:
            template_uuid: Optional template UUID to invalidate
            page_uuid: Optional page UUID to invalidate
        """
        if template_uuid is None and page_uuid is None:
            # Clear all cache
            self._content_cache.clear()
            self._template_cache.clear()
            self._env_cache.clear()
            self.logger.info("All caches cleared")
            return
        
        # Clear specific entries
        keys_to_remove = []
        
        for cache_key in self._content_cache.keys():
            key_parts = cache_key.split('_')
            if len(key_parts) >= 2:
                cache_template_uuid = key_parts[0]
                cache_page_uuid = key_parts[2] if len(key_parts) > 2 else None
                
                should_remove = False
                if template_uuid and str(template_uuid) == cache_template_uuid:
                    should_remove = True
                if page_uuid and cache_page_uuid and str(page_uuid) == cache_page_uuid:
                    should_remove = True
                
                if should_remove:
                    keys_to_remove.append(cache_key)
        
        for key in keys_to_remove:
            del self._content_cache[key]
        
        # Clear template-specific environment cache
        if template_uuid:
            env_key = f"env_{template_uuid}"
            if env_key in self._env_cache:
                del self._env_cache[env_key]
        
        self.logger.info(f"Invalidated {len(keys_to_remove)} cache entries")

    def clear_cache(self):
        """Clear all cached templates and content"""
        self._template_cache.clear()
        self._content_cache.clear()
        self._env_cache.clear()
        self.logger.info("All caches cleared")

    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics"""
        return {
            'template_cache_size': len(self._template_cache),
            'content_cache_size': len(self._content_cache),
            'environment_cache_size': len(self._env_cache)
        }

    def list_available_templates(self) -> List[Dict[str, Any]]:
        """List all available templates"""
        templates = self.session.query(Template).order_by(Template.name).all()
        
        result = []
        for template in templates:
            # Count active fragments
            fragment_count = self.session.query(TemplateFragment)\
                .filter_by(template_uuid=template.uuid, is_active=True)\
                .count()
            
            result.append({
                'uuid': str(template.uuid),
                'name': template.name,
                'display_name': template.display_name,
                'template_file': template.template_file,
                'active_fragments': fragment_count,
                'layout_type': template.layout_type,
                'is_admin_template': template.is_admin_template
            })
        
        return result

    def validate_template_data(self, template_uuid: Union[str, uuid.UUID], 
                              data: Dict[str, Any]) -> List[str]:
        """
        Validate template data against template requirements
        
        Args:
            template_uuid: Template UUID to validate against
            data: Data to validate
            
        Returns:
            List of validation error messages (empty if valid)
        """
        if isinstance(template_uuid, str):
            template_uuid = uuid.UUID(template_uuid)
        
        errors = []
        
        # Get template fragments with variable schemas
        fragments = TemplateFragment.get_all_active_for_template(
            self.session, template_uuid
        )
        
        for fragment in fragments:
            if fragment.variables_schema:
                # Validate against JSON schema if available
                try:
                    import jsonschema
                    jsonschema.validate(data, fragment.variables_schema)
                except ImportError:
                    self.logger.warning("jsonschema not available for validation")
                except Exception as e:
                    errors.append(f"Fragment {fragment.fragment_key}: {str(e)}")
        
        return errors