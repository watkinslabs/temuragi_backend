#!/usr/bin/env python3
"""
Forms CLI - Test Miner's form_metadata function
Enhanced with custom actions support for list generators
"""

import sys
import json
from datetime import datetime, date
import argparse
from pprint import pprint
from app.base.cli import BaseCLI
from app.register.classes import get_model, _class_registry

from .form_class import FormGenerator
from .page_creator_class import ModelPageCreator

CLI_DESCRIPTION = "Test Miner's form_metadata function"


class SafeJSONEncoder(json.JSONEncoder):
    """JSON encoder that handles SQLAlchemy and other non-serializable objects"""
    def default(self, obj):
        if hasattr(obj, '__dict__'):
            # For SQLAlchemy objects with __dict__
            return str(obj)
        elif isinstance(obj, (datetime, date)):
            return obj.isoformat()
        elif isinstance(obj, set):
            return list(obj)
        else:
            # Fallback to string representation
            return str(obj)


class FormsCLI(BaseCLI):
    def __init__(self, verbose=False, show_icons=True, table_format=None):
        """Initialize CLI with database connection"""
        super().__init__(
            name="forms",
            log_file="logs/forms_cli.log",
            connect_db=True,
            verbose=verbose,
            show_icons=show_icons,
            table_format=table_format
        )

        # Mock flask.g for Miner
        import flask
        flask.g = type('g', (), {
            'session': self.session,
            'auth_context': {'user_id': 'forms-cli', 'token_id': 'forms-cli'}
        })()

        from app.classes import Miner
        if not Miner:
            raise RuntimeError("Miner class not found in registry")
        self.miner = Miner(self.app)

    def parse_custom_actions(self, actions_str):
        """
        Parse custom actions from CLI input
        
        Format examples:
        - "none" or "no" -> no actions
        - "edit,delete" -> simple actions
        - "edit:url=/custom/edit,delete,create:url=/custom/create:icon=fa-plus"
        
        Returns list of action dicts or None
        """
        if not actions_str:
            return None
            
        # Handle special cases
        if actions_str.lower() in ['none', 'no', 'false']:
            return []
            
        # Parse actions
        actions = []
        action_parts = actions_str.split(',')
        
        for part in action_parts:
            if ':' in part:
                # Complex action with properties
                action_config = {}
                sub_parts = part.split(':')
                action_config['name'] = sub_parts[0].strip()
                
                # Parse properties
                for prop in sub_parts[1:]:
                    if '=' in prop:
                        key, value = prop.split('=', 1)
                        action_config[key.strip()] = value.strip()
                
                actions.append(action_config)
            else:
                # Simple action name
                actions.append(part.strip())
                
        return actions

    def create_report_datatable_page_with_actions(self, report_slug, actions=None,
                                              data_url=None, show_actions=None):
        """Create a page with the DataTable template for a report with custom actions"""

        from .list_generator_class import ReportDataTableGenerator
        from app.models import Page, PageFragment, Template
        import hashlib
        from datetime import datetime

        try:
            # Generate the DataTable template string
            generator = ReportDataTableGenerator(self.session, self.logger)

            # Load report to get info
            report = generator.load_report_by_slug(report_slug)

            # Generate config - page_actions will be fetched automatically
            config = generator.generate_datatable_config(
                report_slug,
                data_url=data_url
            )

            # Generate the template HTML
            template_html = generator.generate_jinja_template(
                report_slug,
                data_url=data_url
            )

            # Create page directly
            page_slug = f"f/{report_slug}"

            # Check if page exists
            existing_page = self.session.query(Page).filter_by(slug=page_slug).first()

            if existing_page:
                self.output_warning(f"Page already exists at /{page_slug}")

                # Update the fragment
                fragment = self.session.query(PageFragment).filter_by(
                    page_id=existing_page.id,
                    fragment_key='main_content',
                    is_active=True
                ).first()

                if fragment:
                    fragment.content_source = template_html
                    fragment.content_hash = hashlib.sha256(template_html.encode('utf-8')).hexdigest()
                    fragment.updated_at = datetime.utcnow()
                    self.session.commit()
                    self.output_success(f"Updated page fragment for /{page_slug}")
                    
                    # Show action summary
                    if config.get('actions'):
                        action_summary = []
                        page_actions = [a for a in config['actions'] if a.get('mode') == 'page']
                        row_actions = [a for a in config['actions'] if a.get('mode') != 'page']
                        
                        if page_actions:
                            action_summary.append(f"{len(page_actions)} page actions")
                        if row_actions:
                            action_summary.append(f"{len(row_actions)} row actions")
                        
                        if action_summary:
                            self.output_info(f"Actions configured: {', '.join(action_summary)}")
                            for action in config['actions']:
                                self.output_info(f"  - {action['name']} ({action.get('mode', 'row')}): {action.get('title', action['name'])}")
                    else:
                        self.output_info("No actions configured")
                else:
                    self.output_error("No active fragment found to update")
                    return 1
            else:
                # Get default template
                template = self.session.query(Template).first()
                if not template:
                    self.output_error("No templates found in database")
                    return 1

                # Create new page
                page = Page(
                    name=f"{report.name} Report",
                    title=report.display or report.name,
                    slug=page_slug,
                    template_id=template.id,
                    meta_description=report.description or f"View {report.name} data",
                    published=True,
                    requires_auth=True,
                    cache_duration=0,
                    sort_order=999
                )

                self.session.add(page)
                self.session.flush()

                # Create fragment
                fragment = PageFragment(
                    page_id=page.id,
                    fragment_type='content',
                    fragment_name='Main Content',
                    fragment_key='main_content',
                    content_type='text/html',
                    version_number=1,
                    is_active=True,
                    content_source=template_html,
                    content_hash=hashlib.sha256(template_html.encode('utf-8')).hexdigest(),
                    description=f"DataTable view for {report.name}",
                    is_published=True,
                    sort_order=0,
                    cache_duration=0
                )

                self.session.add(fragment)
                self.session.commit()

                self.output_success(f"Created page at /{page_slug}")
                
                # Show action summary
                if custom_actions is not None:
                    if custom_actions:
                        self.output_info(f"Actions configured: {custom_actions}")
                    else:
                        self.output_info("No actions configured (explicitly disabled)")

            return 0

        except Exception as e:
            self.session.rollback()
            self.output_error(f"Error: {e}")
            if self.verbose:
                import traceback
                traceback.print_exc()
            return 1

    # ... rest of the class methods remain the same ...

    def test_form_metadata(self, model_name, generate_html=False, output_file=None,
                          create_page=False, prefix="", raw_form=False, debug=False,
                          form_mode="both", show_required_badge=True, show_optional_badge=True):
        """
        Test the Miner's handle_form_metadata function and optionally generate HTML

        Args:
            model_name: Name of the model
            generate_html: Whether to generate HTML form
            output_file: File to save output to
            create_page: Whether to create page in database
            prefix: Prefix for form element IDs
            raw_form: Generate only the form without wrapper/scripts
            debug: Show debug information about field requirements
            form_mode: Form mode - "create", "edit", or "both"
            show_required_badge: Show "Required" badges on form fields
            show_optional_badge: Show "Optional" badges on form fields
        """
        # Get model class
        model_class = get_model(model_name)
        if not model_class:
            self.output_error(f"Model '{model_name}' not found")
            self.output_info("\nAvailable models:")
            self.list_models()
            return 1

        self.log_info(f"Testing handle_form_metadata for {model_name}")

        try:
            # Call Miner's handle_form_metadata
            response = self.miner.handle_form_metadata(model_class, {}, {})
            pprint(response)
            # Get JSON from Flask response
            result = response

            if debug and result.get('success'):
                # Debug field requirements
                metadata = result['metadata']
                generator = FormGenerator(metadata, prefix=prefix,
                                        show_required_badge=show_required_badge,
                                        show_optional_badge=show_optional_badge)
                generator.debug_field_requirements()

            if generate_html and result.get('success'):
                # Generate HTML form
                metadata = result['metadata']
                generator = FormGenerator(metadata, prefix=prefix,
                                        show_required_badge=show_required_badge,
                                        show_optional_badge=show_optional_badge)

                if raw_form:
                    # Generate only the form without wrapper
                    form_html = generator.generate_form(
                        form_mode=form_mode,
                        include_relationships=False,
                        include_wrapper=False
                    )
                else:
                    # Generate complete template with wrapper and scripts
                    form_html = generator.generate_form(
                        form_mode=form_mode,
                        include_relationships=False,
                        include_wrapper=True
                    )

                if create_page:
                    # Use ModelPageCreator to create page
                    creator = ModelPageCreator(self.session, self.logger)

                    success, page, fragment, message = creator.create_management_page(
                        model_name, form_html
                    )

                    if success:
                        self.output_success(message)
                        if page:
                            self.output_info(f"Page URL: /{page.slug}")
                    else:
                        self.output_error(message)
                        return 1

                elif output_file:
                    # Save to file
                    with open(output_file, 'w') as f:
                        f.write(form_html)
                    self.output_success(f"Form template saved to: {output_file}")
                else:
                    # Print to stdout
                    print(form_html)
            else:
                # Just print JSON
                print(json.dumps(result, indent=2, cls=SafeJSONEncoder))

            return 0

        except Exception as e:
            self.output_error(f"Error: {e}")
            if self.verbose:
                import traceback
                traceback.print_exc()
            return 1

    def test_multiple_forms(self, model_name, show_required_badge=True, show_optional_badge=True):
        """Test generating multiple forms with different prefixes on same page"""
        # Get model class
        model_class = get_model(model_name)
        if not model_class:
            self.output_error(f"Model '{model_name}' not found")
            return 1

        self.log_info(f"Generating multiple forms demo for {model_name}")

        try:
            # Call Miner's handle_form_metadata
            response = self.miner.handle_form_metadata(model_class, {}, {})
            result = response

            if result.get('success'):
                metadata = result['metadata']

                # Generate page with two forms
                html = []
                html.append('{% block title %}Multiple Forms Demo - ' + model_name + '{% endblock %}')
                html.append('')
                html.append('{% block content %}')
                html.append('<div class="container-fluid">')
                html.append('  <div class="row">')
                html.append('    <div class="col-md-6">')
                html.append('      <h3>Form 1 - Create New</h3>')

                # First form with prefix "form1_"
                generator1 = FormGenerator(metadata, prefix="form1_",
                                         show_required_badge=show_required_badge,
                                         show_optional_badge=show_optional_badge)
                form1 = generator1.generate_form(
                    form_mode="create",
                    include_relationships=False,
                    include_wrapper=False
                )
                html.append(form1)

                html.append('    </div>')
                html.append('    <div class="col-md-6">')
                html.append('      <h3>Form 2 - Create Another</h3>')

                # Second form with prefix "form2_"
                generator2 = FormGenerator(metadata, prefix="form2_",
                                         show_required_badge=show_required_badge,
                                         show_optional_badge=show_optional_badge)
                form2 = generator2.generate_form(
                    form_mode="create",
                    include_relationships=False,
                    include_wrapper=False
                )
                html.append(form2)

                html.append('    </div>')
                html.append('  </div>')
                html.append('</div>')
                html.append('{% endblock %}')
                html.append('')
                html.append('{% block scripts %}')
                html.append('<script>')
                html.append('// Handle multiple forms')
                html.append('["form1_", "form2_"].forEach(prefix => {')
                html.append(f'  const formId = prefix + "{model_name.lower()}_form";')
                html.append('  const form = document.getElementById(formId);')
                html.append('  ')
                html.append('  form.addEventListener("submit", async (e) => {')
                html.append('    e.preventDefault();')
                html.append('    console.log("Submitting form with prefix:", prefix);')
                html.append('    // Form submission logic here')
                html.append('  });')
                html.append('});')
                html.append('</script>')
                html.append('{% endblock %}')

                print('\n'.join(html))

            return 0

        except Exception as e:
            self.output_error(f"Error: {e}")
            if self.verbose:
                import traceback
                traceback.print_exc()
            return 1

    def list_models(self):
        """List all available models"""
        models = []

        for name in sorted(_class_registry.keys()):
            cls = _class_registry[name]
            if hasattr(cls, '__tablename__'):
                models.append(name)

        if models:
            for model in models:
                print(f"  {model}")
        else:
            self.output_warning("No models found")


def main():
    """Entry point"""
    parser = argparse.ArgumentParser(description=CLI_DESCRIPTION)
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--no-icons', action='store_true', help='Disable icons')

    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # List command
    list_parser = subparsers.add_parser('list', help='List all available models')

    # Generate command
    generate_parser = subparsers.add_parser('generate', help='Generate form HTML')
    generate_parser.add_argument('model', help='Model name')
    generate_parser.add_argument('--output', '-o', help='Save form to file')
    generate_parser.add_argument('--create-page', '-p', action='store_true',
                               help='Create page and fragment in database')
    generate_parser.add_argument('--prefix', default='', help='Prefix for form element IDs')
    generate_parser.add_argument('--raw-form', action='store_true',
                               help='Generate only form without wrapper/scripts')
    generate_parser.add_argument('--mode', choices=['create', 'edit', 'both'], default='both',
                               help='Form mode: create-only, edit-only, or both (default: both)')
    generate_parser.add_argument('--no-required-badge', action='store_true',
                               help='Hide "Required" badges on form fields')
    generate_parser.add_argument('--no-optional-badge', action='store_true',
                               help='Hide "Optional" badges on form fields')
    generate_parser.add_argument('--no-badges', action='store_true',
                               help='Hide both "Required" and "Optional" badges')

    # Debug command
    debug_parser = subparsers.add_parser('debug', help='Debug model metadata')
    debug_parser.add_argument('model', help='Model name')
    debug_parser.add_argument('--no-required-badge', action='store_true',
                            help='Hide "Required" badges on form fields')
    debug_parser.add_argument('--no-optional-badge', action='store_true',
                            help='Hide "Optional" badges on form fields')
    debug_parser.add_argument('--no-badges', action='store_true',
                            help='Hide both "Required" and "Optional" badges')

    # Test command (for testing form metadata)
    test_parser = subparsers.add_parser('test', help='Test form metadata output')
    test_parser.add_argument('model', help='Model name')

    # Multiple command (demo multiple forms)
    multiple_parser = subparsers.add_parser('multiple', help='Demo multiple forms on one page')
    multiple_parser.add_argument('model', help='Model name')
    multiple_parser.add_argument('--no-required-badge', action='store_true',
                               help='Hide "Required" badges on form fields')
    multiple_parser.add_argument('--no-optional-badge', action='store_true',
                               help='Hide "Optional" badges on form fields')
    multiple_parser.add_argument('--no-badges', action='store_true',
                               help='Hide both "Required" and "Optional" badges')

    # Enhanced report-datatable command
    report_parser = subparsers.add_parser('report-datatable',
                                        help='Create a DataTable page for a report')
    report_parser.add_argument('report_slug', help='Slug of the report')
    report_parser.add_argument('--data-url', '-u',
                            help='Override data URL for the table')

    args = parser.parse_args()

    # If no command specified, show help
    if not args.command:
        parser.print_help()
        return 1

    cli = FormsCLI(
        verbose=args.verbose,
        show_icons=not args.no_icons
    )

    try:
        if args.command == 'list':
            cli.list_models()
            return 0

        elif args.command == 'generate':
            # Handle badge flags
            show_required = True
            show_optional = True

            if hasattr(args, 'no_badges') and args.no_badges:
                show_required = False
                show_optional = False
            else:
                if hasattr(args, 'no_required_badge') and args.no_required_badge:
                    show_required = False
                if hasattr(args, 'no_optional_badge') and args.no_optional_badge:
                    show_optional = False

            return cli.test_form_metadata(
                args.model,
                generate_html=True,  # Always generate HTML for this command
                output_file=args.output,
                create_page=args.create_page,
                prefix=args.prefix,
                raw_form=args.raw_form,
                debug=False,
                form_mode=args.mode,
                show_required_badge=show_required,
                show_optional_badge=show_optional
            )

        elif args.command == 'debug':
            # Handle badge flags
            show_required = True
            show_optional = True

            if hasattr(args, 'no_badges') and args.no_badges:
                show_required = False
                show_optional = False
            else:
                if hasattr(args, 'no_required_badge') and args.no_required_badge:
                    show_required = False
                if hasattr(args, 'no_optional_badge') and args.no_optional_badge:
                    show_optional = False

            return cli.test_form_metadata(
                args.model,
                generate_html=False,
                debug=True,
                show_required_badge=show_required,
                show_optional_badge=show_optional
            )

        elif args.command == 'test':
            # Just output the JSON metadata
            return cli.test_form_metadata(
                args.model,
                generate_html=False,
                debug=False
            )

        elif args.command == 'multiple':
            # Handle badge flags
            show_required = True
            show_optional = True

            if hasattr(args, 'no_badges') and args.no_badges:
                show_required = False
                show_optional = False
            else:
                if hasattr(args, 'no_required_badge') and args.no_required_badge:
                    show_required = False
                if hasattr(args, 'no_optional_badge') and args.no_optional_badge:
                    show_optional = False

            return cli.test_multiple_forms(
                args.model,
                show_required_badge=show_required,
                show_optional_badge=show_optional
            )

        elif args.command == 'report-datatable':
            return cli.create_report_datatable_page_with_actions(
                args.report_slug,
                data_url=args.data_url
            )

        else:
            parser.print_help()
            return 1

    except KeyboardInterrupt:
        cli.output_info("\nCancelled")
        return 1
    except Exception as e:
        cli.output_error(f"Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1
    finally:
        cli.close()


if __name__ == '__main__':
    sys.exit(main())