#!/usr/bin/env python3
"""
Render CLI - Render templates using TemplateLoader
"""

import sys
import argparse
import json
import uuid
from jinja2 import Environment

# Add app path
sys.path.append('/web/temuragi')
from app.base.cli import BaseCLI



CLI_DESCRIPTION = "Simple template rendering"

class RenderCLI(BaseCLI):
    def __init__(self, verbose=False, show_icons=True, table_format=None):
        """Initialize CLI with database connection"""
        super().__init__(
            name="render",
            log_file="logs/render_cli.log",
            connect_db=True,
            verbose=verbose,
            show_icons=show_icons,
            table_format=table_format
        )

        self.log_info("Starting render CLI initialization")

        try:
            self.template_model = self.get_model('Template')
            self.template_fragment_model = self.get_model('TemplateFragment')
            self.page_model = self.get_model('Page')
            self.page_fragment_model = self.get_model('PageFragment')            

            if not all([self.template_model, self.template_fragment_model, 
                    self.page_model, self.page_fragment_model]):
                self.log_error("Required models not found in registry")
                raise Exception("Required models not found in registry")
                        
            self.log_info("Render CLI initialized successfully")

        except Exception as e:
            self.log_error(f"Failed to initialize render CLI: {e}")
            raise


    def list_templates(self):
        """List all templates"""
        self.log_info("Listing templates")

        try:
            templates = self.session.query(self.template_model).order_by(self.template_model.name).all()

            if not templates:
                self.output_warning("No templates found")
                return 0

            headers = ["Name", "Display Name", "UUID"]
            rows = []

            for template in templates:
                rows.append([
                    template.name,
                    template.display_name or '',
                    str(template.uuid)
                ])

            self.output_info("Available Templates:")
            self.output_table(rows, headers=headers)
            return 0

        except Exception as e:
            self.log_error(f"Error listing templates: {e}")
            self.output_error(f"Error listing templates: {e}")
            return 1

    def show_template_fragments(self, template_name):
        """Show fragments for a template"""
        self.log_info(f"Showing fragments for template: {template_name}")

        try:
            template = self.session.query(self.template_model).filter_by(name=template_name).first()
            if not template:
                self.output_error(f"Template '{template_name}' not found")
                return 1

            # Get all fragments for this template
            fragments = self.session.query(self.template_fragment_model).filter_by(
                template_uuid=template.uuid,
                is_active=True
            ).order_by(self.template_fragment_model.fragment_type, self.template_fragment_model.sort_order).all()
            
            self.output_info(f"Template: {template.name} ({template.uuid})")
            
            if not fragments:
                self.output_warning("No active fragments found")
                return 0
            
            self.output_info(f"Active Fragments ({len(fragments)}):")
            
            for fragment in fragments:
                source_length = len(fragment.template_source) if fragment.template_source else 0
                is_base = " (BASE)" if fragment.fragment_type == 'base' else ""
                self.output_info(f"  {fragment.fragment_key}: {fragment.fragment_type}{is_base} - {source_length} chars")
                
                # Show first few lines of template source for debugging
                if fragment.template_source:
                    lines = fragment.template_source.split('\n')[:3]
                    preview = ' | '.join(line.strip() for line in lines if line.strip())
                    if len(preview) > 100:
                        preview = preview[:100] + "..."
                    self.output_info(f"    Preview: {preview}")

            return 0

        except Exception as e:
            self.log_error(f"Error showing template fragments: {e}")
            self.output_error(f"Error showing template fragments: {e}")
            return 1

    def render_template(self, template_name, data_json=None):
        """Render a template with optional JSON data"""
        self.log_info(f"Rendering template: {template_name}")

        try:
            # Find template
            template = self.session.query(self.template_model).filter_by(name=template_name).first()
            if not template:
                self.output_error(f"Template '{template_name}' not found")
                return 1

            # Parse data if provided
            data = {}
            if data_json:
                try:
                    data = json.loads(data_json)
                    self.output_info(f"Loaded data: {len(data)} keys")
                except json.JSONDecodeError as e:
                    self.output_error(f"Invalid JSON data: {e}")
                    return 1

            # Create loader and environment
            loader = TemplateLoader(self.session, template.uuid)
            env = Environment(
                loader=loader,
                autoescape=True,
                trim_blocks=True,
                lstrip_blocks=True,
                undefined=self._create_safe_undefined()
            )

            # Register basic template functions
            self._register_template_functions(env, template.uuid)

            # Get base fragment key and render
            base_fragment_key = loader.get_base_fragment_key()
            self.output_info(f"Rendering base fragment: {base_fragment_key}")
            
            jinja_template = env.get_template(base_fragment_key)
            rendered_content = jinja_template.render(**data)

            # Output result
            self.output_info("Rendered content:")
            print("=" * 60)
            print(rendered_content)
            print("=" * 60)

            self.output_success(f"Template '{template_name}' rendered successfully")
            self.output_info(f"Content length: {len(rendered_content)} characters")

            return 0

        except Exception as e:
            self.log_error(f"Error rendering template: {e}")
            self.output_error(f"Error rendering template: {e}")
            return 1

    def _register_template_functions(self, env, template_uuid):
        """Register basic template functions"""
        
        def render_fragment(fragment_key):
            """Render a template fragment by key"""
            self.log_debug("render_fragment called for '{fragment_key}'")
            try:
                fragment = self.session.query(self.template_fragment_model).filter_by(
                    template_uuid=template_uuid,
                    fragment_key=fragment_key,
                    is_active=True
                ).first()
                
                if not fragment:
                    self.log_debug("Fragment '{fragment_key}' not found in database")
                    return f"<!-- Fragment '{fragment_key}' not found -->"
                
                if not fragment.template_source:
                    self.log_debug("Fragment '{fragment_key}' has no source")
                    return f"<!-- Fragment '{fragment_key}' has no source -->"
                
                self.log_debug("Found fragment '{fragment_key}' with {len(fragment.template_source)} chars")
                
                # Render the fragment source directly
                fragment_template = env.from_string(fragment.template_source)
                result = fragment_template.render()
                self.log_debug("Rendered fragment '{fragment_key}' to {len(result)} chars")
                return result
                
            except Exception as e:
                self.log_debug("Error rendering fragment {fragment_key}: {e}")
                self.log_error(f"Error rendering fragment {fragment_key}: {e}")
                return f"<!-- Error rendering fragment '{fragment_key}': {e} -->"

        def include_fragment(fragment_key, **kwargs):
            """Include and render a template fragment with data"""
            self.log_debug("include_fragment called for '{fragment_key}' with data: {kwargs}")
            try:
                fragment = self.session.query(self.template_fragment_model).filter_by(
                    template_uuid=template_uuid,
                    fragment_key=fragment_key,
                    is_active=True
                ).first()
                
                if not fragment or not fragment.template_source:
                    return f"<!-- Fragment '{fragment_key}' not found -->"
                
                # Render with provided data
                fragment_template = env.from_string(fragment.template_source)
                return fragment_template.render(**kwargs)
                
            except Exception as e:
                self.log_error(f"Error including fragment {fragment_key}: {e}")
                return f"<!-- Error including fragment '{fragment_key}' -->"

        # Register the functions
        env.globals['render_fragment'] = render_fragment
        env.globals['include_fragment'] = include_fragment

    def _create_safe_undefined(self):
        """Create a custom undefined handler that returns safe fallback content"""
        from jinja2 import Undefined
        
        class SafeUndefined(Undefined):
            def __str__(self):
                return f"<!-- FAILED TO LOAD {self._undefined_name} -->"
            
            def __call__(self, *args, **kwargs):
                return f"<!-- FAILED TO LOAD {self._undefined_name}({args}, {kwargs}) -->"
            
            def __getattr__(self, name):
                return SafeUndefined(name=f"{self._undefined_name}.{name}")
        
        return SafeUndefined

    def test_loader(self, template_name):
        """Test the loader for a template"""
        self.log_info(f"Testing loader for template: {template_name}")

        try:
            template = self.session.query(self.template_model).filter_by(name=template_name).first()
            if not template:
                self.output_error(f"Template '{template_name}' not found")
                return 1

            # Create loader
            loader = TemplateLoader(self.session, template.uuid)
            
            self.output_info(f"Loader created for template: {template.name}")
            self.output_info(f"Template UUID: {template.uuid}")
            self.output_info(f"Base fragment key: {loader.base_fragment_key}")
            self.output_info(f"Total fragments loaded: {len(loader.fragments)}")
            
            self.output_info("Fragment details:")
            for fragment_key, fragment in loader.fragments.items():
                source_length = len(fragment.template_source) if fragment.template_source else 0
                is_base = " (BASE)" if fragment.fragment_type == 'base' else ""
                self.output_info(f"  {fragment_key}: {fragment.fragment_type}{is_base} - {source_length} chars")

            return 0

        except Exception as e:
            self.log_error(f"Error testing loader: {e}")
            self.output_error(f"Error testing loader: {e}")
            return 1


    def list_pages(self):
        """List all pages"""
        self.log_info("Listing pages")

        try:
            pages = self.session.query(self.page_model).order_by(self.page_model.slug).all()

            if not pages:
                self.output_warning("No pages found")
                return 0

            headers = ["Slug", "Title", "Template", "Published", "UUID"]
            rows = []

            for page in pages:
                template_name = ""
                if page.template_uuid:
                    template = self.session.query(self.template_model).filter_by(uuid=page.template_uuid).first()
                    template_name = template.name if template else "MISSING"

                rows.append([
                    page.slug,
                    page.title[:30] + "..." if len(page.title) > 30 else page.title,
                    template_name,
                    "Yes" if page.published else "No",
                    str(page.uuid)
                ])

            self.output_info("Available Pages:")
            self.output_table(rows, headers=headers)
            return 0

        except Exception as e:
            self.log_error(f"Error listing pages: {e}")
            self.output_error(f"Error listing pages: {e}")
            return 1

    def show_page_fragments(self, page_slug):
        """Show fragments for a page"""
        self.log_info(f"Showing fragments for page: {page_slug}")

        try:
            page = self.session.query(self.page_model).filter_by(slug=page_slug).first()
            if not page:
                self.output_error(f"Page '{page_slug}' not found")
                return 1

            # Get all fragments for this page
            fragments = self.session.query(self.page_fragment_model).filter_by(
                page_uuid=page.uuid,
                is_active=True
            ).order_by(self.page_fragment_model.fragment_type, self.page_fragment_model.sort_order).all()

            self.output_info(f"Page: {page.slug} - {page.title}")
            self.output_info(f"UUID: {page.uuid}")

            if not fragments:
                self.output_warning("No active fragments found")
                return 0

            self.output_info(f"Active Page Fragments ({len(fragments)}):")

            for fragment in fragments:
                source_length = len(fragment.content_source) if fragment.content_source else 0
                published_status = " (PUBLISHED)" if fragment.is_published else " (UNPUBLISHED)"
                self.output_info(f"  {fragment.fragment_key}: {fragment.fragment_type}{published_status} - {source_length} chars")

                # Show first few lines of content for debugging
                if fragment.content_source:
                    lines = fragment.content_source.split('\n')[:3]
                    preview = ' | '.join(line.strip() for line in lines if line.strip())
                    if len(preview) > 100:
                        preview = preview[:100] + "..."
                    self.output_info(f"    Preview: {preview}")

            return 0

        except Exception as e:
            self.log_error(f"Error showing page fragments: {e}")
            self.output_error(f"Error showing page fragments: {e}")
            return 1

    def render_page(self, page_slug, data_json=None):
        """Render a page by slug"""
        self.log_info(f"Rendering page: {page_slug}")

        try:
            # Find page by slug
            page = self.session.query(self.page_model).filter_by(slug=page_slug).first()
            if not page:
                self.output_error(f"Page '{page_slug}' not found")
                return 1

            if not page.template_uuid:
                self.output_error(f"Page '{page_slug}' has no template assigned")
                return 1

            # Get template info
            template = self.session.query(self.template_model).filter_by(uuid=page.template_uuid).first()
            template_name = template.name if template else "UNKNOWN"

            self.output_info(f"Page: {page.title}")
            self.output_info(f"Slug: {page.slug}")
            self.output_info(f"Template: {template_name}")
            self.output_info(f"Published: {'Yes' if page.published else 'No'}")

            # Parse data if provided
            data = {}
            if data_json:
                try:
                    data = json.loads(data_json)
                    self.output_info(f"Loaded additional data: {len(data)} keys")
                except json.JSONDecodeError as e:
                    self.output_error(f"Invalid JSON data: {e}")
                    return 1

            # Create renderer and render page
            from app.classes import TemplateRenderer  # Import here to avoid circular imports
            renderer = TemplateRenderer(self.session, self.logger)
            rendered_content = renderer.render_page(page.uuid, data)

            # Output result
            self.output_info("Rendered page content:")
            print("=" * 60)
            print(rendered_content)
            print("=" * 60)

            self.output_success(f"Page '{page_slug}' rendered successfully")
            self.output_info(f"Content length: {len(rendered_content)} characters")

            return 0

        except Exception as e:
            self.log_error(f"Error rendering page: {e}")
            self.output_error(f"Error rendering page: {e}")
            return 1
                
    def close(self):
        """Clean up resources"""
        self.log_debug("Closing render CLI")
        super().close()


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Simple template rendering",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    parser.add_argument('--no-icons', action='store_true', help='Disable icons in output')
    parser.add_argument('--table-format', choices=['simple', 'grid', 'pipe', 'orgtbl', 'rst'],
                       help='Override table format')

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # List templates
    subparsers.add_parser('list', help='List all templates')

    # Show template
    show_parser = subparsers.add_parser('show', help='Show template fragments')
    show_parser.add_argument('template_name', help='Template name to show')

    # Render template
    render_parser = subparsers.add_parser('render', help='Render a template')
    render_parser.add_argument('template_name', help='Template name to render')
    render_parser.add_argument('--data', help='JSON data string (e.g. \'{"key": "value"}\')')


    # List pages
    subparsers.add_parser('list-pages', help='List all pages')

    # Show page
    show_page_parser = subparsers.add_parser('show-page', help='Show page fragments')
    show_page_parser.add_argument('page_slug', help='Page slug to show')

    # Render page
    render_page_parser = subparsers.add_parser('render-page', help='Render a page')
    render_page_parser.add_argument('page_slug', help='Page slug to render')
    render_page_parser.add_argument('--data', help='JSON data string (e.g. \'{"key": "value"}\')')


    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Initialize CLI
    cli = None
    try:
        cli = RenderCLI(
            verbose=args.verbose,
            show_icons=not args.no_icons,
            table_format=args.table_format
        )
    except Exception as e:
        print(f"Error initializing CLI: {e}")
        return 1

    # Execute commands
    try:
        if args.command == 'list':
            return cli.list_templates()
        
        elif args.command == 'show':
            return cli.show_template_fragments(args.template_name)
        
        elif args.command == 'render':
            return cli.render_template(
                args.template_name,
                data_json=getattr(args, 'data', None)
            )
        elif args.command == 'list-pages':
            return cli.list_pages()

        elif args.command == 'show-page':
            return cli.show_page_fragments(args.page_slug)

        elif args.command == 'render-page':
            return cli.render_page(
                args.page_slug,
                data_json=getattr(args, 'data', None)
            )
        else:
            parser.print_help()
            return 1

    except KeyboardInterrupt:
        if cli:
            cli.log_info("Operation cancelled by user")
        print("\nOperation cancelled")
        return 1
    except Exception as e:
        if cli:
            cli.log_error(f"Unexpected error: {e}")
        print(f"Error: {e}")
        return 1
    finally:
        if cli:
            cli.close()

    return 0


if __name__ == '__main__':
    sys.exit(main())