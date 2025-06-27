"""
Model Page Creator - Creates pages and fragments for model forms
"""

import hashlib
from datetime import datetime
from app.register.classes import get_model


class ModelPageCreator:
    """Creates and manages pages/fragments for model forms"""
    
    def __init__(self, session, logger=None):
        self.session = session
        self.logger = logger
        
        # Load required models
        self.Page = get_model('Page')
        self.PageFragment = get_model('PageFragment')
        self.Template = get_model('Template')
        
        if not all([self.Page, self.PageFragment, self.Template]):
            raise RuntimeError("Required models (Page, PageFragment, Template) not found")
    
    def create_management_page(self, model_name, form_html, options=None):
        """
        Create or update a management page for a model
        
        Args:
            model_name: Name of the model
            form_html: Generated form HTML
            options: Dict with optional settings:
                - slug_pattern: Pattern for slug (default: "{model}/manage")
                - template_id: Specific template ID to use
                - requires_auth: Whether page requires auth (default: True)
                - published: Whether to publish immediately (default: True)
                - fragment_key: Key for the fragment (default: "main_content")
                - meta_description: SEO description
                - cache_duration: Cache time in seconds (default: 0)
        
        Returns:
            Tuple of (success: bool, page: Page, fragment: PageFragment, message: str)
        """
        options = options or {}
        
        # Generate page properties
        slug = self._generate_slug(model_name, options.get('slug_pattern'))
        name = f"{model_name} Management"
        title = f"Manage {model_name}"
        
        try:
            # Check if page exists
            existing_page = self.session.query(self.Page).filter_by(slug=slug).first()
            
            if existing_page:
                # Update existing page
                return self._update_existing_page(existing_page, form_html, options)
            else:
                # Create new page
                return self._create_new_page(
                    model_name, slug, name, title, form_html, options
                )
                
        except Exception as e:
            self.session.rollback()
            error_msg = f"Failed to create/update page: {str(e)}"
            if self.logger:
                self.logger.error(error_msg)
            return False, None, None, error_msg
    
    def _generate_slug(self, model_name, pattern=None):
        """Generate slug for the page"""
        if pattern:
            return pattern.format(model=model_name.lower())
        return f"f/{model_name.lower()}/manage"
    
    def _get_template(self, template_id=None):
        """Get template by ID or find default"""
        if template_id:
            template = self.session.query(self.Template).filter_by(id=template_id).first()
            if template:
                return template
                
        # Try default template
        template = self.session.query(self.Template).filter_by(id='00000000-0000-0000-0000-000000000002').first()
        if template:
            return template
            
        # Fallback to any template
        template = self.session.query(self.Template).first()
        if not template:
            raise ValueError("No templates found in database")
            
        return template
    
    def _create_new_page(self, model_name, slug, name, title, form_html, options):
        """Create a new page with fragment"""
        # Get template
        template = self._get_template(options.get('template_id'))
        
        if self.logger:
            self.logger.info(f"Creating new page '{slug}' with template '{template.name}'")
        
        # Create page
        page = self.Page(
            name=name,
            title=title,
            slug=slug,
            template_id=template.id,
            meta_description=options.get('meta_description', f"Manage {model_name} records"),
            published=options.get('published', True),
            requires_auth=options.get('requires_auth', True),
            cache_duration=options.get('cache_duration', 0),
            sort_order=options.get('sort_order', 999)
        )
        
        # Add SEO data if provided
        if options.get('meta_keywords'):
            page.meta_keywords = options['meta_keywords']
        if options.get('og_title'):
            page.og_title = options['og_title']
        if options.get('og_description'):
            page.og_description = options['og_description']
            
        self.session.add(page)
        self.session.flush()  # Get page ID
        
        # Create fragment
        fragment = self._create_fragment(
            page.id,
            form_html,
            options.get('fragment_key', 'main_content'),
            f"Auto-generated form for {model_name} management",
            version_number=1,
            is_active=True
        )
        
        self.session.add(fragment)
        self.session.commit()
        
        success_msg = f"Created page '{slug}' with form fragment"
        if self.logger:
            self.logger.info(success_msg)
            
        return True, page, fragment, success_msg
    
    def _update_existing_page(self, page, form_html, options):
        """Update existing page with new fragment version"""
        fragment_key = options.get('fragment_key', 'main_content')

        if self.logger:
            self.logger.info(f"Updating existing page '{page.slug}'")

        # Get current active fragment
        current_fragment = self.session.query(self.PageFragment).filter_by(
            page_id=page.id,
            fragment_key=fragment_key,
            is_active=True
        ).first()

        # Check if content actually changed
        new_hash = hashlib.sha256(form_html.encode('utf-8')).hexdigest()
        if current_fragment and current_fragment.content_hash == new_hash:
            msg = f"Page '{page.slug}' fragment unchanged, skipping update"
            if self.logger:
                self.logger.info(msg)
            return True, page, current_fragment, msg

        if current_fragment:
            # Update existing fragment instead of creating new version
            # This avoids any unique constraint issues
            current_fragment.content_source = form_html
            current_fragment.content_hash = new_hash
            current_fragment.change_description = "Auto-updated from model metadata"
            current_fragment.updated_at = datetime.utcnow()
            
            self.session.commit()
            
            success_msg = f"Updated page '{page.slug}' fragment"
            if self.logger:
                self.logger.info(success_msg)
                
            return True, page, current_fragment, success_msg
        else:
            # No existing fragment, create new one
            fragment = self._create_fragment(
                page.id,
                form_html,
                fragment_key,
                f"Auto-generated form for {page.name}",
                version_number=1,
                version_label="1",
                is_active=True,
                change_description="Initial auto-generated form"
            )
            
            self.session.add(fragment)
            self.session.commit()
            
            success_msg = f"Created fragment for existing page '{page.slug}'"
            if self.logger:
                self.logger.info(success_msg)
                
            return True, page, fragment, success_msg

    def _create_fragment(self, page_id, content, fragment_key, description,
                        version_number=1, version_label=None, is_active=True,
                        change_description=None):
        """Create a page fragment"""
        fragment = self.PageFragment(
            page_id=page_id,
            fragment_type='content',
            fragment_name='Main Form',
            fragment_key=fragment_key,
            content_type='text/html',
            version_number=version_number,
            version_label=version_label,
            is_active=is_active,
            content_source=content,
            content_hash=hashlib.sha256(content.encode('utf-8')).hexdigest(),
            description=description,
            change_description=change_description,
            is_published=True,
            sort_order=0,
            cache_duration=0  # Don't cache forms
        )
        
        return fragment
    
    def create_bulk_pages(self, model_forms, options=None):
        """
        Create multiple model pages at once
        
        Args:
            model_forms: List of tuples (model_name, form_html)
            options: Default options for all pages
            
        Returns:
            Dict with results for each model
        """
        results = {}
        
        for model_name, form_html in model_forms:
            success, page, fragment, message = self.create_management_page(
                model_name, form_html, options
            )
            results[model_name] = {
                'success': success,
                'page': page,
                'fragment': fragment,
                'message': message
            }
            
        return results
    
    def get_management_page(self, model_name, slug_pattern=None):
        """Get the management page for a model"""
        slug = self._generate_slug(model_name, slug_pattern)
        return self.session.query(self.Page).filter_by(slug=slug).first()
    
    def list_management_pages(self):
        """List all management pages (pages with /manage in slug)"""
        pages = self.session.query(self.Page).filter(
            self.Page.slug.like('%/manage')
        ).order_by(self.Page.name).all()
        
        return pages