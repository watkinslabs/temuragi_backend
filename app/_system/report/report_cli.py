#!/usr/bin/env python3
"""
Report CLI - Manage reports, templates, and executions
Provides comprehensive report management capabilities
"""

import sys
import json
import argparse
from tabulate import tabulate
from datetime import datetime, timedelta

# Add your app path to import the model and config
sys.path.append('/web/temuragi')

from app.base.cli import BaseCLI

CLI_DESCRIPTION = "Manage reports, templates, and executions"


class ReportCLI(BaseCLI):
    def __init__(self, verbose=False, show_icons=True, table_format=None):
        """Initialize CLI with database connection and report service"""
        super().__init__(
            name="report",
            log_file="logs/report_cli.log",
            connect_db=True,
            verbose=verbose,
            show_icons=show_icons,
            table_format=table_format
        )

        self.log_info("Starting report CLI initialization")

        try:
            from app.classes  import ReportService

            self.service = ReportService(self.session, logger=self.logger)
            self.log_info("Report service initialized successfully")
        except Exception as e:
            self.log_error(f"Failed to initialize report service: {e}")
            raise

    # =====================================================================
    # TEMPLATE OPERATIONS
    # =====================================================================

    def list_templates(self):
        """List all report templates"""
        self.log_info("Listing report templates")

        try:
            templates = self.service.list_report_templates()

            if not templates:
                self.output_warning("No report templates found")
                return 0

            headers = ['Name', 'Display Name', 'Base Template', 'Filters', 'Export', 'Reports']
            rows = []

            for template in templates:
                # Count reports using this template
                report_count = self.session.query(self.service.session.query(Report).filter_by(
                    report_template_id=template.id
                ).count()).scalar()

                rows.append([
                    template.name,
                    template.display_name,
                    template.template.name if template.template else 'N/A',
                    f"{self.icon('check') if template.show_filters else self.icon('cross')} {template.filter_position}",
                    self.icon('check') if template.show_export_buttons else self.icon('cross'),
                    report_count
                ])

            self.output_info(f"Report Templates ({len(templates)} total):")
            self.output_table(rows, headers=headers)

            return 0

        except Exception as e:
            self.log_error(f"Error listing templates: {e}")
            self.output_error(f"Error listing templates: {e}")
            return 1

    def create_template(self, name, display_name, template_id, **kwargs):
        """Create a new report template"""
        self.log_info(f"Creating report template: {name}")

        try:
            template = self.service.create_report_template(
                name=name,
                display_name=display_name,
                template_id=template_id,
                **kwargs
            )

            self.output_success(f"Report template created: {template.name} ({template.id})")
            return 0

        except ValueError as e:
            self.output_error(f"Validation error: {e}")
            return 1
        except Exception as e:
            self.log_error(f"Error creating template: {e}")
            self.output_error(f"Error creating template: {e}")
            return 1

    # =====================================================================
    # REPORT OPERATIONS
    # =====================================================================

    def list_reports(self, category=None, connection=None, show_permissions=False):
        """List all reports with optional filtering"""
        self.log_info(f"Listing reports - category: {category}, connection: {connection}")

        try:
            # Get connection UUID if name provided
            connection_id = None
            if connection:
                conn = self.session.query(Connection).filter_by(name=connection).first()
                if conn:
                    connection_id = conn.id
                else:
                    self.output_warning(f"Connection '{connection}' not found")

            reports = self.service.list_reports(
                category=category,
                connection_id=connection_id
            )

            if not reports:
                self.output_warning("No reports found matching criteria")
                return 0

            if show_permissions:
                headers = ['Slug', 'Name', 'Category', 'Connection', 'Model', 'Template', 'Public', 'Permissions']
            else:
                headers = ['Slug', 'Name', 'Category', 'Connection', 'Model', 'Template', 'Public', 'Last Run']

            rows = []

            for report in reports:
                # Get model name if associated
                model_name = 'None'
                if report.model_id:
                    try:
                        if hasattr(report, 'model') and report.model:
                            model_name = report.model.name
                    except:
                        model_name = 'Unknown'
                
                if show_permissions:
                    # Get permission count
                    from app.models import Permission
                    perm_count = self.session.query(Permission).filter(
                        Permission.service == 'report',
                        Permission.resource == report.slug
                    ).count()

                    rows.append([
                        report.slug,
                        report.name,
                        report.category or 'None',
                        report.connection.name,
                        model_name,
                        report.report_template.name if report.report_template else 'None',
                        self.icon('check') if report.is_public else self.icon('cross'),
                        f"{perm_count} permissions"
                    ])
                else:
                    last_run = 'Never'
                    if report.last_run:
                        last_run = report.last_run.strftime('%Y-%m-%d %H:%M')

                    rows.append([
                        report.slug,
                        report.name,
                        report.category or 'None',
                        report.connection.name,
                        model_name,
                        report.report_template.name if report.report_template else 'None',
                        self.icon('check') if report.is_public else self.icon('cross'),
                        last_run
                    ])

            self.output_info(f"Reports ({len(reports)} total):")
            self.output_table(rows, headers=headers)

            # Show category summary
            categories = {}
            for report in reports:
                cat = report.category or 'Uncategorized'
                categories[cat] = categories.get(cat, 0) + 1

            if len(categories) > 1:
                self.output_info("\nReports by Category:")
                for cat, count in sorted(categories.items()):
                    self.output_info(f"  {cat}: {count}")

            return 0

        except Exception as e:
            self.log_error(f"Error listing reports: {e}")
            self.output_error(f"Error listing reports: {e}")
            return 1
        
    def show_report(self, report_id):
        """Show detailed information about a report"""
        self.log_info(f"Showing report details: {report_id}")

        try:
            report = self.service.get_report(report_id)
            if not report:
                self.output_error(f"Report '{report_id}' not found")
                return 1

            # Get report structure
            structure = self.service.get_report_structure(report.id)

            # Basic info
            self.output_info(f"Report: {report.name}")
            self.output_info("=" * 60)

            # Get model info
            model_info = 'None'
            if report.model_id:
                try:
                    if hasattr(report, 'model') and report.model:
                        model_info = f"{report.model.name} ({report.model_id})"
                    else:
                        model_info = f"Model ID: {report.model_id}"
                except:
                    model_info = f"Model ID: {report.model_id}"

            basic_info = [
                ['Slug', report.slug],
                ['Display Name', report.display or 'N/A'],
                ['Description', (report.description[:50] + '...') if report.description and len(report.description) > 50 else (report.description or 'N/A')],
                ['Category', report.category or 'None'],
                ['Connection', report.connection.name],
                ['Database Type', report.connection.db_type],
                ['Model', model_info],  # Add this
                ['Template', report.report_template.display_name if report.report_template else 'None'],
                ['Created', report.created_at.strftime('%Y-%m-%d %H:%M')],
                ['Last Run', report.last_run.strftime('%Y-%m-%d %H:%M') if report.last_run else 'Never']
            ]

            self.output_table(basic_info, headers=['Property', 'Value'])

            # Flags
            self.output_info("\nSettings:")
            flags = [
                ['Is Model Report', self.icon('check') if report.is_model else self.icon('cross')],  # Add this
                ['Public Access', self.icon('check') if report.is_public else self.icon('cross')],
                ['Auto Run', self.icon('check') if report.is_auto_run else self.icon('cross')],
                ['AJAX Loading', self.icon('check') if report.is_ajax else self.icon('cross')],
                ['Searchable', self.icon('check') if report.is_searchable else self.icon('cross')],
                ['CSV Export', self.icon('check') if report.is_download_csv else self.icon('cross')],
                ['Excel Export', self.icon('check') if report.is_download_xlsx else self.icon('cross')],
                ['Wide Layout', self.icon('check') if report.is_wide else self.icon('cross')],
                ['Published', self.icon('check') if report.is_published else self.icon('cross')],  # Add this
            ]
            self.output_table(flags, headers=['Setting', 'Status'])

            # Columns
            if structure['columns']:
                self.output_info(f"\nColumns ({structure['column_count']}):")
                col_headers = ['Name', 'Display', 'Type', 'Searchable', 'Sortable', 'Format']
                col_rows = []

                for col in structure['columns']:
                    col_rows.append([
                        col.name,
                        col.display_name,
                        col.data_type.display,
                        self.icon('check') if col.is_searchable else self.icon('cross'),
                        self.icon('check') if col.is_sortable else self.icon('cross'),
                        col.format_string or 'None'
                    ])

                self.output_table(col_rows, headers=col_headers)

            # Variables
            if structure['variables']:
                self.output_info(f"\nVariables ({structure['variable_count']}):")
                var_headers = ['Name', 'Display', 'Type', 'Input', 'Required', 'Default']
                var_rows = []

                for var in structure['variables']:
                    var_rows.append([
                        var.name,
                        var.display_name,
                        var.data_type.display,
                        var.variable_type.display,
                        self.icon('check') if var.is_required else self.icon('cross'),
                        var.default_value or 'None'
                    ])

                self.output_table(var_rows, headers=var_headers)

            # Show sample query
            if self.verbose:
                self.output_info("\nQuery:")
                self.output_info("-" * 60)
                # Show first 500 chars of query
                query_preview = report.query[:500]
                if len(report.query) > 500:
                    query_preview += "\n... (truncated)"
                self.output(query_preview)

            return 0

        except Exception as e:
            self.log_error(f"Error showing report: {e}")
            self.output_error(f"Error showing report: {e}")
            return 1

    def create_report(self, slug, name, query_file, connection, **kwargs):
        """Create a new report"""
        self.log_info(f"Creating report: {slug}")

        try:
            # Read query from file
            try:
                with open(query_file, 'r') as f:
                    query = f.read()
            except FileNotFoundError:
                self.output_error(f"Query file not found: {query_file}")
                return 1

            # Get connection
            conn = self.session.query(Connection).filter_by(name=connection).first()
            if not conn:
                self.output_error(f"Connection '{connection}' not found")
                return 1

            # Get template if specified
            template_id = None
            if kwargs.get('template'):
                template = self.service.get_report_template(kwargs['template'])
                if template:
                    template_id = template.id
                    del kwargs['template']

            # Get model if specified
            model_id = None
            if kwargs.get('model'):
                model = self.service.get_model(kwargs['model'])
                if model:
                    model_id = model.id
                    self.output_info(f"Associating with model: {model.name}")
                else:
                    self.output_warning(f"Model '{kwargs['model']}' not found - proceeding without model association")
                del kwargs['model']

            report = self.service.create_report(
                slug=slug,
                name=name,
                query=query,
                connection_id=conn.id,
                report_template_id=template_id,
                model_id=model_id,
                **kwargs
            )

            self.output_success(f"Report created: {report.slug} ({report.id})")
            self.output_info(f"Permissions created: report:{report.slug}:*")
            if model_id:
                self.output_info(f"Associated with model: {model.name}")

            return 0

        except ValueError as e:
            self.output_error(f"Validation error: {e}")
            return 1
        except Exception as e:
            self.log_error(f"Error creating report: {e}")
            self.output_error(f"Error creating report: {e}")
            return 1
        
    def delete_report(self, report_id, force=False):
        """Delete a report"""
        self.log_info(f"Deleting report: {report_id}")

        try:
            report = self.service.get_report(report_id)
            if not report:
                self.output_error(f"Report '{report_id}' not found")
                return 1

            if not force:
                # Confirm deletion
                self.output_warning(f"This will delete report '{report.name}' and all associated data")
                response = input("Are you sure? (y/N): ")
                if response.lower() != 'y':
                    self.output_info("Deletion cancelled")
                    return 0

            self.service.delete_report(report.id)
            self.output_success(f"Report deleted: {report.slug}")

            return 0

        except Exception as e:
            self.log_error(f"Error deleting report: {e}")
            self.output_error(f"Error deleting report: {e}")
            return 1

    def duplicate_report(self, source_id, new_name, new_slug=None):
        """Duplicate an existing report"""
        self.log_info(f"Duplicating report: {source_id}")

        try:
            source = self.service.get_report(source_id)
            if not source:
                self.output_error(f"Source report '{source_id}' not found")
                return 1

            new_report, message = self.service.duplicate_report(
                source.id, new_name, new_slug
            )

            self.output_success(message)
            self.output_info(f"New report: {new_report.slug} ({new_report.id})")

            return 0

        except ValueError as e:
            self.output_error(f"Error: {e}")
            return 1
        except Exception as e:
            self.log_error(f"Error duplicating report: {e}")
            self.output_error(f"Error duplicating report: {e}")
            return 1

    # =====================================================================
    # EXECUTION OPERATIONS
    # =====================================================================

    def test_report(self, report_id):
        """Test a report query"""
        self.log_info(f"Testing report: {report_id}")

        try:
            report = self.service.get_report(report_id)
            if not report:
                self.output_error(f"Report '{report_id}' not found")
                return 1

            self.output_info(f"Testing report: {report.name}")
            self.output_info(f"Connection: {report.connection.name} ({report.connection.db_type})")

            # Test the query
            columns = self.service.test_report_query(report.id)

            self.output_success("Query executed successfully!")
            self.output_info(f"Detected {len(columns)} columns:")

            headers = ['Column Name', 'Display Name', 'Type']
            rows = []

            for col in columns:
                rows.append([
                    col['name'],
                    col['display'],
                    col['type']
                ])

            self.output_table(rows, headers=headers)

            return 0

        except Exception as e:
            self.log_error(f"Query test failed: {e}")
            self.output_error(f"Query test failed: {e}")
            return 1

    def execute_report(self, report_id, output_file=None, params=None):
        """Execute a report"""
        self.log_info(f"Executing report: {report_id}")

        try:
            report = self.service.get_report(report_id)
            if not report:
                self.output_error(f"Report '{report_id}' not found")
                return 1

            # Parse parameters
            request_data = {
                'draw': 1,
                'start': 0,
                'length': 100,
                'vars': {}
            }

            if params:
                for param in params:
                    if '=' in param:
                        key, value = param.split('=', 1)
                        request_data['vars'][key] = value

            self.output_info(f"Executing report: {report.name}")
            if request_data['vars']:
                self.output_info(f"Parameters: {request_data['vars']}")

            # Execute report
            result = self.service.execute_report(report.id, request_data)

            if 'error' in result:
                self.output_error(f"Execution failed: {result['error']}")
                return 1

            # Display results
            self.output_success(f"Report executed successfully!")
            self.output_info(f"Total records: {result['recordsTotal']}")
            self.output_info(f"Filtered records: {result['recordsFiltered']}")

            if result['data']:
                # Show first 10 rows
                headers = result.get('headers', list(result['data'][0].keys()) if result['data'] else [])
                rows = []

                for i, row in enumerate(result['data'][:10]):
                    row_data = []
                    for header in headers:
                        value = row.get(header, '')
                        # Truncate long values
                        if isinstance(value, str) and len(value) > 50:
                            value = value[:47] + '...'
                        row_data.append(value)
                    rows.append(row_data)

                self.output_info(f"\nShowing first {min(10, len(result['data']))} rows:")
                self.output_table(rows, headers=headers)

                if len(result['data']) > 10:
                    self.output_info(f"... and {len(result['data']) - 10} more rows")

            # Save to file if requested
            if output_file:
                with open(output_file, 'w') as f:
                    json.dump(result, f, indent=2, default=str)
                self.output_success(f"Results saved to: {output_file}")

            return 0

        except Exception as e:
            self.log_error(f"Error executing report: {e}")
            self.output_error(f"Error executing report: {e}")
            return 1

    def list_executions(self, report_id=None, limit=20):
        """List recent report executions"""
        self.log_info(f"Listing executions - report: {report_id}, limit: {limit}")

        try:
            if report_id:
                report = self.service.get_report(report_id)
                if not report:
                    self.output_error(f"Report '{report_id}' not found")
                    return 1

                executions = self.service.get_report_execution_history(report.id, limit)
                self.output_info(f"Execution History for: {report.name}")
            else:
                # Get all recent executions
                from app.models import ReportExecution
                executions = self.session.query(ReportExecution)\
                    .order_by(ReportExecution.executed_at.desc())\
                    .limit(limit)\
                    .all()
                self.output_info(f"Recent Executions (all reports):")

            if not executions:
                self.output_warning("No executions found")
                return 0

            headers = ['Report', 'Executed At', 'Duration (ms)', 'Rows', 'Status', 'User']
            rows = []

            for exec in executions:
                rows.append([
                    exec.report.name if exec.report else 'Unknown',
                    exec.executed_at.strftime('%Y-%m-%d %H:%M:%S'),
                    exec.duration_ms or 'N/A',
                    exec.row_count or 0,
                    f"{self.icon('check') if exec.status == 'success' else self.icon('cross')} {exec.status}",
                    'System' if not exec.user_id else 'User'
                ])

            self.output_table(rows, headers=headers)

            # Show error details if any failed
            failed = [e for e in executions if e.status != 'success']
            if failed and self.verbose:
                self.output_warning(f"\nFailed Executions ({len(failed)}):")
                for exec in failed[:5]:
                    self.output_error(f"  {exec.executed_at}: {exec.error_message}")

            return 0

        except Exception as e:
            self.log_error(f"Error listing executions: {e}")
            self.output_error(f"Error listing executions: {e}")
            return 1

    # =====================================================================
    # PERMISSION OPERATIONS
    # =====================================================================

    def assign_report(self, report_id, role_name, actions=None):
        """Assign report to a role"""
        self.log_info(f"Assigning report {report_id} to role {role_name}")

        try:
            report = self.service.get_report(report_id)
            if not report:
                self.output_error(f"Report '{report_id}' not found")
                return 1

            # Get role
            from app.models import Role
            role = self.session.query(Role).filter_by(name=role_name).first()
            if not role:
                self.output_error(f"Role '{role_name}' not found")
                return 1

            # Parse actions
            if actions:
                action_list = [a.strip() for a in actions.split(',')]
            else:
                action_list = None

            success, message = self.service.assign_report_to_role(
                report.id, role.id, action_list
            )

            if success:
                self.output_success(message)
            else:
                self.output_error(message)

            return 0 if success else 1

        except Exception as e:
            self.log_error(f"Error assigning report: {e}")
            self.output_error(f"Error assigning report: {e}")
            return 1

    # =====================================================================
    # UTILITY OPERATIONS
    # =====================================================================

    def stats(self):
        """Show report system statistics"""
        self.log_info("Generating report statistics")

        try:
            stats = self.service.get_dashboard_stats()

            self.output_info("Report System Statistics")
            self.output_info("=" * 60)

            # Report stats
            self.output_info("\nReports:")
            report_stats = [
                ['Total Reports', stats['reports']['total']],
                ['Public Reports', stats['reports']['public']],
                ['Private Reports', stats['reports']['private']],
                ['Report Templates', stats['templates']]
            ]
            self.output_table(report_stats, headers=['Metric', 'Count'])

            # Execution stats
            self.output_info("\nExecutions:")
            exec_stats = [
                ['Total Executions', stats['executions']['total']],
                ['Successful', stats['executions']['successful']],
                ['Failed', stats['executions']['failed']],
                ['Success Rate', f"{stats['executions']['success_rate']:.1f}%"]
            ]
            self.output_table(exec_stats, headers=['Metric', 'Value'])

            # Categories
            if stats['categories']:
                self.output_info("\nReports by Category:")
                cat_rows = [[cat, count] for cat, count in sorted(stats['categories'].items())]
                self.output_table(cat_rows, headers=['Category', 'Count'])

            # Connections
            if stats['connections']:
                self.output_info("\nReports by Connection:")
                conn_rows = [[conn, count] for conn, count in sorted(stats['connections'].items())]
                self.output_table(conn_rows, headers=['Connection', 'Count'])

            return 0

        except Exception as e:
            self.log_error(f"Error generating statistics: {e}")
            self.output_error(f"Error generating statistics: {e}")
            return 1

    def export_report(self, report_id, output_file):
        """Export report definition"""
        self.log_info(f"Exporting report: {report_id}")

        try:
            report = self.service.get_report(report_id)
            if not report:
                self.output_error(f"Report '{report_id}' not found")
                return 1

            definition = self.service.export_report_definition(report.id)

            with open(output_file, 'w') as f:
                json.dump(definition, f, indent=2)

            self.output_success(f"Report exported to: {output_file}")
            self.output_info(f"Columns: {len(definition['columns'])}")
            self.output_info(f"Variables: {len(definition['variables'])}")

            return 0

        except Exception as e:
            self.log_error(f"Error exporting report: {e}")
            self.output_error(f"Error exporting report: {e}")
            return 1

    def import_report(self, input_file, connection):
        """Import report definition"""
        self.log_info(f"Importing report from: {input_file}")

        try:
            # Read definition
            try:
                with open(input_file, 'r') as f:
                    definition = json.load(f)
            except FileNotFoundError:
                self.output_error(f"File not found: {input_file}")
                return 1
            except json.JSONDecodeError as e:
                self.output_error(f"Invalid JSON: {e}")
                return 1

            # Get connection
            conn = self.session.query(Connection).filter_by(name=connection).first()
            if not conn:
                self.output_error(f"Connection '{connection}' not found")
                return 1

            report = self.service.import_report_definition(definition, conn.id)

            self.output_success(f"Report imported: {report.slug} ({report.id})")
            self.output_info(f"Columns: {len(report.columns)}")
            self.output_info(f"Variables: {len(report.variables)}")

            return 0

        except Exception as e:
            self.log_error(f"Error importing report: {e}")
            self.output_error(f"Error importing report: {e}")
            return 1

    def close(self):
        """Clean up resources"""
        self.log_debug("Closing report CLI")
        super().close()


def main():
    """Entry point for report CLI"""
    parser = argparse.ArgumentParser(
        description=CLI_DESCRIPTION,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
        """
    )

    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    parser.add_argument('--no-icons', action='store_true', help='Disable icons in output')
    parser.add_argument('--table-format', choices=['simple', 'grid', 'pipe', 'orgtbl'],
                       help='Table format')

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # List command
    list_parser = subparsers.add_parser('list', help='List reports')
    list_parser.add_argument('--category', '-c', help='Filter by category')
    list_parser.add_argument('--connection', help='Filter by connection')
    list_parser.add_argument('--permissions', action='store_true', help='Show permission info')

    # Show command
    show_parser = subparsers.add_parser('show', help='Show report details')
    show_parser.add_argument('report', help='Report slug or UUID')

    # Create command
    create_parser = subparsers.add_parser('create', help='Create new report')
    create_parser.add_argument('slug', help='Report slug')
    create_parser.add_argument('name', help='Report name')
    create_parser.add_argument('--query-file', '-q', required=True, help='SQL query file')
    create_parser.add_argument('--connection', '-c', required=True, help='Database connection')
    create_parser.add_argument('--description', '-d', help='Report description')
    create_parser.add_argument('--category', help='Report category')
    create_parser.add_argument('--template', help='Report template name')
    create_parser.add_argument('--model', help='Associated model name or UUID') 
    create_parser.add_argument('--public', action='store_true', help='Make report public')

    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete report')
    delete_parser.add_argument('report', help='Report slug or UUID')
    delete_parser.add_argument('--force', '-f', action='store_true', help='Skip confirmation')

    # Duplicate command
    dup_parser = subparsers.add_parser('duplicate', help='Duplicate report')
    dup_parser.add_argument('source', help='Source report slug or UUID')
    dup_parser.add_argument('name', help='New report name')
    dup_parser.add_argument('--slug', help='New report slug (auto-generated if not provided)')

    # Test command
    test_parser = subparsers.add_parser('test', help='Test report query')
    test_parser.add_argument('report', help='Report slug or UUID')

    # Execute command
    exec_parser = subparsers.add_parser('execute', help='Execute report')
    exec_parser.add_argument('report', help='Report slug or UUID')
    exec_parser.add_argument('--output', '-o', help='Output file (JSON)')
    exec_parser.add_argument('--param', '-p', action='append', help='Parameters (key=value)')

    # Executions command
    execs_parser = subparsers.add_parser('executions', help='List executions')
    execs_parser.add_argument('--report', '-r', help='Filter by report')
    execs_parser.add_argument('--limit', '-l', type=int, default=20, help='Number of results')

    # Assign command
    assign_parser = subparsers.add_parser('assign', help='Assign report to role')
    assign_parser.add_argument('report', help='Report slug or UUID')
    assign_parser.add_argument('role', help='Role name')
    assign_parser.add_argument('--actions', '-a', help='Comma-separated actions')

    # Templates command
    templates_parser = subparsers.add_parser('templates', help='List report templates')

    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show statistics')

    # Export command
    export_parser = subparsers.add_parser('export', help='Export report definition')
    export_parser.add_argument('report', help='Report slug or UUID')
    export_parser.add_argument('output', help='Output file')

    # Import command
    import_parser = subparsers.add_parser('import', help='Import report definition')
    import_parser.add_argument('input', help='Input file')
    import_parser.add_argument('connection', help='Database connection name')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Initialize CLI
    cli = None
    try:
        cli = ReportCLI(
            verbose=args.verbose,
            show_icons=not args.no_icons,
            table_format=args.table_format
        )
    except Exception as e:
        print(f"Error initializing CLI: {e}")
        return 1

    # Execute command
    try:
        if args.command == 'list':
            return cli.list_reports(
                category=args.category,
                connection=args.connection,
                show_permissions=args.permissions
            )

        elif args.command == 'show':
            return cli.show_report(args.report)

        elif args.command == 'create':
            kwargs = {}
            if args.description:
                kwargs['description'] = args.description
            if args.category:
                kwargs['category'] = args.category
            if args.template:
                kwargs['template'] = args.template
            if args.model:
                kwargs['model'] = args.model
            if args.public:
                kwargs['is_public'] = True

            return cli.create_report(
                args.slug,
                args.name,
                args.query_file,
                args.connection,
                **kwargs
            )

        elif args.command == 'delete':
            return cli.delete_report(args.report, args.force)

        elif args.command == 'duplicate':
            return cli.duplicate_report(args.source, args.name, args.slug)

        elif args.command == 'test':
            return cli.test_report(args.report)

        elif args.command == 'execute':
            return cli.execute_report(args.report, args.output, args.param)

        elif args.command == 'executions':
            return cli.list_executions(args.report, args.limit)

        elif args.command == 'assign':
            return cli.assign_report(args.report, args.role, args.actions)

        elif args.command == 'templates':
            return cli.list_templates()

        elif args.command == 'stats':
            return cli.stats()

        elif args.command == 'export':
            return cli.export_report(args.report, args.output)

        elif args.command == 'import':
            return cli.import_report(args.input, args.connection)

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