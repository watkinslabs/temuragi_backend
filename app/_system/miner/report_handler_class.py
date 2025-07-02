from sqlalchemy import or_, create_engine


from .handler_class import  (
        MinerError,
        MinerPermissionError,
        DataBrokerError,
        BaseDataHandler
        )

from app.models import Report, ReportQueryExecutor
from app.register.database import db_registry

class ReportDataHandler(BaseDataHandler):
    """Handler for Report models that executes SQL queries"""
    __depends_on__ = ['Miner', 'Report', 'ReportQueryExecutor']
    
    def handle_list(self, data):
        """Execute report with DataTables parameters"""
        # Get report1
        report_id = data.get('report_id')
        if not report_id:
            raise MinerError('report_id is required', 'ValidationError', 400)

        db_session=db_registry._routing_session()
        report = db_session.query(Report).filter(
                or_(Report.id == report_id, Report.slug == report_id)
            ).first()
        
        if not report:
            raise MinerError(f'Report {report_id} not found', 'NotFoundError', 404)
        
        if report.is_model:
            raise MinerError(f'Report {report_id} is not available as a data model', 'ValidationError', 400)
        
        # Use ReportQueryExecutor
        executor = ReportQueryExecutor(report.connection.database_type.name.lower())
        
        from app.models import Connection

        ##SQL ACHMEY DB MODEL CONECTION 
        # The data from Miner already has DataTables format
        # Just pass it through to the executor
        result = executor.execute_report(
            report, 
            data  # Pass the whole data dict
        )
        
        return result
    
    def handle_metadata(self, data):
        """Return report metadata in Miner format"""
        report_id = data.get('report_id')
        report = self._get_report(report_id)
        
        # Convert report columns to Miner metadata format
        return {
            'model_name': f'Report_{report.slug}',
            'columns': [self._convert_column_metadata(col) for col in report.columns],
            'variables': [self._convert_variable_metadata(var) for var in report.variables]
        }