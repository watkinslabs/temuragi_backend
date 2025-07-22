# app/_system/miner/parked_order_handler_class.py

from sqlalchemy import or_, and_, String
from typing import Dict, List, Optional, Any

from app._system.miner.miner_class import BaseDataHandler, MinerError
from app.register.database import db_registry

# Import the service from the correct location
from .parked_order_service import (
    ParkedOrderService,
    ParkedOrderError,
    ParkedOrderErrorCode
)


class ParkedOrderHandler(BaseDataHandler):
    """Handler for Parked Orders data access via Miner API"""
    __depends_on__ = ['Miner', 'ParkedOrderService']

    def __init__(self, auth_context, logger=None):
        super().__init__(auth_context, logger)
        self.company_database = self._get_company_database()
    
    def _get_company_database(self) -> str:
        """Determine company database from auth context"""
        # Get company from auth context or default to GPACIFIC
        company = self.auth_context.get('company', 'GPACIFIC') if self.auth_context else 'GPACIFIC'
        
        # Map company codes to database names if needed
        company_map = {
            'US': 'GPACIFIC',
            'CA': 'GCANADA',
            'GPACIFIC': 'GPACIFIC',
            'GCANADA': 'GCANADA',
            'PACIFIC': 'GPACIFIC',
            'CANADA': 'GCANADA'
        }
        
        return company_map.get(company.upper(), 'GPACIFIC')
    
    def handle_list(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        List parked orders with filtering and pagination
        
        Expected data format:
        {
            "draw": 1,
            "start": 0,
            "length": 10,
            "search": {"value": ""},
            "order": [{"column": 0, "dir": "asc"}],
            "filters": {
                "status": "OPEN",  # OPEN, PARTIAL, COMPLETE
                "customer_code": 12345,
                "date_from": "2025-01-01",
                "date_to": "2025-01-31"
            }
        }
        """
        try:
            db_session = db_registry._routing_session()
            
            # Import models here to avoid circular imports
            from app.models import PartsTrader_dbo_parked_orders
            
            # Base query
            query = db_session.query(PartsTrader_dbo_parked_orders)
            
            # Apply filters
            filters = data.get('filters', {})
            
            if filters.get('status'):
                query = query.filter(PartsTrader_dbo_parked_orders.status == filters['status'])
            
            if filters.get('customer_code'):
                query = query.filter(PartsTrader_dbo_parked_orders.customer_code == filters['customer_code'])
            
            if filters.get('date_from'):
                query = query.filter(PartsTrader_dbo_parked_orders.created_at >= filters['date_from'])
            
            if filters.get('date_to'):
                query = query.filter(PartsTrader_dbo_parked_orders.created_at <= filters['date_to'])
            
            # Search functionality
            search_value = data.get('search', {}).get('value', '')
            if search_value:
                query = query.filter(
                    or_(
                        PartsTrader_dbo_parked_orders.pt_order_id.contains(search_value),
                        PartsTrader_dbo_parked_orders.pr_repair_order_id.cast(String).contains(search_value)
                    )
                )
            
            # Get total count before pagination
            total_records = query.count()
            
            # Apply ordering - MSSQL requires ORDER BY for OFFSET/LIMIT
            order_data = data.get('order', [])
            
            # Dynamic column mapping based on column names
            column_map = {
                'pr_repair_order_id': PartsTrader_dbo_parked_orders.pr_repair_order_id,
                'pt_order_id': PartsTrader_dbo_parked_orders.pt_order_id,
                'customer_code': PartsTrader_dbo_parked_orders.customer_code,
                'status': PartsTrader_dbo_parked_orders.status,
                'created_at': PartsTrader_dbo_parked_orders.created_at,
                'total': PartsTrader_dbo_parked_orders.total,
                'repairer_id': PartsTrader_dbo_parked_orders.repairer_id,
                'lines': PartsTrader_dbo_parked_orders.lines,
                'part_count': PartsTrader_dbo_parked_orders.part_count
            }
            
            # Determine order column and direction
            order_column = None
            direction = 'asc'
            
            if order_data and isinstance(order_data, list) and len(order_data) > 0:
                order_info = order_data[0]
                
                # Handle both column index and column name
                if 'column' in order_info:
                    column_ref = order_info['column']
                    
                    # If it's a string (column name), use it directly
                    if isinstance(column_ref, str) and column_ref in column_map:
                        order_column = column_map[column_ref]
                    # If it's an integer (index) and columns are provided
                    elif isinstance(column_ref, int) and 'columns' in data:
                        columns_list = data.get('columns', [])
                        if 0 <= column_ref < len(columns_list):
                            column_name = columns_list[column_ref].get('data') or columns_list[column_ref].get('name')
                            if column_name in column_map:
                                order_column = column_map[column_name]
                
                direction = order_info.get('dir', 'asc')
            
            # Default to created_at DESC if no valid order column found
            if order_column is None:
                order_column = PartsTrader_dbo_parked_orders.created_at
                direction = 'desc'
            
            # Apply ordering
            if direction == 'desc':
                query = query.order_by(order_column.desc())
            else:
                query = query.order_by(order_column)
            
            # Apply pagination
            start = data.get('start', 0)
            length = data.get('length', 10)
            
            if length > 0:
                query = query.offset(start).limit(length)
            
            # Execute query
            orders = query.all()
            
            # Format results
            results = []
            for order in orders:
                results.append({
                    'pr_repair_order_id': order.pr_repair_order_id,
                    'pt_order_id': order.pt_order_id,
                    'customer_code': order.customer_code,
                    'repairer_id': order.repairer_id,
                    'status': order.status if order.status else 'UNKNOWN',
                    'lines': order.lines if order.lines else 0,
                    'part_count': order.part_count if order.part_count else 0,
                    'total': float(order.total) if order.total else None,
                    'created_at': order.created_at.isoformat() if order.created_at else None
                })
            
            return {
                'draw': data.get('draw', 1),
                'recordsTotal': total_records,
                'recordsFiltered': total_records,
                'data': results
            }
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error listing parked orders: {e}")
            raise MinerError(f"Failed to list parked orders: {str(e)}", "DatabaseError", 500)
        finally:
            if 'db_session' in locals():
                db_session.close()
    
    def handle_get(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get complete parked order details
        
        Expected data format:
        {
            "pr_repair_order_id": 12345
        }
        """
        db_session = None
        try:
            # Validate required fields
            pr_repair_order_id = data.get('pr_repair_order_id')

            if not pr_repair_order_id:
                raise MinerError(
                    'pr_repair_order_id is required',
                    'ValidationError',
                    400
                )
            
            # Get database session
            db_session = db_registry._routing_session()
            
            # Create service instance
            service = ParkedOrderService(db_session, self.company_database)
            
            # Get order details - now only needs pr_repair_order_id
            result = service.get_parked_order_details(pr_repair_order_id)
            
            if not result:
                raise MinerError(
                    f'Parked order not found: RO={pr_repair_order_id}',
                    'NotFoundError',
                    404
                )
            
            return result
            
        except ParkedOrderError as e:
            # Convert service errors to Miner errors
            status_code_map = {
                ParkedOrderErrorCode.ORDER_NOT_FOUND: 404,
                ParkedOrderErrorCode.INVALID_COMPANY: 400,
                ParkedOrderErrorCode.DATABASE_ERROR: 500,
                ParkedOrderErrorCode.VALIDATE_ORDER_FAILED: 400,
                ParkedOrderErrorCode.MODEL_NOT_FOUND: 500
            }
            
            raise MinerError(
                e.message,
                e.error_code.value,
                status_code_map.get(e.error_code, 400),
                {'additional_info': e.additional_info}
            )
        except MinerError:
            raise
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error getting parked order details: {e}")
            raise MinerError(f"Failed to get parked order: {str(e)}", "DatabaseError", 500)
        finally:
            if db_session:
                db_session.close()
    
    def handle_metadata(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Return parked orders metadata in Miner format"""
        return {
            'model_name': 'ParkedOrders',
            'operations': ['list', 'get', 'process'],
            'filters': {
                'status': {
                    'type': 'select',
                    'options': ['OPEN', 'PARTIAL', 'COMPLETE'],
                    'description': 'Order status'
                },
                'customer_code': {
                    'type': 'integer',
                    'description': 'Customer code'
                },
                'date_from': {
                    'type': 'date',
                    'description': 'Start date for filtering'
                },
                'date_to': {
                    'type': 'date',
                    'description': 'End date for filtering'
                }
            },
            'columns': [
                {
                    'name': 'pr_repair_order_id',
                    'type': 'integer',
                    'description': 'Performance Radiator Repair Order ID',
                    'sortable': True
                },
                {
                    'name': 'pt_order_id',
                    'type': 'string',
                    'description': 'Parts Trader Order ID',
                    'sortable': True
                },
                {
                    'name': 'customer_code',
                    'type': 'integer',
                    'description': 'Customer Code',
                    'sortable': True
                },
                {
                    'name': 'status',
                    'type': 'string',
                    'description': 'Order Status',
                    'sortable': True
                },
                {
                    'name': 'created_at',
                    'type': 'datetime',
                    'description': 'Order Creation Date',
                    'sortable': True
                },
                {
                    'name': 'total',
                    'type': 'decimal',
                    'description': 'Total Order Value',
                    'sortable': True
                }
            ]
        }
    
    def handle_create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create operations not implemented for parked orders"""
        raise MinerError(
            'Create operation not supported for parked orders',
            'NotImplementedError',
            405
        )
    
    def handle_update(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update operations not implemented for parked orders"""
        raise MinerError(
            'Update operation not supported for parked orders',
            'NotImplementedError',
            405
        )
    
    def handle_process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process custom operations like creating POs for parts
        
        Expected data format for create_po:
        {
            "action": "create_po",
            "pr_repair_order_id": 12345,
            "part_line": 1,
            "vendor_code": "VEND001",
            "quantity": 2,
            "user": "john.doe"
        }
        """
        action = data.get('action')
        
        if action == 'create_po':
            return self._handle_create_po(data)
        else:
            raise MinerError(
                f'Unknown action: {action}',
                'ValidationError',
                400
            )
    
    def _handle_create_po(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle PO creation for a part"""
        db_session = None
        try:
            # Validate required fields
            required_fields = ['pr_repair_order_id', 'part_line', 'vendor_code', 'quantity']
            for field in required_fields:
                if field not in data:
                    raise MinerError(f'{field} is required', 'ValidationError', 400)
            
            db_session = db_registry._routing_session()
            service = ParkedOrderService(db_session, self.company_database)
            
            po_number = service.create_purchase_order_for_part(
                pr_repair_order_id=data['pr_repair_order_id'],
                part_line=data['part_line'],
                vendor_code=data['vendor_code'],
                quantity=data['quantity'],
                user=data.get('user', self.auth_context.get('username', 'SYSTEM'))
            )
            
            if po_number:
                return {
                    'success': True,
                    'po_number': po_number,
                    'message': f'Purchase order {po_number} created successfully'
                }
            else:
                raise MinerError('Failed to create purchase order', 'ProcessingError', 500)
                
        except MinerError:
            raise
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error creating PO: {e}")
            raise MinerError(f"Failed to create PO: {str(e)}", "DatabaseError", 500)
        finally:
            if db_session:
                db_session.close()