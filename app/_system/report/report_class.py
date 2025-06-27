import json
import logging
from typing import Optional, List, Dict, Any, Union, Tuple
from uuid import UUID
from datetime import datetime
from sqlalchemy import text, func
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

try:
    from app.classes import QueryMetadataError, QueryMetadataExtractor
    from app.classes import ReportQueryExecutor
except Exception as ex:
    pass

#from .metadata_extractor_class import QueryMetadataExtractor
try:
    from app.models import (
        Report, ReportColumn, ReportVariable, ReportExecution,
        ReportSchedule,  Connection, DataType, ReportTemplate,
        VariableType, DatabaseType, Template, Model
    )
except Exception as ex:
    pass

class ReportService:
    """
    Comprehensive service for managing reports, templates, and executions.
    Handles all report-related operations including CRUD, execution, and template management.
    """
    __depends_on__ = ['ReportTemplate','ReportQueryExecutor','QueryMetadataExtractor','Report', 
                      'ReportColumn', 'ReportVariable', 'ReportExecution',
                        'ReportSchedule',  'Connection', 'DataType', 
                        'VariableType', 'DatabaseType', 'Template' ]

    def __init__(self, session: Session, logger: Optional[logging.Logger] = None):
        
        self.session = session
        self.logger = logger or logging.getLogger(__name__)
        self.metadata_extractor = QueryMetadataExtractor(logger=self.logger)

    # =====================================================================
    # REPORT TEMPLATE OPERATIONS
    # =====================================================================

    def create_report_template(self, name: str, display_name: str,
                             template_id: UUID, description: Optional[str] = None,
                             show_filters: bool = True, filter_position: str = 'top',
                             show_export_buttons: bool = True, show_pagination: bool = True,
                             pagination_position: str = 'bottom', datatable_options: Optional[Dict] = None,
                             custom_css: Optional[str] = None, custom_js: Optional[str] = None) -> ReportTemplate:
        """Create a new report template"""
        self.logger.info(f"Creating report template: {name}")

        # Validate template exists
        template = self.session.query(Template).filter_by(id=template_id).first()
        if not template:
            raise ValueError(f"Template {template_id} not found")

        report_template = ReportTemplate(
            name=name,
            display_name=display_name,
            template_id=template_id,
            description=description,
            show_filters=show_filters,
            filter_position=filter_position,
            show_export_buttons=show_export_buttons,
            show_pagination=show_pagination,
            pagination_position=pagination_position,
            datatable_options=datatable_options or {},
            custom_css=custom_css,
            custom_js=custom_js
        )

        self.session.add(report_template)

        try:
            self.session.commit()
            self.logger.info(f"Report template created: {name} ({report_template.id})")
            return report_template
        except IntegrityError as e:
            self.session.rollback()
            self.logger.error(f"Failed to create report template {name}: {e}")
            raise ValueError(f"Report template with name '{name}' already exists")

    def get_report_template(self, template_id: Union[str, UUID]) -> Optional[ReportTemplate]:
        """Get report template by UUID or name"""
        if isinstance(template_id, str) and not self._is_valid_id(template_id):
            # Try by name
            return self.session.query(ReportTemplate).filter_by(name=template_id).first()
        return self.session.query(ReportTemplate).filter_by(id=template_id).first()

    def update_report_template(self, template_id: UUID, **kwargs) -> ReportTemplate:
        """Update report template"""
        report_template = self.get_report_template(template_id)
        if not report_template:
            raise ValueError(f"Report template {template_id} not found")

        self.logger.info(f"Updating report template: {report_template.name}")

        for key, value in kwargs.items():
            if hasattr(report_template, key):
                setattr(report_template, key, value)

        self.session.commit()
        self.logger.info(f"Report template updated: {report_template.name}")
        return report_template

    def delete_report_template(self, template_id: UUID, force: bool = False) -> bool:
        """Delete report template"""
        report_template = self.get_report_template(template_id)
        if not report_template:
            raise ValueError(f"Report template {template_id} not found")

        # Check for dependent reports
        report_count = self.session.query(Report).filter_by(report_template_id=template_id).count()
        if report_count > 0 and not force:
            raise ValueError(f"Cannot delete template with {report_count} dependent reports")

        self.logger.info(f"Deleting report template: {report_template.name}")

        try:
            self.session.delete(report_template)
            self.session.commit()
            self.logger.info(f"Report template deleted: {report_template.name}")
            return True
        except Exception as e:
            self.session.rollback()
            self.logger.error(f"Failed to delete report template: {e}")
            raise

    def list_report_templates(self) -> List[ReportTemplate]:
        """List all report templates"""
        return self.session.query(ReportTemplate).order_by(ReportTemplate.name).all()

    # =====================================================================
    # REPORT OPERATIONS
    # =====================================================================

    def create_report(self, slug: str, name: str, query: str, connection_id: UUID,
                     display: Optional[str] = None, description: Optional[str] = None,
                     category: Optional[str] = None, tags: Optional[List[str]] = None,
                     report_template_id: Optional[UUID] = None, is_model: bool = False, 
                     model_id: Optional[UUID] = None, **kwargs) -> Report:  # Add model_id parameter
        """Create a new report with validation"""
        self.logger.info(f"Creating report: {slug}")

        # Generate slug if needed
        if not slug:
            slug = Report.generate_slug(name, self.session)

        # Validate connection exists
        connection = self.session.query(Connection).filter_by(id=connection_id).first()
        if not connection:
            raise ValueError(f"Connection {connection_id} not found")

        # Validate report template if provided
        if report_template_id:
            report_template = self.get_report_template(report_template_id)
            if not report_template:
                raise ValueError(f"Report template {report_template_id} not found")

        # Validate model if provided
        if model_id:
            model = self.session.query(Model).filter_by(id=model_id).first()
            if not model:
                raise ValueError(f"Model {model_id} not found")

        report = Report(
            slug=slug,
            name=name,
            display=display,
            query=query,
            description=description,
            connection_id=connection_id,
            category=category,
            tags=tags or [],
            report_template_id=report_template_id,
            is_model=is_model,
            model_id=model_id,  # Add this
            **kwargs
        )

        self.session.add(report)

        try:
            self.session.commit()

            # Create permissions
            if not report.permissions_created:
                report.create_permissions(self.session)
                report.permissions_created = True
                self.session.commit()

            self.logger.info(f"Report created: {slug} ({report.id})")
            return report
        except IntegrityError as e:
            self.session.rollback()
            self.logger.error(f"Failed to create report {slug}: {e}")
            raise ValueError(f"Report with slug '{slug}' already exists")

    def get_model(self, model_id: Union[str, UUID]) -> Optional['Model']:
        """Get model by UUID or name"""
        try:
            if isinstance(model_id, str) and not self._is_valid_id(model_id):
                # Try by name
                return self.session.query(Model).filter_by(name=model_id).first()
            return self.session.query(Model).filter_by(id=model_id).first()
        except:
            # Model class might not be available
            return None
        

    def get_report(self, report_id: Union[str, UUID]) -> Optional[Report]:
        """Get report by UUID or slug"""
        if isinstance(report_id, str) and not self._is_valid_id(report_id):
            # Try by slug
            return self.session.query(Report).filter_by(slug=report_id).first()
        return self.session.query(Report).filter_by(id=report_id).first()

    def update_report(self, report_id: UUID, **kwargs) -> Report:
        """Update report with validation"""
        report = self.get_report(report_id)
        if not report:
            raise ValueError(f"Report {report_id} not found")

        self.logger.info(f"Updating report: {report.slug}")

        # Handle slug changes carefully
        if 'slug' in kwargs and kwargs['slug'] != report.slug:
            # Check if new slug exists
            existing = self.session.query(Report).filter_by(slug=kwargs['slug']).first()
            if existing:
                raise ValueError(f"Report with slug '{kwargs['slug']}' already exists")

        # Update fields
        for key, value in kwargs.items():
            if hasattr(report, key):
                setattr(report, key, value)

        # Update permissions if name changed
        if 'name' in kwargs or 'display' in kwargs:
            report.update_permission_descriptions(self.session)

        self.session.commit()
        self.logger.info(f"Report updated: {report.slug}")
        return report

    def delete_report(self, report_id: UUID) -> bool:
        """Delete report and related permissions"""
        report = self.get_report(report_id)
        if not report:
            raise ValueError(f"Report {report_id} not found")

        self.logger.info(f"Deleting report: {report.slug}")

        try:
            # Delete permissions first
            if report.permissions_created:
                report.delete_permissions(self.session)

            # Delete report (cascade will handle related records)
            self.session.delete(report)
            self.session.commit()

            self.logger.info(f"Report deleted: {report.slug}")
            return True
        except Exception as e:
            self.session.rollback()
            self.logger.error(f"Failed to delete report: {e}")
            raise

    def list_reports(self, category: Optional[str] = None,
                    connection_id: Optional[UUID] = None,
                    is_public: Optional[bool] = None,
                    user_id: Optional[UUID] = None) -> List[Report]:
        """List reports with optional filtering"""
        query = self.session.query(Report)

        if category:
            query = query.filter_by(category=category)
        if connection_id:
            query = query.filter_by(connection_id=connection_id)
        if is_public is not None:
            query = query.filter_by(is_public=is_public)

        reports = query.order_by(Report.category, Report.name).all()

        # Filter by user permissions if user_id provided
        if user_id:
            return Report.get_user_reports(self.session, user_id)

        return reports

    def duplicate_report(self, report_id: UUID, new_name: str,
                        new_slug: Optional[str] = None) -> Tuple[Report, str]:
        """Duplicate a report with all its columns and variables"""
        report = self.get_report(report_id)
        if not report:
            raise ValueError(f"Report {report_id} not found")

        return report.duplicate(self.session, new_name, new_slug)

    # =====================================================================
    # REPORT COLUMN OPERATIONS
    # =====================================================================

    def add_report_column(self, report_id: UUID, name: str, data_type_id: UUID,
                         display_name: Optional[str] = None, **kwargs) -> ReportColumn:
        """Add a column to a report"""
        report = self.get_report(report_id)
        if not report:
            raise ValueError(f"Report {report_id} not found")

        # Get next order index
        max_order = self.session.query(func.max(ReportColumn.order_index))\
                               .filter_by(report_id=report_id).scalar()
        order_index = (max_order or -1) + 1

        column = ReportColumn(
            report_id=report_id,
            name=name,
            display_name=display_name or name,
            data_type_id=data_type_id,
            order_index=order_index,
            **kwargs
        )

        self.session.add(column)
        self.session.commit()

        self.logger.info(f"Added column '{name}' to report {report.slug}")
        return column

    def update_report_column(self, column_id: UUID, **kwargs) -> ReportColumn:
        """Update a report column"""
        column = self.session.query(ReportColumn).filter_by(id=column_id).first()
        if not column:
            raise ValueError(f"Report column {column_id} not found")

        for key, value in kwargs.items():
            if hasattr(column, key):
                setattr(column, key, value)

        self.session.commit()
        return column

    def delete_report_column(self, column_id: UUID) -> bool:
        """Delete a report column"""
        column = self.session.query(ReportColumn).filter_by(id=column_id).first()
        if not column:
            raise ValueError(f"Report column {column_id} not found")

        self.session.delete(column)
        self.session.commit()
        return True

    def reorder_columns(self, report_id: UUID, column_order: List[UUID]) -> bool:
        """Reorder report columns"""
        for index, column_id in enumerate(column_order):
            self.session.query(ReportColumn)\
                       .filter_by(id=column_id, report_id=report_id)\
                       .update({'order_index': index})

        self.session.commit()
        return True

    # =====================================================================
    # REPORT VARIABLE OPERATIONS
    # =====================================================================

    def add_report_variable(self, report_id: UUID, name: str,
                           variable_type_id: UUID, 
                           display_name: Optional[str] = None, **kwargs) -> ReportVariable:
        """Add a variable to a report"""
        report = self.get_report(report_id)
        if not report:
            raise ValueError(f"Report {report_id} not found")

        # Get next order index
        max_order = self.session.query(func.max(ReportVariable.order_index))\
                               .filter_by(report_id=report_id).scalar()
        order_index = (max_order or -1) + 1

        variable = ReportVariable(
            report_id=report_id,
            name=name,
            display_name=display_name or name,
            variable_type_id=variable_type_id,
            order_index=order_index,
            **kwargs
        )

        self.session.add(variable)
        self.session.commit()

        self.logger.info(f"Added variable '{name}' to report {report.slug}")
        return variable

    def update_report_variable(self, variable_id: UUID, **kwargs) -> ReportVariable:
        """Update a report variable"""
        variable = self.session.query(ReportVariable).filter_by(id=variable_id).first()
        if not variable:
            raise ValueError(f"Report variable {variable_id} not found")

        for key, value in kwargs.items():
            if hasattr(variable, key):
                setattr(variable, key, value)

        self.session.commit()
        return variable

    def delete_report_variable(self, variable_id: UUID) -> bool:
        """Delete a report variable"""
        variable = self.session.query(ReportVariable).filter_by(id=variable_id).first()
        if not variable:
            raise ValueError(f"Report variable {variable_id} not found")

        self.session.delete(variable)
        self.session.commit()
        return True

    # =====================================================================
    # REPORT EXECUTION
    # =====================================================================

    def execute_report(self, report_id: UUID, request_data: Dict[str, Any],
                      user_id: Optional[UUID] = None) -> Dict[str, Any]:
        """Execute a report with parameters"""
        report = self.get_report(report_id)
        if not report:
            raise ValueError(f"Report {report_id} not found")

        self.logger.info(f"Executing report: {report.slug}")

        # Check permissions if user provided
        if user_id and not Report.check_permission(self.session, user_id, report.slug, 'execute'):
            raise PermissionError(f"User does not have permission to execute report {report.slug}")

        # Get database connection
        connection = report.connection
        db_type = connection.database_type.name.lower()
        connection_string = connection.get_connection_string()

        # Create executor for the database type
        executor = ReportQueryExecutor(db_type)

        # Track execution start
        start_time = datetime.utcnow()

        try:
            # Create database session for report
            from sqlalchemy import create_engine
            engine = create_engine(connection_string)

            with engine.connect() as db_connection:
                # Execute report
                result = executor.execute_report(db_connection, report, request_data)

            # Calculate execution time
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            # Record execution
            execution = ReportExecution(
                report_id=report_id,
                user_id=user_id,
                duration_ms=int(execution_time),
                row_count=result.get('recordsFiltered', 0),
                parameters_used=request_data.get('vars', {}),
                status='success'
            )
            self.session.add(execution)
            self.session.commit()

            self.logger.info(f"Report {report.slug} executed successfully in {execution_time}ms")
            return result

        except Exception as e:
            # Record failed execution
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            execution = ReportExecution(
                report_id=report_id,
                user_id=user_id,
                duration_ms=int(execution_time),
                parameters_used=request_data.get('vars', {}),
                status='error',
                error_message=str(e)
            )
            self.session.add(execution)
            self.session.commit()

            self.logger.error(f"Report {report.slug} execution failed: {e}")
            raise

    def test_report_query(self, report_id: UUID, params: Optional[Dict] = None) -> List[Dict]:
        """Test a report query and return column information"""
        report = self.get_report(report_id)
        if not report:
            raise ValueError(f"Report {report_id} not found")

        # Get database connection
        connection = report.connection
        db_type = connection.database_type.name.lower()
        connection_string = connection.get_connection_string()

        # Create executor
        executor = ReportQueryExecutor(db_type)

        try:
            from sqlalchemy import create_engine
            engine = create_engine(connection_string)

            with engine.connect() as db_connection:
                columns = executor.test_query(db_connection, report.query, params)

            return columns
        except Exception as e:
            self.logger.error(f"Failed to test report query: {e}")
            raise

    def get_report_execution_history(self, report_id: UUID,
                                   limit: int = 100) -> List[ReportExecution]:
        """Get execution history for a report"""
        return self.session.query(ReportExecution)\
                          .filter_by(report_id=report_id)\
                          .order_by(ReportExecution.executed_at.desc())\
                          .limit(limit)\
                          .all()

    # =====================================================================
    # REPORT PERMISSIONS
    # =====================================================================

    def assign_report_to_role(self, report_id: UUID, role_id: UUID,
                            actions: Optional[List[str]] = None) -> Tuple[bool, str]:
        """Assign report permissions to a role"""
        report = self.get_report(report_id)
        if not report:
            raise ValueError(f"Report {report_id} not found")

        return report.assign_to_role(self.session, role_id, actions)

    def remove_report_from_role(self, report_id: UUID, role_id: UUID,
                               actions: Optional[List[str]] = None) -> Tuple[bool, str]:
        """Remove report permissions from a role"""
        report = self.get_report(report_id)
        if not report:
            raise ValueError(f"Report {report_id} not found")

        return report.remove_from_role(self.session, role_id, actions)

    def get_report_roles(self, report_id: UUID, action: str = 'view') -> List[Any]:
        """Get all roles with access to a report"""
        report = self.get_report(report_id)
        if not report:
            raise ValueError(f"Report {report_id} not found")

        return report.get_roles_with_access(self.session, action)

    def check_user_permission(self, user_id: UUID, report_slug: str,
                            action: str = 'view') -> bool:
        """Check if user has permission for report action"""
        return Report.check_permission(self.session, user_id, report_slug, action)

    # =====================================================================
    # DATA TYPE AND VARIABLE TYPE OPERATIONS
    # =====================================================================

    def list_data_types(self) -> List[DataType]:
        """List all available data types"""
        return self.session.query(DataType)\
                          .filter_by(is_active=True)\
                          .order_by(DataType.display)\
                          .all()

    def list_variable_types(self) -> List[VariableType]:
        """List all available variable types"""
        return self.session.query(VariableType)\
                          .filter_by(is_active=True)\
                          .order_by(VariableType.display)\
                          .all()

    def list_database_types(self) -> List[DatabaseType]:
        """List all available database types"""
        return self.session.query(DatabaseType)\
                          .filter_by(is_active=True)\
                          .order_by(DatabaseType.display)\
                          .all()

    # =====================================================================
    # CONNECTION OPERATIONS
    # =====================================================================

    def list_connections(self) -> List[Connection]:
        """List all database connections"""
        return self.session.query(Connection)\
                          .order_by(Connection.name)\
                          .all()

    def test_connection(self, connection_id: UUID) -> Tuple[bool, str]:
        """Test a database connection"""
        connection = self.session.query(Connection).filter_by(id=connection_id).first()
        if not connection:
            raise ValueError(f"Connection {connection_id} not found")

        try:
            from sqlalchemy import create_engine
            connection_string = connection.get_connection_string()
            engine = create_engine(connection_string)

            with engine.connect() as conn:
                # Simple test query based on database type
                if connection.database_type.name.lower() == 'postgresql':
                    conn.execute(text("SELECT 1"))
                elif connection.database_type.name.lower() == 'mysql':
                    conn.execute(text("SELECT 1"))
                elif connection.database_type.name.lower() == 'mssql':
                    conn.execute(text("SELECT 1"))
                elif connection.database_type.name.lower() == 'sqlite':
                    conn.execute(text("SELECT 1"))
                else:
                    conn.execute(text("SELECT 1"))

            return True, "Connection successful"
        except Exception as e:
            return False, str(e)

    # =====================================================================
    # UTILITY METHODS
    # =====================================================================

    def _is_valid_id(self, value: str) -> bool:
        """Check if string is a valid UUID"""
        try:
            UUID(value)
            return True
        except ValueError:
            return False

    def get_report_structure(self, report_id: UUID) -> Dict[str, Any]:
        """Get complete report structure including columns and variables"""
        report = self.get_report(report_id)
        if not report:
            raise ValueError(f"Report {report_id} not found")

        return {
            'report': report,
            'columns': report.columns,
            'variables': report.variables,
            'connection': report.connection,
            'template': report.report_template,
            'column_count': len(report.columns),
            'variable_count': len(report.variables),
            'last_execution': self.session.query(ReportExecution)\
                                         .filter_by(report_id=report_id)\
                                         .order_by(ReportExecution.executed_at.desc())\
                                         .first()
        }

    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get dashboard statistics for reports"""
        total_reports = self.session.query(Report).count()
        public_reports = self.session.query(Report).filter_by(is_public=True).count()

        # Execution stats
        total_executions = self.session.query(ReportExecution).count()
        successful_executions = self.session.query(ReportExecution)\
                                           .filter_by(status='success').count()

        # Recent executions
        recent_executions = self.session.query(ReportExecution)\
                                      .order_by(ReportExecution.executed_at.desc())\
                                      .limit(10)\
                                      .all()

        # Reports by category
        categories = self.session.query(
            Report.category,
            func.count(Report.id)
        ).group_by(Report.category).all()

        # Connection usage
        connection_usage = self.session.query(
            Connection.name,
            func.count(Report.id)
        ).join(Report).group_by(Connection.name).all()

        return {
            'reports': {
                'total': total_reports,
                'public': public_reports,
                'private': total_reports - public_reports
            },
            'executions': {
                'total': total_executions,
                'successful': successful_executions,
                'failed': total_executions - successful_executions,
                'success_rate': (successful_executions / total_executions * 100) if total_executions > 0 else 0
            },
            'recent_executions': recent_executions,
            'categories': dict(categories),
            'connections': dict(connection_usage),
            'templates': self.session.query(ReportTemplate).count()
        }

    def export_report_definition(self, report_id: UUID) -> Dict[str, Any]:
        """Export report definition as JSON"""
        report = self.get_report(report_id)
        if not report:
            raise ValueError(f"Report {report_id} not found")

        return {
            'report': {
                'connection_id': report.connection_id,
                'model_id': report.model_id,  # Add this
                'slug': report.slug,
                'name': report.name,
                'display': report.display,
                'query': report.query,
                'description': report.description,
                'category': report.category,
                'tags': report.tags,
                'options': report.options,
                'flags': {
                    'is_wide': report.is_wide,
                    'is_ajax': report.is_ajax,
                    'is_auto_run': report.is_auto_run,
                    'is_searchable': report.is_searchable,
                    'is_public': report.is_public,
                    'is_download_csv': report.is_download_csv,
                    'is_download_xlsx': report.is_download_xlsx,
                    'is_published': report.is_published,
                    'is_model': report.is_model  # Add this
                }
            },
            'columns': [
                {
                    'name': col.name,
                    'display_name': col.display_name,
                    'data_type': col.data_type.name,
                    'is_searchable': col.is_searchable,
                    'search_type': col.search_type,
                    'is_visible': col.is_visible,
                    'is_sortable': col.is_sortable,
                    'format_string': col.format_string,
                    'width': col.width,
                    'alignment': col.alignment,
                    'options': col.options,
                    'order_index': col.order_index
                } for col in report.columns
            ],
            'variables': [
                {
                    'name': var.name,
                    'display_name': var.display_name,
                    'variable_type': var.variable_type.name,
                    'default_value': var.default_value,
                    'placeholder': var.placeholder,
                    'help_text': var.help_text,
                    'is_required': var.is_required,
                    'is_hidden': var.is_hidden,
                    'limits': var.limits,
                    'order_index': var.order_index
                } for var in report.variables
            ]
        }

    def import_report_definition(self, definition: Dict[str, Any],
                               connection_id: UUID) -> Report:
        """Import report from JSON definition"""
        report_data = definition['report']

        # Create report
        report = self.create_report(
            slug=report_data['slug'],
            name=report_data['name'],
            display=report_data.get('display'),
            query=report_data['query'],
            description=report_data.get('description'),
            connection_id=connection_id,
            category=report_data.get('category'),
            tags=report_data.get('tags'),
            **report_data.get('flags', {})
        )

        # Get data type and variable type lookups
        data_types = {dt.name: dt.id for dt in self.list_data_types()}
        variable_types = {vt.name: vt.id for vt in self.list_variable_types()}

        # Add columns
        for col_data in definition.get('columns', []):
            self.add_report_column(
                report_id=report.id,
                name=col_data['name'],
                display_name=col_data.get('display_name'),
                data_type_id=data_types[col_data['data_type']],
                is_searchable=col_data.get('is_searchable', True),
                search_type=col_data.get('search_type', 'contains'),
                is_visible=col_data.get('is_visible', True),
                is_sortable=col_data.get('is_sortable', True),
                format_string=col_data.get('format_string'),
                width=col_data.get('width'),
                alignment=col_data.get('alignment', 'left'),
                options=col_data.get('options', {}),
                order_index=col_data.get('order_index', 0)
            )

        # Add variables
        for var_data in definition.get('variables', []):
            self.add_report_variable(
                report_id=report.id,
                name=var_data['name'],
                display_name=var_data.get('display_name'),
                variable_type_id=variable_types[var_data['variable_type']],
                default_value=var_data.get('default_value'),
                placeholder=var_data.get('placeholder'),
                help_text=var_data.get('help_text'),
                is_required=var_data.get('is_required', False),
                is_hidden=var_data.get('is_hidden', False),
                limits=var_data.get('limits', {}),
                order_index=var_data.get('order_index', 0)
            )

        return report
    
    def get_query_metadata(self, query: str, connection_id: UUID, 
                          params: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        Extract column metadata from a SQL query without fetching data.
        
        Args:
            query: SQL query to analyze
            connection_id: UUID of the database connection
            params: Optional query parameters
            
        Returns:
            List of column metadata dictionaries
        """
        # Get connection details
        connection = self.session.query(Connection).filter_by(id=connection_id).first()
        if not connection:
            raise ValueError(f"Connection {connection_id} not found")
        
        db_type = connection.database_type.name.lower()
        connection_string = connection.get_connection_string()
        
        # Use metadata extractor
        try:
            return self.metadata_extractor.extract_metadata(
                query=query,
                connection_string=connection_string,
                db_type=db_type,
                params=params
            )
        except QueryMetadataError as e:
            self.logger.error(f"Metadata extraction failed: {e}")
            raise

    def analyze_report_columns(self, report_id: UUID, 
                             auto_update: bool = False,
                             dry_run: bool = False) -> Dict[str, Any]:
        """
        Analyze a report's query and compare with existing column definitions.
        
        Args:
            report_id: UUID of the report to analyze
            auto_update: Whether to automatically update column definitions
            dry_run: If True, show what would be updated without making changes
            
        Returns:
            Analysis results including new columns, missing columns, and type changes
        """
        report = self.get_report(report_id)
        if not report:
            raise ValueError(f"Report {report_id} not found")
        
        self.logger.info(f"Analyzing columns for report: {report.slug}")
        
        # Check query compatibility
        db_type = report.connection.database_type.name.lower()
        compatibility = self.metadata_extractor.analyze_query_compatibility(
            report.query, 
            db_type
        )
        
        if not compatibility['is_select']:
            raise ValueError("Report query must be a SELECT statement for column analysis")
        
        # Get query metadata
        try:
            metadata_columns = self.get_query_metadata(
                report.query, 
                report.connection_id,
                params={}  # Use empty params for analysis
            )
        except QueryMetadataError as e:
            return {
                'error': str(e),
                'compatibility': compatibility,
                'analysis_failed': True
            }
        
        # Get existing columns
        existing_columns = {col.name: col for col in report.columns}
        
        # Analyze differences
        analysis = {
            'compatibility': compatibility,
            'query_columns': metadata_columns,
            'existing_columns': list(existing_columns.keys()),
            'new_columns': [],
            'missing_columns': [],
            'type_changes': [],
            'changes_made': []
        }
        
        # Find new columns in query
        for meta_col in metadata_columns:
            col_name = meta_col['name']
            if col_name not in existing_columns:
                analysis['new_columns'].append({
                    'name': col_name,
                    'suggested_type': meta_col.get('suggested_type', 'string'),
                    'sql_type': meta_col.get('sql_type'),
                    'nullable': meta_col.get('nullable')
                })
        
        # Find missing columns (in DB but not in query)
        query_col_names = {col['name'] for col in metadata_columns}
        for existing_name in existing_columns.keys():
            if existing_name not in query_col_names:
                analysis['missing_columns'].append(existing_name)
        
        # Check for type changes
        data_types = {dt.name: dt for dt in self.list_data_types()}
        
        for meta_col in metadata_columns:
            col_name = meta_col['name']
            if col_name in existing_columns:
                existing_col = existing_columns[col_name]
                suggested_type = meta_col.get('suggested_type', 'string')
                
                if existing_col.data_type.name != suggested_type:
                    analysis['type_changes'].append({
                        'name': col_name,
                        'current_type': existing_col.data_type.name,
                        'suggested_type': suggested_type,
                        'sql_type': meta_col.get('sql_type')
                    })
        
        # Auto-update if requested and not dry run
        if auto_update and not dry_run and (analysis['new_columns'] or analysis['type_changes']):
            self.logger.info(f"Auto-updating columns for report {report.slug}")
            
            # Add new columns
            for new_col in analysis['new_columns']:
                data_type = data_types.get(new_col['suggested_type'])
                if data_type:
                    try:
                        col = self.add_report_column(
                            report_id=report.id,
                            name=new_col['name'],
                            data_type_id=data_type.id,
                            display_name=new_col['name'].replace('_', ' ').title()
                        )
                        analysis['changes_made'].append(f"Added column: {new_col['name']}")
                    except Exception as e:
                        self.logger.error(f"Failed to add column {new_col['name']}: {e}")
            
            # Update type changes
            for type_change in analysis['type_changes']:
                col_name = type_change['name']
                existing_col = existing_columns[col_name]
                data_type = data_types.get(type_change['suggested_type'])
                
                if data_type:
                    try:
                        self.update_report_column(
                            existing_col.id,
                            data_type_id=data_type.id
                        )
                        analysis['changes_made'].append(
                            f"Updated {col_name} type: {type_change['current_type']} → {type_change['suggested_type']}"
                        )
                    except Exception as e:
                        self.logger.error(f"Failed to update column {col_name}: {e}")
        
        analysis['dry_run'] = dry_run
        analysis['auto_update_enabled'] = auto_update
        
        return analysis

    def sync_report_columns_from_query(self, report_id: UUID,
                                      remove_missing: bool = False) -> Dict[str, Any]:
        """
        Synchronize report columns with query metadata.
        More aggressive than analyze_report_columns - will reorder and optionally remove columns.
        
        Args:
            report_id: UUID of the report
            remove_missing: Whether to remove columns not in query
            
        Returns:
            Sync results
        """
        report = self.get_report(report_id)
        if not report:
            raise ValueError(f"Report {report_id} not found")
        
        self.logger.info(f"Synchronizing columns for report: {report.slug}")
        
        # Get query metadata
        metadata_columns = self.get_query_metadata(
            report.query,
            report.connection_id
        )
        
        # Get data types lookup
        data_types = {dt.name: dt for dt in self.list_data_types()}
        
        results = {
            'added': [],
            'updated': [],
            'removed': [],
            'reordered': False
        }
        
        # Create name to metadata mapping
        meta_by_name = {col['name']: col for col in metadata_columns}
        existing_by_name = {col.name: col for col in report.columns}
        
        # Add/update columns based on query order
        for index, meta_col in enumerate(metadata_columns):
            col_name = meta_col['name']
            suggested_type = meta_col.get('suggested_type', 'string')
            data_type = data_types.get(suggested_type)
            
            if not data_type:
                self.logger.warning(f"Unknown data type: {suggested_type}, using string")
                data_type = data_types.get('string')
            
            if col_name in existing_by_name:
                # Update existing column
                existing_col = existing_by_name[col_name]
                updates = {}
                
                # Check type change
                if existing_col.data_type_id != data_type.id:
                    updates['data_type_id'] = data_type.id
                
                # Check order change
                if existing_col.order_index != index:
                    updates['order_index'] = index
                    results['reordered'] = True
                
                if updates:
                    self.update_report_column(existing_col.id, **updates)
                    results['updated'].append({
                        'name': col_name,
                        'changes': list(updates.keys())
                    })
            else:
                # Add new column
                col = self.add_report_column(
                    report_id=report.id,
                    name=col_name,
                    data_type_id=data_type.id,
                    display_name=col_name.replace('_', ' ').title(),
                    order_index=index
                )
                results['added'].append(col_name)
        
        # Remove missing columns if requested
        if remove_missing:
            query_col_names = {col['name'] for col in metadata_columns}
            for existing_col in report.columns:
                if existing_col.name not in query_col_names:
                    self.delete_report_column(existing_col.id)
                    results['removed'].append(existing_col.name)
        
        return results