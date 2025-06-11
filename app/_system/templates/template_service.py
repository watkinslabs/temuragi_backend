import logging
import hashlib
import datetime
from typing import Optional, List, Dict, Any, Union
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models import Template
from app.models import Page
from app.models import TemplateFragment
from app.models import PageFragment
from app.models import Theme


class TemplateService:
    """
    Comprehensive service for CRUD operations on templates, pages, and fragments.
    Handles all template engine functionality including associations and versioning.
    """
    
    def __init__(self, session: Session, logger: Optional[logging.Logger] = None):
        self.session = session
        self.logger = logger or logging.getLogger(__name__)
    
    # =====================================================================
    # TEMPLATE OPERATIONS
    # =====================================================================
    
    def create_template(self, name: str, display_name: str, description: Optional[str] = None,
                       theme_uuid: Optional[UUID] = None, menu_type_uuid: Optional[UUID] = None,
                       layout_type: str = 'full-width', container_class: str = 'container-fluid',
                       sidebar_enabled: bool = False, header_type: str = 'static',
                       footer_type: str = 'static', breadcrumbs_enabled: bool = True,
                       module_uuid: Optional[UUID] = None, is_system: bool = False,
                       is_admin_template: bool = False, is_default_template: bool = False) -> Template:
        """Create a new template with validation"""
        self.logger.info(f"Creating template: {name}")
        
        template = Template(
            name=name,
            display_name=display_name,
            description=description,
            theme_uuid=theme_uuid,
            menu_type_uuid=menu_type_uuid,
            layout_type=layout_type,
            container_class=container_class,
            sidebar_enabled=sidebar_enabled,
            header_type=header_type,
            footer_type=footer_type,
            breadcrumbs_enabled=breadcrumbs_enabled,
            module_uuid=module_uuid,
            is_system=is_system,
            is_admin_template=is_admin_template,
            is_default_template=is_default_template
        )
        
        # Validate slug format
        template.validate_slug()
        
        self.session.add(template)
        
        try:
            if is_default_template:
                template.set_as_default(self.session)
            else:
                self.session.commit()
            
            self.logger.info(f"Template created: {name} ({template.uuid})")
            return template
            
        except IntegrityError as e:
            self.session.rollback()
            self.logger.error(f"Failed to create template {name}: {e}")
            raise ValueError(f"Template with name '{name}' already exists")
    
    def get_template(self, template_id: Union[str, UUID], by_name: bool = False,
                    module_uuid: Optional[UUID] = None) -> Optional[Template]:
        """Get template by UUID or name"""
        if by_name:
            return Template.get_by_name(self.session, template_id, module_uuid)
        
        return self.session.query(Template).filter_by(uuid=template_id).first()
    
    def update_template(self, template_uuid: UUID, **kwargs) -> Template:
        """Update template with provided fields"""
        template = self.get_template(template_uuid)
        if not template:
            raise ValueError(f"Template {template_uuid} not found")
        
        self.logger.info(f"Updating template: {template.name}")
        
        for key, value in kwargs.items():
            if hasattr(template, key):
                setattr(template, key, value)
        
        # Re-validate if name changed
        if 'name' in kwargs:
            template.validate_slug()
        
        # Handle default template change
        if kwargs.get('is_default_template'):
            template.set_as_default(self.session)
        else:
            self.session.commit()
        
        self.logger.info(f"Template updated: {template.name}")
        return template
    
    def delete_template(self, template_uuid: UUID, force: bool = False) -> bool:
        """Delete template if no dependencies exist or force is True"""
        template = self.get_template(template_uuid)
        if not template:
            raise ValueError(f"Template {template_uuid} not found")
        
        if template.is_system and not force:
            raise ValueError("Cannot delete system template without force=True")
        
        # Check for dependent pages
        page_count = template.get_pages_count(self.session)
        if page_count > 0 and not force:
            raise ValueError(f"Cannot delete template with {page_count} dependent pages")
        
        self.logger.info(f"Deleting template: {template.name}")
        
        try:
            # Cascade will handle fragments
            self.session.delete(template)
            self.session.commit()
            
            self.logger.info(f"Template deleted: {template.name}")
            return True
            
        except Exception as e:
            self.session.rollback()
            self.logger.error(f"Failed to delete template {template.name}: {e}")
            raise
    
    def list_templates(self, module_uuid: Optional[UUID] = None, layout_type: Optional[str] = None,
                      is_admin: Optional[bool] = None, include_system: bool = True) -> List[Template]:
        """List templates with optional filtering"""
        return Template.get_templates_by_type(
            self.session,
            layout_type=layout_type,
            is_admin=is_admin,
            module_uuid=module_uuid if include_system or module_uuid else module_uuid
        )
    
    def clone_template(self, template_uuid: UUID, new_name: str, 
                      new_display_name: Optional[str] = None) -> Template:
        """Clone a template with all its fragments"""
        template = self.get_template(template_uuid)
        if not template:
            raise ValueError(f"Template {template_uuid} not found")
        
        return template.clone_template(self.session, new_name, new_display_name)
    
    # =====================================================================
    # TEMPLATE FRAGMENT OPERATIONS
    # =====================================================================
    
    def create_template_fragment(self, template_uuid: UUID, fragment_type: str,
                               fragment_name: str, fragment_key: str,
                               template_file_path: str, template_source: str,
                               content_type: str = 'text/html',
                               compiled_file_path: Optional[str] = None,
                               version_label: Optional[str] = None,
                               is_active: bool = True, **kwargs) -> TemplateFragment:
        """Create a new template fragment"""
        self.logger.info(f"Creating template fragment: {fragment_key}")
        
        # Get next version number
        version_number = TemplateFragment.get_next_version_number(
            self.session, template_uuid, template_file_path
        )
        
        # Calculate content hash
        content_hash = hashlib.sha256(template_source.encode('utf-8')).hexdigest()
        
        fragment = TemplateFragment(
            template_uuid=template_uuid,
            fragment_type=fragment_type,
            fragment_name=fragment_name,
            fragment_key=fragment_key,
            template_file_path=template_file_path,
            compiled_file_path=compiled_file_path,
            content_type=content_type,
            version_number=version_number,
            version_label=version_label,
            is_active=is_active,
            template_source=template_source,
            template_hash=content_hash,
            **kwargs
        )
        
        self.session.add(fragment)
        
        try:
            if is_active:
                # Deactivate other versions first
                self.session.query(TemplateFragment)\
                           .filter_by(template_uuid=template_uuid,
                                     template_file_path=template_file_path)\
                           .update({'is_active': False})
                fragment.is_active = True
            
            self.session.commit()
            self.logger.info(f"Template fragment created: {fragment_key} v{version_number}")
            return fragment
            
        except Exception as e:
            self.session.rollback()
            self.logger.error(f"Failed to create template fragment {fragment_key}: {e}")
            raise
    
    def get_template_fragment(self, fragment_uuid: UUID) -> Optional[TemplateFragment]:
        """Get template fragment by UUID"""
        return self.session.query(TemplateFragment).filter_by(uuid=fragment_uuid).first()
    
    def get_template_fragment_by_key(self, template_uuid: UUID, 
                                   fragment_key: str) -> Optional[TemplateFragment]:
        """Get active template fragment by key"""
        return TemplateFragment.get_active_by_key(self.session, template_uuid, fragment_key)
    
    def update_template_fragment(self, fragment_uuid: UUID, **kwargs) -> TemplateFragment:
        """Update template fragment"""
        fragment = self.get_template_fragment(fragment_uuid)
        if not fragment:
            raise ValueError(f"Template fragment {fragment_uuid} not found")
        
        self.logger.info(f"Updating template fragment: {fragment.fragment_key}")
        
        # Handle content update specially
        if 'template_source' in kwargs:
            fragment.update_content_and_hash(kwargs['template_source'])
            del kwargs['template_source']
        
        for key, value in kwargs.items():
            if hasattr(fragment, key):
                setattr(fragment, key, value)
        
        self.session.commit()
        self.logger.info(f"Template fragment updated: {fragment.fragment_key}")
        return fragment
    
    def activate_template_fragment_version(self, fragment_uuid: UUID) -> TemplateFragment:
        """Activate a specific template fragment version"""
        return TemplateFragment.set_active_version(self.session, fragment_uuid)
    
    def list_template_fragments(self, template_uuid: UUID, 
                              fragment_type: Optional[str] = None,
                              active_only: bool = True) -> List[TemplateFragment]:
        """List template fragments with optional filtering"""
        if fragment_type:
            return TemplateFragment.get_fragments_by_type(
                self.session, template_uuid, fragment_type
            )
        
        if active_only:
            return TemplateFragment.get_all_active_for_template(self.session, template_uuid)
        
        return self.session.query(TemplateFragment)\
                          .filter_by(template_uuid=template_uuid)\
                          .order_by(TemplateFragment.fragment_type, TemplateFragment.sort_order)\
                          .all()
    
    def get_template_fragment_versions(self, template_uuid: UUID, 
                                     template_file_path: str) -> List[TemplateFragment]:
        """Get all versions of a template fragment file"""
        return TemplateFragment.get_file_version_history(
            self.session, template_uuid, template_file_path
        )
    
    # =====================================================================
    # PAGE OPERATIONS
    # =====================================================================
    
    def create_page(self, name: str, title: str, slug: str,
                   template_uuid: Optional[UUID] = None,
                   module_uuid: Optional[UUID] = None,
                   published: bool = False, **kwargs) -> Page:
        """Create a new page"""
        self.logger.info(f"Creating page: {slug}")
        
        page = Page(
            name=name,
            title=title,
            slug=slug,
            template_uuid=template_uuid,
            module_uuid=module_uuid,
            published=published,
            **kwargs
        )
        
        self.session.add(page)
        
        try:
            self.session.commit()
            self.logger.info(f"Page created: {slug} ({page.uuid})")
            return page
            
        except IntegrityError as e:
            self.session.rollback()
            self.logger.error(f"Failed to create page {slug}: {e}")
            raise ValueError(f"Page with slug '{slug}' already exists")
    
    def get_page(self, page_id: Union[str, UUID], by_slug: bool = False,
                include_unpublished: bool = False) -> Optional[Page]:
        """Get page by UUID or slug"""
        if by_slug:
            return Page.get_by_slug(self.session, page_id, include_unpublished)
        
        return self.session.query(Page).filter_by(uuid=page_id).first()
    
    def update_page(self, page_uuid: UUID, **kwargs) -> Page:
        """Update page with provided fields"""
        page = self.get_page(page_uuid)
        if not page:
            raise ValueError(f"Page {page_uuid} not found")
        
        self.logger.info(f"Updating page: {page.slug}")
        
        for key, value in kwargs.items():
            if hasattr(page, key):
                setattr(page, key, value)
        
        self.session.commit()
        self.logger.info(f"Page updated: {page.slug}")
        return page
    
    def publish_page(self, page_uuid: UUID, 
                    publish_date: Optional[datetime.datetime] = None) -> Page:
        """Publish a page"""
        page = self.get_page(page_uuid)
        if not page:
            raise ValueError(f"Page {page_uuid} not found")
        
        page.publish(self.session, publish_date)
        return page
    
    def unpublish_page(self, page_uuid: UUID) -> Page:
        """Unpublish a page"""
        page = self.get_page(page_uuid)
        if not page:
            raise ValueError(f"Page {page_uuid} not found")
        
        page.unpublish(self.session)
        return page
    
    def delete_page(self, page_uuid: UUID, force: bool = False) -> bool:
        """Delete page"""
        page = self.get_page(page_uuid)
        if not page:
            raise ValueError(f"Page {page_uuid} not found")
        
        self.logger.info(f"Deleting page: {page.slug}")
        
        try:
            # Cascade will handle fragments
            self.session.delete(page)
            self.session.commit()
            
            self.logger.info(f"Page deleted: {page.slug}")
            return True
            
        except Exception as e:
            self.session.rollback()
            self.logger.error(f"Failed to delete page {page.slug}: {e}")
            raise
    
    def list_pages(self, module_uuid: Optional[UUID] = None, published_only: bool = True,
                  featured_only: bool = False, limit: Optional[int] = None) -> List[Page]:
        """List pages with optional filtering"""
        return Page.get_published_pages(
            self.session,
            module_uuid=module_uuid,
            featured_only=featured_only,
            limit=limit
        ) if published_only else self.session.query(Page)\
                                              .filter_by(module_uuid=module_uuid)\
                                              .order_by(Page.sort_order, Page.created_at.desc())\
                                              .limit(limit).all() if limit else \
                                 self.session.query(Page)\
                                              .filter_by(module_uuid=module_uuid)\
                                              .order_by(Page.sort_order, Page.created_at.desc())\
                                              .all()
    
    def search_pages(self, search_term: str, published_only: bool = True) -> List[Page]:
        """Search pages by title, name, or slug"""
        return Page.search_pages(self.session, search_term, published_only)
    
    # =====================================================================
    # PAGE FRAGMENT OPERATIONS
    # =====================================================================
    
    def create_page_fragment(self, page_uuid: UUID, fragment_type: str,
                           fragment_name: str, fragment_key: str,
                           content_source: str, content_type: str = 'text/html',
                           version_label: Optional[str] = None,
                           is_active: bool = True, **kwargs) -> PageFragment:
        """Create a new page fragment"""
        self.logger.info(f"Creating page fragment: {fragment_key}")
        
        # Get next version number
        version_number = PageFragment.get_next_version_number(
            self.session, page_uuid, fragment_key
        )
        
        # Calculate content hash
        content_hash = hashlib.sha256(content_source.encode('utf-8')).hexdigest()
        
        fragment = PageFragment(
            page_uuid=page_uuid,
            fragment_type=fragment_type,
            fragment_name=fragment_name,
            fragment_key=fragment_key,
            content_type=content_type,
            version_number=version_number,
            version_label=version_label,
            is_active=is_active,
            content_source=content_source,
            content_hash=content_hash,
            **kwargs
        )
        
        self.session.add(fragment)
        
        try:
            if is_active:
                # Deactivate other versions first
                self.session.query(PageFragment)\
                           .filter_by(page_uuid=page_uuid, fragment_key=fragment_key)\
                           .update({'is_active': False})
                fragment.is_active = True
            
            self.session.commit()
            self.logger.info(f"Page fragment created: {fragment_key} v{version_number}")
            return fragment
            
        except Exception as e:
            self.session.rollback()
            self.logger.error(f"Failed to create page fragment {fragment_key}: {e}")
            raise
    
    def get_page_fragment(self, fragment_uuid: UUID) -> Optional[PageFragment]:
        """Get page fragment by UUID"""
        return self.session.query(PageFragment).filter_by(uuid=fragment_uuid).first()
    
    def get_page_fragment_by_key(self, page_uuid: UUID, 
                               fragment_key: str) -> Optional[PageFragment]:
        """Get active page fragment by key"""
        return PageFragment.get_active_by_key(self.session, page_uuid, fragment_key)
    
    def update_page_fragment(self, fragment_uuid: UUID, **kwargs) -> PageFragment:
        """Update page fragment"""
        fragment = self.get_page_fragment(fragment_uuid)
        if not fragment:
            raise ValueError(f"Page fragment {fragment_uuid} not found")
        
        self.logger.info(f"Updating page fragment: {fragment.fragment_key}")
        
        # Handle content update specially
        if 'content_source' in kwargs:
            fragment.update_content_and_hash(kwargs['content_source'])
            del kwargs['content_source']
        
        for key, value in kwargs.items():
            if hasattr(fragment, key):
                setattr(fragment, key, value)
        
        self.session.commit()
        self.logger.info(f"Page fragment updated: {fragment.fragment_key}")
        return fragment
    
    def activate_page_fragment_version(self, fragment_uuid: UUID) -> PageFragment:
        """Activate a specific page fragment version"""
        return PageFragment.set_active_version(self.session, fragment_uuid)
    
    def list_page_fragments(self, page_uuid: UUID, fragment_type: Optional[str] = None,
                          include_hidden: bool = False) -> List[PageFragment]:
        """List page fragments with optional filtering"""
        if fragment_type:
            return PageFragment.get_fragments_by_type(
                self.session, page_uuid, fragment_type, include_hidden
            )
        
        return PageFragment.get_all_active_for_page(self.session, page_uuid, include_hidden)
    
    def get_page_fragment_versions(self, page_uuid: UUID, 
                                 fragment_key: str) -> List[PageFragment]:
        """Get all versions of a page fragment"""
        return PageFragment.get_fragment_version_history(
            self.session, page_uuid, fragment_key
        )
    
    # =====================================================================
    # THEME OPERATIONS
    # =====================================================================
    
    def get_theme(self, theme_uuid: UUID) -> Optional[Theme]:
        """Get theme by UUID"""
        return self.session.query(Theme).filter_by(uuid=theme_uuid).first()
    
    def list_themes(self) -> List[Theme]:
        """List all themes"""
        return self.session.query(Theme).order_by(Theme.name).all()
    
    # =====================================================================
    # ASSOCIATIONS AND RELATIONSHIPS
    # =====================================================================
    
    def assign_template_to_page(self, page_uuid: UUID, template_uuid: UUID) -> Page:
        """Assign a template to a page"""
        page = self.get_page(page_uuid)
        template = self.get_template(template_uuid)
        
        if not page:
            raise ValueError(f"Page {page_uuid} not found")
        if not template:
            raise ValueError(f"Template {template_uuid} not found")
        
        page.template_uuid = template_uuid
        page.validate_template_exists(self.session)
        
        self.session.commit()
        self.logger.info(f"Template {template.name} assigned to page {page.slug}")
        return page
    
    def get_pages_by_template(self, template_uuid: UUID, 
                            published_only: bool = True) -> List[Page]:
        """Get all pages using a specific template"""
        return Page.get_pages_by_template(self.session, template_uuid, published_only)
    
    def get_template_structure(self, template_uuid: UUID) -> Dict[str, Any]:
        """Get complete template structure including fragments"""
        template = self.get_template(template_uuid)
        if not template:
            raise ValueError(f"Template {template_uuid} not found")
        
        fragments = TemplateFragment.get_template_structure(self.session, template_uuid)
        
        return {
            'template': template,
            'fragments': fragments,
            'fragment_count': len(fragments),
            'integrity_check': template.validate_template_integrity(self.session)
        }
    
    def get_page_structure(self, page_uuid: UUID, 
                         include_hidden: bool = False) -> Dict[str, Any]:
        """Get complete page structure including fragments"""
        page = self.get_page(page_uuid)
        if not page:
            raise ValueError(f"Page {page_uuid} not found")
        
        fragments = PageFragment.get_page_fragment_structure(
            self.session, page_uuid, include_hidden
        )
        
        return {
            'page': page,
            'fragments': fragments,
            'fragment_count': len(fragments),
            'template': self.get_template(page.template_uuid) if page.template_uuid else None
        }
    
    # =====================================================================
    # UTILITY METHODS
    # =====================================================================
    
    def validate_template_integrity(self, template_uuid: UUID) -> Dict[str, Any]:
        """Comprehensive template integrity validation"""
        template = self.get_template(template_uuid)
        if not template:
            raise ValueError(f"Template {template_uuid} not found")
        
        issues = []
        
        # Basic template validation
        is_valid = template.validate_template_integrity(self.session)
        
        # Check for circular dependencies
        has_cycles = not TemplateFragment.find_circular_dependencies(self.session, template_uuid)
        if has_cycles:
            issues.append("Circular dependencies detected")
        
        # Fragment compilation check
        fragments = self.list_template_fragments(template_uuid)
        needs_compilation = [f for f in fragments if f.needs_compilation()]
        
        return {
            'template_uuid': template_uuid,
            'is_valid': is_valid and not has_cycles,
            'has_circular_dependencies': has_cycles,
            'fragments_needing_compilation': len(needs_compilation),
            'compilation_details': [f.get_compilation_info() for f in needs_compilation],
            'issues': issues
        }
    
    def get_dashboard_stats(self, module_uuid: Optional[UUID] = None) -> Dict[str, Any]:
        """Get dashboard statistics for the template engine"""
        base_query_args = {'module_uuid': module_uuid} if module_uuid else {}
        
        # Template stats
        total_templates = self.session.query(Template).filter_by(**base_query_args).count()
        admin_templates = self.session.query(Template).filter_by(
            is_admin_template=True, **base_query_args
        ).count()
        
        # Page stats
        total_pages = self.session.query(Page).filter_by(**base_query_args).count()
        published_pages = self.session.query(Page).filter_by(
            published=True, **base_query_args
        ).count()
        
        # Fragment stats
        if module_uuid:
            template_uuids = [t.uuid for t in self.session.query(Template.uuid).filter_by(module_uuid=module_uuid)]
            page_uuids = [p.uuid for p in self.session.query(Page.uuid).filter_by(module_uuid=module_uuid)]
            
            template_fragments = self.session.query(TemplateFragment).filter(
                TemplateFragment.template_uuid.in_(template_uuids)
            ).count() if template_uuids else 0
            
            page_fragments = self.session.query(PageFragment).filter(
                PageFragment.page_uuid.in_(page_uuids)
            ).count() if page_uuids else 0
        else:
            template_fragments = self.session.query(TemplateFragment).count()
            page_fragments = self.session.query(PageFragment).count()
        
        return {
            'templates': {
                'total': total_templates,
                'admin_only': admin_templates,
                'public': total_templates - admin_templates
            },
            'pages': {
                'total': total_pages,
                'published': published_pages,
                'unpublished': total_pages - published_pages
            },
            'fragments': {
                'template_fragments': template_fragments,
                'page_fragments': page_fragments,
                'total_fragments': template_fragments + page_fragments
            }
        }