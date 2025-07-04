#!/usr/bin/env python3
"""
Render CLI - Render templates using the new renderer
"""

import sys
import argparse
import json
import uuid
from jinja2 import Environment

sys.path.append('/web/ahoy2.radiatorusa.com')
from app.base.cli_v1 import BaseCLI


CLI_DESCRIPTION = "Template and page rendering"

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
                    str(template.id)
                ])

            self.output_info("Available Templates:")
            self.output_table(rows, headers=headers)
            return 0

        except Exception as e:
            self.log_error(f"Error listing templates: {e}")
            self.output_error(f"Error listing templates: {e}")
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
                if page.template_id:
                    template = self.session.query(self.template_model).filter_by(id=page.template_id).first()
                    template_name = template.name if template else "MISSING"

                rows.append([
                    page.slug,
                    page.title[:30] + "..." if len(page.title) > 30 else page.title,
                    template_name,
                    "Yes" if page.published else "No",
                    str(page.id)
                ])

            self.output_info("Available Pages:")
            self.output_table(rows, headers=headers)
            return 0

        except Exception as e:
            self.log_error(f"Error listing pages: {e}")
            self.output_error(f"Error listing pages: {e}")
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

            if not page.template_id:
                self.output_error(f"Page '{page_slug}' has no template assigned")
                return 1

            # Get template info
            template = self.session.query(self.template_model).filter_by(id=page.template_id).first()
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
            
            from app.classes import TemplateRenderer
            # Create renderer and render page
            renderer = TemplateRenderer()
            rendered_content = renderer.render_template(page.id, **data)

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
    subparsers.add_parser('list-templates', help='List all templates')

    # List pages
    subparsers.add_parser('list-pages', help='List all pages')

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
        if args.command == 'list-templates':
            return cli.list_templates()
        elif args.command == 'list-pages':
            return cli.list_pages()
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
