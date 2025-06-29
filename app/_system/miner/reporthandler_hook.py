import functools
from typing import Optional, List
from flask import g, session, request, current_app

__depends_on__=['Miner']
def register_report_handler(app):
    """Report Data API"""
    try:
        from app.classes import ReportDataHandler
        with app.app_context():
            app.extensions['Miner'].register_data_handler("ReportHandler", ReportDataHandler)
        app.logger.info("ReportHandler api initialized")
    except ImportError as i:
        print(i)
        app.logger.info("ReportHandler api not available")
