#!/usr/bin/env python3
"""
Template Render CLI - Manage and render templates
"""

import sys
import argparse
import yaml
import json
import uuid
from pathlib import Path

# Add app path
sys.path.append('/web/temuragi')
from app.base_cli import BaseCLI
from .template_renderer import TemplateRenderer

CLI_DESCRIPTION = "Manage and render templates"

class TemplateRenderCLI(BaseCLI):
    def __init__(self, verbose=False, show_icons=True, table_format=None):
        """Initialize CLI with database connection and renderer"""
        super().__init__(
            name="template_render",
            log_file="logs/template_render_cli.log",
            connect_db=True,
            verbose=verbose,
            show_icons=show_icons,
            table_format=table_format
        )

        self.log_info("Starting template render CLI initialization")

        try:
            self.template_model = self.get_model('Template')
            self.template_fragment_model = self.get_model('TemplateFragment')
            
            if not all([self.template_model, self.template_fragment_model]):
                self.log_error("Required models not found in registry")
                raise Exception("Required models not found in registry")
            
            # Initialize renderer
            self.renderer = TemplateRenderer(
                session=self.session,
                cache_enabled=True,
                logger=self.logger
            )
            
            self.log_info("Template renderer initialized successfully")

        except Exception as e:
            self.log_error(f"Failed to initialize template render CLI: {e}")
            raise

    def list_templates(self, module_name=None):
        """List all templates"""
        self.log_info("Listing templates")

        try:
            query = self.session.query(self.template_model)
            
            if module_name:
                module_model = self.get_model('Module')
                if module_model:
                    module = self.session.query(module_model).filter_by(name=module_name).first()
                    if module:
                        query = query.filter_by(module_uuid=module.uuid)
                    else:
                        self.output_error(f"Module '{module_name}' not found")
                        return 1
            
            templates = query.order_by(self.template_model.name).all()

            if not templates:
                self.output_warning("No templates found")
                return 0

            headers = ["Name", "Display Name", "Layout", "Module", "System", "UUID"]
            rows = []

            for template in templates:
                module_name = ""
                if hasattr(template, 'module') and template.module:
                    module_name = template.module.name

                rows.append([
                    template.name,
                    template.display_name or '',
                    template.layout_type or '',
                    module_name,
                    "Yes" if template.is_system else "No",
                    str(template.uuid)
                ])

            self.output_info("Available Templates:")
            self.output_table(rows, headers=headers)
            return 0

        except Exception as e:
            self.log_error(f"Error listing templates: {e}")
            self.output_error(f"Error listing templates: {e}")
            return 1

    def list_fragments(self, template_name=None):
        """List template fragments"""
        self.log_info(f"Listing template fragments for template: {template_name or 'all'}")

        try:
            query = self.session.query(self.template_fragment_model)
            
            if template_name:
                template = self.session.query(self.template_model).filter_by(name=template_name).first()
                if not template:
                    self.output_error(f"Template '{template_name}' not found")
                    return 1
                query = query.filter_by(template_uuid=template.uuid)
            
            fragments = query.order_by(
                self.template_fragment_model.template_uuid,
                self.template_fragment_model.fragment_type,
                self.template_fragment_model.sort_order
            ).all()

            if not fragments:
                self.output_warning("No template fragments found")
                return 0

            headers = ["Template", "Fragment Key", "Type", "Version", "Active", "File Path", "UUID"]
            rows = []

            for fragment in fragments:
                template_name = ""
                if hasattr(fragment, 'template') and fragment.template:
                    template_name = fragment.template.name

                rows.append([
                    template_name,
                    fragment.fragment_key,
                    fragment.fragment_type,
                    fragment.get_display_version(),
                    "Yes" if fragment.is_active else "No",
                    fragment.template_file_path,
                    str(fragment.uuid)
                ])

            self.output_info("Template Fragments:")
            self.output_table(rows, headers=headers)
            return 0

        except Exception as e:
            self.log_error(f"Error listing template fragments: {e}")
            self.output_error(f"Error listing template fragments: {e}")
            return 1

    def show_template(self, template_name):
        """Show detailed template information"""
        self.log_info(f"Showing template details: {template_name}")

        try:
            template = self.session.query(self.template_model).filter_by(name=template_name).first()
            if not template:
                self.output_error(f"Template '{template_name}' not found")
                return 1

            self.output_info(f"Template: {template.name}")
            self.output_info(f"  UUID: {template.uuid}")
            self.output_info(f"  Display Name: {template.display_name}")
            self.output_info(f"  Description: {template.description or 'None'}")
            self.output_info(f"  Layout Type: {template.layout_type}")
            self.output_info(f"  System Template: {'Yes' if template.is_system else 'No'}")
            
            if hasattr(template, 'module') and template.module:
                self.output_info(f"  Module: {template.module.name}")
            
            # Show base fragment
            base_fragment = self.session.query(self.template_fragment_model).filter_by(
                template_uuid=template.uuid,
                fragment_type='base',
                is_active=True
            ).first()
            
            if base_fragment:
                self.output_info(f"  Base Fragment: {base_fragment.fragment_key}")
            else:
                self.output_warning("  Base Fragment: None found")
            
            # Show active fragments
            fragments = self.template_fragment_model.get_all_active_for_template(
                self.session, template.uuid
            )
            
            if fragments:
                self.output_info(f"  Active Fragments ({len(fragments)}):")
                for fragment in fragments:
                    self.output_info(f"    - {fragment.fragment_key} ({fragment.fragment_type})")
            else:
                self.output_info("  Active Fragments: None")

            return 0

        except Exception as e:
            self.log_error(f"Error showing template: {e}")
            self.output_error(f"Error showing template: {e}")
            return 1

    def render_template(self, template_name, data_file=None, output_file=None, force_refresh=False):
        """Render a template"""
        self.log_info(f"Rendering template: {template_name}")

        try:
            template = self.session.query(self.template_model).filter_by(name=template_name).first()
            if not template:
                self.output_error(f"Template '{template_name}' not found")
                return 1

            # Load data if provided
            data = {}
            if data_file:
                data_path = Path(data_file)
                if data_path.exists():
                    data = data_path
                    self.output_info(f"Using data file: {data_file}")
                else:
                    self.output_error(f"Data file not found: {data_file}")
                    return 1

            # Render template
            result = self.renderer.render_template_by_uuid(
                template.uuid, 
                data=data,
                force_refresh=force_refresh
            )

            if result.errors:
                self.output_error("Template rendering failed:")
                for error in result.errors:
                    self.output_error(f"  - {error}")
                return 1

            # Output results
            self.output_success(f"Template '{template_name}' rendered successfully")
            self.output_info(f"  Render time: {result.render_time_ms:.2f}ms")
            self.output_info(f"  Cache hit: {'Yes' if result.cache_hit else 'No'}")
            self.output_info(f"  Content length: {len(result.content)} characters")
            
            if result.fragments_rendered:
                self.output_info(f"  Fragments rendered: {', '.join(result.fragments_rendered)}")

            if result.warnings:
                self.output_warning("Warnings:")
                for warning in result.warnings:
                    self.output_warning(f"  - {warning}")

            # Save to file if specified
            if output_file:
                output_path = Path(output_file)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(result.content)
                self.output_success(f"Rendered content saved to: {output_file}")
            else:
                # Output first 500 characters of content
                preview = result.content[:500]
                if len(result.content) > 500:
                    preview += "..."
                self.output_info("Rendered content preview:")
                print(preview)

            return 0

        except Exception as e:
            self.log_error(f"Error rendering template: {e}")
            self.output_error(f"Error rendering template: {e}")
            return 1

    def render_base_template(self, template_name, data_file=None, output_file=None):
        """Render template using base fragment"""
        self.log_info(f"Rendering base template: {template_name}")

        try:
            template = self.session.query(self.template_model).filter_by(name=template_name).first()
            if not template:
                self.output_error(f"Template '{template_name}' not found")
                return 1

            # Load data if provided
            data = {}
            if data_file:
                data_path = Path(data_file)
                if data_path.exists():
                    data = data_path
                else:
                    self.output_error(f"Data file not found: {data_file}")
                    return 1

            # Render base template
            result = self.renderer.render_base_template(template.uuid, data=data)

            self.output_success(f"Base template '{template_name}' rendered successfully")
            self.output_info(f"  Content length: {len(result.content)} characters")

            # Save to file if specified
            if output_file:
                output_path = Path(output_file)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(result.content)
                self.output_success(f"Rendered content saved to: {output_file}")
            else:
                # Output first 500 characters of content
                preview = result.content[:500]
                if len(result.content) > 500:
                    preview += "..."
                self.output_info("Rendered content preview:")
                print(preview)

            return 0

        except Exception as e:
            self.log_error(f"Error rendering base template: {e}")
            self.output_error(f"Error rendering base template: {e}")
            return 1

    def render_fragment(self, template_name, fragment_key, data_file=None, output_file=None):
        """Render a specific fragment"""
        self.log_info(f"Rendering fragment: {fragment_key} from template: {template_name}")

        try:
            template = self.session.query(self.template_model).filter_by(name=template_name).first()
            if not template:
                self.output_error(f"Template '{template_name}' not found")
                return 1

            # Load data if provided
            data = {}
            if data_file:
                data_path = Path(data_file)
                if data_path.exists():
                    if data_path.suffix.lower() in ['.yaml', '.yml']:
                        with open(data_path, 'r') as f:
                            data = yaml.safe_load(f) or {}
                    elif data_path.suffix.lower() == '.json':
                        with open(data_path, 'r') as f:
                            data = json.load(f)
                else:
                    self.output_error(f"Data file not found: {data_file}")
                    return 1

            # Render fragment
            content = self.renderer.render_fragment_by_key(
                fragment_key, template.uuid, data
            )

            if content.startswith('<!--'):
                self.output_error(f"Fragment rendering failed: {content}")
                return 1

            self.output_success(f"Fragment '{fragment_key}' rendered successfully")
            self.output_info(f"  Content length: {len(content)} characters")

            # Save to file if specified
            if output_file:
                output_path = Path(output_file)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.output_success(f"Rendered content saved to: {output_file}")
            else:
                # Output content
                self.output_info("Rendered fragment content:")
                print(content)

            return 0

        except Exception as e:
            self.log_error(f"Error rendering fragment: {e}")
            self.output_error(f"Error rendering fragment: {e}")
            return 1

    def cache_stats(self):
        """Show cache statistics"""
        self.log_info("Getting cache statistics")

        try:
            stats = self.renderer.get_cache_stats()
            
            self.output_info("Cache Statistics:")
            self.output_info(f"  Template cache entries: {stats['template_cache_size']}")
            self.output_info(f"  Content cache entries: {stats['content_cache_size']}")
            self.output_info(f"  Environment cache entries: {stats['environment_cache_size']}")

            return 0

        except Exception as e:
            self.log_error(f"Error getting cache stats: {e}")
            self.output_error(f"Error getting cache stats: {e}")
            return 1

    def clear_cache(self, template_name=None):
        """Clear template cache"""
        self.log_info(f"Clearing cache for template: {template_name or 'all'}")

        try:
            if template_name:
                template = self.session.query(self.template_model).filter_by(name=template_name).first()
                if not template:
                    self.output_error(f"Template '{template_name}' not found")
                    return 1
                
                self.renderer.invalidate_cache(template_uuid=template.uuid)
                self.output_success(f"Cache cleared for template: {template_name}")
            else:
                self.renderer.clear_cache()
                self.output_success("All caches cleared")

            return 0

        except Exception as e:
            self.log_error(f"Error clearing cache: {e}")
            self.output_error(f"Error clearing cache: {e}")
            return 1

    def close(self):
        """Clean up resources"""
        self.log_debug("Closing template render CLI")
        super().close()


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Manage and render templates",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    parser.add_argument('--no-icons', action='store_true', help='Disable icons in output')
    parser.add_argument('--table-format', choices=['simple', 'grid', 'pipe', 'orgtbl', 'rst'],
                       help='Override table format')

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # List commands
    list_parser = subparsers.add_parser('list', help='List templates or fragments')
    list_subparsers = list_parser.add_subparsers(dest='list_type', help='What to list')
    
    templates_parser = list_subparsers.add_parser('templates', help='List templates')
    templates_parser.add_argument('--module', help='Filter by module name')
    
    fragments_parser = list_subparsers.add_parser('fragments', help='List template fragments')
    fragments_parser.add_argument('--template', help='Filter by template name')

    # Show command
    show_parser = subparsers.add_parser('show', help='Show template details')
    show_parser.add_argument('template_name', help='Template name to show')

    # Render commands
    render_parser = subparsers.add_parser('render', help='Render templates or fragments')
    render_subparsers = render_parser.add_subparsers(dest='render_type', help='What to render')
    
    template_render_parser = render_subparsers.add_parser('template', help='Render template')
    template_render_parser.add_argument('template_name', help='Template name to render')
    template_render_parser.add_argument('--data', help='YAML/JSON data file')
    template_render_parser.add_argument('--output', help='Output file')
    template_render_parser.add_argument('--force-refresh', action='store_true', help='Force cache refresh')
    
    base_render_parser = render_subparsers.add_parser('base', help='Render base fragment')
    base_render_parser.add_argument('template_name', help='Template name to render')
    base_render_parser.add_argument('--data', help='YAML/JSON data file')
    base_render_parser.add_argument('--output', help='Output file')
    
    fragment_render_parser = render_subparsers.add_parser('fragment', help='Render specific fragment')
    fragment_render_parser.add_argument('template_name', help='Template name')
    fragment_render_parser.add_argument('fragment_key', help='Fragment key to render')
    fragment_render_parser.add_argument('--data', help='YAML/JSON data file')
    fragment_render_parser.add_argument('--output', help='Output file')

    # Cache commands
    cache_parser = subparsers.add_parser('cache', help='Cache management')
    cache_subparsers = cache_parser.add_subparsers(dest='cache_action', help='Cache action')
    
    cache_subparsers.add_parser('stats', help='Show cache statistics')
    
    clear_parser = cache_subparsers.add_parser('clear', help='Clear cache')
    clear_parser.add_argument('--template', help='Template name (clear all if not specified)')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Initialize CLI
    cli = None
    try:
        cli = TemplateRenderCLI(
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
            if args.list_type == 'templates':
                return cli.list_templates(module_name=getattr(args, 'module', None))
            elif args.list_type == 'fragments':
                return cli.list_fragments(template_name=getattr(args, 'template', None))
            else:
                list_parser.print_help()
                return 1

        elif args.command == 'show':
            return cli.show_template(args.template_name)

        elif args.command == 'render':
            if args.render_type == 'template':
                return cli.render_template(
                    args.template_name,
                    data_file=getattr(args, 'data', None),
                    output_file=getattr(args, 'output', None),
                    force_refresh=getattr(args, 'force_refresh', False)
                )
            elif args.render_type == 'base':
                return cli.render_base_template(
                    args.template_name,
                    data_file=getattr(args, 'data', None),
                    output_file=getattr(args, 'output', None)
                )
            elif args.render_type == 'fragment':
                return cli.render_fragment(
                    args.template_name,
                    args.fragment_key,
                    data_file=getattr(args, 'data', None),
                    output_file=getattr(args, 'output', None)
                )
            else:
                render_parser.print_help()
                return 1

        elif args.command == 'cache':
            if args.cache_action == 'stats':
                return cli.cache_stats()
            elif args.cache_action == 'clear':
                return cli.clear_cache(template_name=getattr(args, 'template', None))
            else:
                cache_parser.print_help()
                return 1

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