import logging
from typing import Dict, List, Any, Optional
from datetime import datetime


try:
    from app._system.miner.miner_class import BaseDataHandler, MinerError
    from .po_service import PurchaseOrderService, PurchaseOrderError
    from .po_error_class import POErrorCode
except: 
    pass

logger = logging.getLogger(__name__)

from app.register.database import db_registry

class PurchaseOrderHandler(BaseDataHandler):
    """
    Data handler for Purchase Order operations
    Thin API layer that bridges between Miner API and PurchaseOrderService
    """
    __depends_on__=['BaseDataHandler']

    def __init__(self, auth_context, logger=None):
        super().__init__(auth_context, logger)
        self.po_service = PurchaseOrderService()
        
    def handle_create(self, data):
        """
        Create a new purchase order
        
        Expected data format:
        {
            'company': 'PACIFIC' or 'CANADA',
            'from': 'vendor_code',
            'to': 'destination_warehouse',
            'vendid': 'vendor_id',
            'line_items': {
                'part_number': {
                    'description': 'desc',
                    'ord_qty': 10,
                    'rec_qty': 0,
                    'price': 100.00,
                    'extended': 1000.00
                }
            },
            'billinfo': {...},
            'shipinfo': {...},
            'freight': 50.00,
            'erd': '2025-01-15',
            'notes': ['note1', 'note2'],
            'warr_items': {...}
        }
        """
        try:
            # Add user from auth context
            data['user'] = self.auth_context.get('username', 'system')
            
            # Convert date strings to datetime objects if needed
            if 'erd' in data and isinstance(data['erd'], str):
                data['erd'] = datetime.strptime(data['erd'], '%Y-%m-%d').date()
            
            # Call PO service
            result = self.po_service.create_purchase_order(data)
            
            if result['success']:
                return {
                    'success': True,
                    'id': result['po_number'],
                    'po_number': result['po_number'],
                    'company': result['company'],
                    'total': result['total'],
                    'warnings': result.get('warnings', [])
                }
            else:
                self._raise_miner_error(result)
                
        except PurchaseOrderError as e:
            raise MinerError(
                message=str(e),
                error_type="PurchaseOrderError",
                status_code=400,
                details={'po_error_code': e.code.name}
            )
        except Exception as e:
            logger.exception("Unexpected error in PO create")
            raise MinerError(
                message=f"Failed to create purchase order: {str(e)}",
                error_type="SystemError",
                status_code=500
            )
    
    def handle_update(self, data):
        """
        Update an existing purchase order
        
        Expected data format:
        {
            'id': po_number,
            'company': 'PACIFIC' or 'CANADA',
            'line_items': {...},
            'billinfo': {...},
            'shipinfo': {...},
            'freight': 50.00,
            'erd': '2025-01-15',
            'notes': [...],
            'warr_items': {...}
        }
        """
        try:
            po_number = data.get('id')
            if not po_number:
                raise MinerError("PO number required for update", "ValidationError", 400)
            
            # Add user from auth context
            data['user'] = self.auth_context.get('username', 'system')
            
            # Convert date strings
            if 'erd' in data and isinstance(data['erd'], str):
                data['erd'] = datetime.strptime(data['erd'], '%Y-%m-%d').date()
            
            # Call PO service
            result = self.po_service.edit_purchase_order(po_number, data)
            
            if result['success']:
                return {
                    'success': True,
                    'id': po_number,
                    'po_number': po_number,
                    'total': result.get('total')
                }
            else:
                self._raise_miner_error(result)
                
        except PurchaseOrderError as e:
            raise MinerError(
                message=str(e),
                error_type="PurchaseOrderError",
                status_code=400,
                details={'po_error_code': e.code.name}
            )
            
    def handle_delete(self, data):
        """
        Delete a purchase order
        
        Expected data format:
        {
            'id': po_number,
            'company': 'PACIFIC' or 'CANADA'
        }
        """
        try:
            po_number = data.get('id')
            if not po_number:
                raise MinerError("PO number required for delete", "ValidationError", 400)
            
            company = data.get('company')
            if not company:
                raise MinerError("Company is required (PACIFIC or CANADA)", "ValidationError", 400)
            
            user = self.auth_context.get('username', 'system')
            
            # Call PO service
            result = self.po_service.delete_purchase_order(po_number, user, company)
            
            if result['success']:
                return {
                    'success': True,
                    'message': result.get('message', f'PO {po_number} deleted successfully')
                }
            else:
                self._raise_miner_error(result)
                
        except PurchaseOrderError as e:
            raise MinerError(
                message=str(e),
                error_type="PurchaseOrderError",
                status_code=400,
                details={'po_error_code': e.code.name}
            )
    
    def handle_process(self, data):
        """
        Handle custom PO operations
        
        Expected data format:
        {
            'operation': 'mark_as_printed' | 'validate' | 'get_po_details' | 'get_historical_po' | 'validate_items',
            'id': po_number,  # for operations that need it
            'company': 'PACIFIC' or 'CANADA',  # for operations that need it
            ... other operation-specific data ...
        }
        """
        data = data.get('data')
        
        operation = data.get('operation')
        if not operation:
            raise MinerError("Operation type required for process", "ValidationError", 400)
        
        try:
            if operation == 'mark_as_printed':
                return self._handle_mark_as_printed(data)
            elif operation == 'validate':
                return self._handle_validate_po_data(data)
            elif operation == 'validate_items':
                return self._handle_validate_items(data)
            elif operation == 'get_po_details':
                return self._handle_get_po_details(data)
            elif operation == 'get_historical_po':
                return self._handle_get_historical_po(data)
            else:
                raise MinerError(
                    f"Unknown operation: {operation}",
                    "ValidationError",
                    400
                )
                
        except PurchaseOrderError as e:
            raise MinerError(
                message=str(e),
                error_type="PurchaseOrderError",
                status_code=400,
                details={'po_error_code': e.code.name}
            )
    
    def handle_metadata(self, data):
        """
        Return PO-specific metadata for forms and validation
        """
        return {
            'success': True,
            'metadata': {
                'operations': [
                    'create', 'update', 'delete', 'mark_as_printed', 
                    'validate', 'validate_items', 'get_po_details', 'get_historical_po'
                ],
                'required_fields': {
                    'create': ['company', 'from', 'to', 'vendid', 'line_items', 'billinfo', 'shipinfo'],
                    'update': ['id', 'company', 'line_items'],
                    'delete': ['id', 'company'],
                    'mark_as_printed': ['id', 'company'],
                    'validate': ['company', 'from', 'to', 'line_items'],
                    'validate_items': ['company', 'location', 'line_items'],
                    'get_po_details': ['id', 'company'],
                    'get_historical_po': ['id', 'company']
                },
                'field_formats': {
                    'company': 'PACIFIC or CANADA',
                    'erd': 'YYYY-MM-DD',
                    'freight': 'decimal',
                    'line_items': {
                        'part_number': {
                            'ord_qty': 'integer',
                            'rec_qty': 'integer',
                            'price': 'decimal',
                            'extended': 'decimal'
                        }
                    }
                }
            }
        }
    
    def handle_validate(self, data):
        """
        Validate PO data structure without saving
        Delegates to service for actual validation
        """
        try:
            result = self.po_service.validate_po_data(data)
            return result
            
        except Exception as e:
            logger.exception("Error validating PO data")
            return {
                'success': False,
                'valid': False,
                'errors': [str(e)]
            }
    
    def handle_batch_create(self, data_list):
        """
        Create multiple POs in batch
        """
        results = []
        for idx, po_data in enumerate(data_list):
            try:
                result = self.handle_create(po_data)
                results.append({
                    'index': idx,
                    'success': True,
                    'po_number': result['po_number']
                })
            except Exception as e:
                results.append({
                    'index': idx,
                    'success': False,
                    'error': str(e)
                })
        
        return {
            'success': True,
            'results': results,
            'total': len(data_list),
            'successful': sum(1 for r in results if r['success'])
        }
    
    # Private helper methods
    
    def _handle_mark_as_printed(self, data):
        """Mark PO as printed"""
        po_number = data.get('id')
        if not po_number:
            raise MinerError("PO number required", "ValidationError", 400)
        
        company = data.get('company')
        if not company:
            raise MinerError("Company is required (PACIFIC or CANADA)", "ValidationError", 400)
        
        result = self.po_service.mark_as_printed(po_number, company)
        
        if result['success']:
            return result
        else:
            self._raise_miner_error(result)
    
    def _handle_validate_po_data(self, data):
        """Validate PO data structure"""
        result = self.po_service.validate_po_data(data)
        return result
    
    def _handle_validate_items(self, data):
        """Validate PO items against location"""
        location = data.get('location')
        line_items = data.get('line_items', {})
        company = data.get('company')
        
        if not location:
            raise MinerError("Location required for validation", "ValidationError", 400)
        if not company:
            raise MinerError("Company required for validation", "ValidationError", 400)
        if not line_items:
            raise MinerError("Line items required for validation", "ValidationError", 400)
        
        # Call service method
        result = self.po_service.validate_po_items(company, location, line_items)
        
        if result['success']:
            return result
        else:
            self._raise_miner_error(result)
    
    def _handle_get_po_details(self, data):
        """Get detailed PO information"""
        po_number = data.get('id')
        if not po_number:
            raise MinerError("PO number required", "ValidationError", 400)
        
        company = data.get('company')
        if not company:
            raise MinerError("Company is required (PACIFIC or CANADA)", "ValidationError", 400)
        
        # Call service method
        result = self.po_service.get_po_details(company, po_number)
        
        if result['success']:
            return result
        else:
            self._raise_miner_error(result)
    
    def _handle_get_historical_po(self, data):
        """Get historical PO"""
        po_number = data.get('id')
        if not po_number:
            raise MinerError("PO number required", "ValidationError", 400)
        
        company = data.get('company')
        if not company:
            raise MinerError("Company is required (PACIFIC or CANADA)", "ValidationError", 400)
        
        # Call the service - get_historical_po is an alias for get_po with check_historical=True
        result = self.po_service.get_historical_po(company, po_number)
        
        if result['success']:
            # If the result is raw data, format it
            if 'header' in result and not 'formatted' in result:
                # Use get_po_details for formatted output
                return self.po_service.get_po_details(company, po_number)
            return result
        else:
            self._raise_miner_error(result)
    
    def _raise_miner_error(self, result):
        """Convert PO service result to MinerError"""
        error_code = result.get('error_code')
        error_message = result.get('error_message', 'Purchase order operation failed')
        
        status_code = 400  # Default to bad request
        
        # Map specific error codes to HTTP status codes
        if error_code:
            if error_code == POErrorCode.INVALID_PO_NUMBER:
                status_code = 404
            elif error_code == POErrorCode.LOCATION_LOCKED:
                status_code = 409  # Conflict
            elif error_code in [POErrorCode.MSSQL_OPEN_FAILED, POErrorCode.MSSQL_QUERY_FAILED]:
                status_code = 500
        
        raise MinerError(
            message=error_message,
            error_type="PurchaseOrderError",
            status_code=status_code,
            details={
                'po_error_code': error_code.name if error_code else None,
                'errors': result.get('errors', [])
            }
        )