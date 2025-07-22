# service/parked_order_service.py
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


from app.models import get_model

class ParkedOrderErrorCode(Enum):
    """Error codes for parked order operations"""
    VALIDATE_ORDER_FAILED = "VALIDATE_ORDER_FAILED"
    ORDER_NOT_FOUND = "ORDER_NOT_FOUND"
    DATABASE_ERROR = "DATABASE_ERROR"
    INVALID_COMPANY = "INVALID_COMPANY"
    MODEL_NOT_FOUND = "MODEL_NOT_FOUND"


class ParkedOrderError(Exception):
    """Custom exception for parked order operations"""
    def __init__(self, error_code: ParkedOrderErrorCode, message: str = "", additional_info: str = ""):
        self.error_code = error_code
        self.message = message or str(error_code.value)
        self.additional_info = additional_info
        super().__init__(self.message)


class ParkedOrderService:
    """Service for managing parked orders and parts procurement"""
    __depends_on__ = []
    
    def __init__(self, db: Session, company_database: str = "GPACIFIC"):
        """
        Initialize the service
        
        Args:
            db: Database session
            company_database: Company database to use (GPACIFIC or GCANADA)
        """
        self.db = db
        self.company_database = company_database
        
        # Validate company database
        if company_database not in ["GPACIFIC", "GCANADA"]:
            raise ParkedOrderError(
                ParkedOrderErrorCode.INVALID_COMPANY,
                additional_info=f"Invalid company database: {company_database}"
            )
    
    def _get_model(self, model_name: str):
        """
        Get the appropriate model based on company database

        Args:
            model_name: Name of the model (e.g., 'BKAPPO', 'BKAPPOL', etc.)

        Returns:
            The appropriate model class for the current company
        """
        if not self.company_database:
            raise ParkedOrderError(
                ParkedOrderErrorCode.VALIDATE_ORDER_FAILED,
                additional_info="Company database not set"
            )

        model_map = {
            'GPACIFIC': {
                'BKAPPO': get_model('GPACIFIC_dbo_BKAPPO'),
                'BKAPPOL': get_model('GPACIFIC_dbo_BKAPPOL'),
                'BKPOERD': get_model('GPACIFIC_dbo_BKPOERD'),
                'BKICLOC': get_model('GPACIFIC_dbo_BKICLOC'),
                'BKSYMSTR': get_model('GPACIFIC_dbo_BKSYMSTR'),
                'BKAPHPO': get_model('GPACIFIC_dbo_BKAPHPO'),
                'BKAPHPOL': get_model('GPACIFIC_dbo_BKAPHPOL'),
                'BKAPVEND': get_model('GPACIFIC_dbo_BKAPVEND'),
                'BKARCUST': get_model('GPACIFIC_dbo_BKARCUST'),
                'BKPHONE': get_model('GPACIFIC_dbo_BKPHONE'),
                'BKICVNXF': get_model('GPACIFIC_dbo_BKICVNXF')
            },
            'GCANADA': {
                'BKAPPO': get_model('GCANADA_dbo_BKAPPO'),
                'BKAPPOL': get_model('GCANADA_dbo_BKAPPOL'),
                'BKPOERD': get_model('GCANADA_dbo_BKPOERD'),
                'BKICLOC': get_model('GCANADA_dbo_BKICLOC'),
                'BKSYMSTR': get_model('GCANADA_dbo_BKSYMSTR'),
                'BKAPHPO': get_model('GCANADA_dbo_BKAPHPO'),
                'BKAPHPOL': get_model('GCANADA_dbo_BKAPHPOL'),
                'BKAPVEND': get_model('GCANADA_dbo_BKAPVEND'),
                'BKARCUST': get_model('GCANADA_dbo_BKARCUST'),
                'BKPHONE': get_model('GCANADA_dbo_BKPHONE'),
                'BKICVNXF': get_model('GCANADA_dbo_BKICVNXF')
            }
        }

        if self.company_database not in model_map:
            raise ParkedOrderError(
                ParkedOrderErrorCode.INVALID_COMPANY,
                additional_info=f"Unknown company database: {self.company_database}"
            )

        if model_name not in model_map[self.company_database]:
            raise ParkedOrderError(
                ParkedOrderErrorCode.MODEL_NOT_FOUND,
                additional_info=f"Unknown model: {model_name}"
            )

        return model_map[self.company_database][model_name]
     
    def get_parked_order_details(self, pr_repair_order_id: int) -> Dict:
        """
        Get complete parked order details for parts procurement management
        
        Args:
            pr_repair_order_id: Performance Radiator repair order ID
            
        Returns:
            Dict with order info, customer, requester, warehouse, parts, and summary
        """
        try:



            # 1. Get main order
            order_info = self._get_order_info(pr_repair_order_id)
            if not order_info:
                raise ParkedOrderError(
                    ParkedOrderErrorCode.ORDER_NOT_FOUND,
                    additional_info=f"Order not found: RO={pr_repair_order_id}"
                )

            # 2. Get requester info (who requested the parts)
            requester = self._get_requester_info(order_info['_repairer_id'])
            
            # 3  getting requester:
            repairer = self._get_repairer_info(order_info['_repairer_id'])


            # 4. Get customer info (where parts will be shipped)
            if order_info['_customer_code']:
                customer = self._get_customer_info(order_info['_customer_code'])
            else:
                customer = self._get_customer_info(repairer['customer_code'])

            # 4. Get closest warehouse for procurement routing
            if customer:
                closest_warehouse = self._get_closest_warehouse(customer.get('zip', ''))
            else:
                closest_warehouse = None

            # 5. Get parts with their procurement status
            parts = self._get_parts_with_procurement_status(pr_repair_order_id)
            
            # 6. Calculate procurement summary
            order_summary = self._calculate_procurement_summary(parts)
            
            # Remove internal fields from order_info
            order_info.pop('_customer_code', None)
            order_info.pop('_repairer_id', None)
            
            return {
                "order_info": order_info,
                "customer": customer,
                "repairer":repairer,
                "requester": requester,
                "closest_warehouse": closest_warehouse,
                "parts": parts,
                "order_summary": order_summary
            }
            
        except ParkedOrderError:
            raise
        except Exception as e:
            logger.error(f"Error getting parked order details: {e}")
            raise ParkedOrderError(
                ParkedOrderErrorCode.DATABASE_ERROR,
                additional_info=str(e)
            )
    
    def _get_order_info(self, pr_repair_order_id: int) -> Optional[Dict]:
        """Get basic order information"""
        try:
            parked_orders = get_model('PartsTrader_dbo_parked_orders')
            order = self.db.query(parked_orders).filter(
                parked_orders.pr_repair_order_id == pr_repair_order_id
            ).first()
            
            if not order:
                return None
            
            # Determine order status based on parts status
            status = self._determine_order_status(pr_repair_order_id)
            
            return {
                "pt_order_id": order.pt_order_id,  # Still include for reference
                "pr_repair_order_id": order.pr_repair_order_id,
                "status": status,
                "created_at": order.created_at.strftime("%Y-%m-%d") if order.created_at else None,
                "total": float(order.total) if order.total else None,
                "subtotal": float(order.total) if order.total else None,
                "tax": None,
                "freight": None,
                "_customer_code": order.customer_code,
                "_repairer_id": order.repairer_id
            }
        except Exception as e:
            logger.error(f"Error getting order info: {e}")
            raise
    
    def _determine_order_status(self, pr_repair_order_id: int) -> Optional[str]:
        """Determine overall order status based on parts and their POs"""
        try:
            parked_parts = get_model('PartsTrader_dbo_parked_order_parts')
            parked_orders_po = get_model('PartsTrader_dbo_parked_orders_po')
            
            # Get all parts for this order
            parts = self.db.query(parked_parts).filter(
                parked_parts.pr_repair_order_id == pr_repair_order_id
            ).all()
            
            if not parts:
                return None
            
            # Check each part's order status
            all_parts_fully_ordered = True
            some_parts_ordered = False
            
            for part in parts:
                # Get total ordered quantity for this part
                po_result = self.db.query(
                    func.sum(parked_orders_po.quantity)
                ).filter(
                    parked_orders_po.pr_repair_order_id == pr_repair_order_id,
                    parked_orders_po.line == part.line,
                    parked_orders_po.part == part.part
                ).scalar()
                
                quantity_ordered = po_result or 0
                
                if quantity_ordered > 0:
                    some_parts_ordered = True
                    
                if quantity_ordered < part.quantity:
                    all_parts_fully_ordered = False
            
            # Determine overall status
            if all_parts_fully_ordered and some_parts_ordered:
                return "COMPLETE"
            elif some_parts_ordered:
                return "PARTIAL"
            else:
                return "OPEN"
                
        except Exception as e:
            logger.error(f"Error determining order status: {e}")
            return None
        
    def _get_customer_info(self, customer_code: Optional[int]) -> Optional[Dict]:
        """Get customer information"""
        try:
            if not customer_code:
                return None
            print("TRYING CUST INFO")
            # Get the appropriate model for this company
            BKARCUST = self._get_model('BKARCUST')
            BKPHONE = self._get_model('BKPHONE')
            
            customer = self.db.query(BKARCUST).filter(
                BKARCUST.code == customer_code
            ).first()
            
            if not customer:
                return None
                
            # Get phone numbers
            phones = self.db.query(BKPHONE).filter(
                BKPHONE.cstcod == customer_code
            ).all()
            
            main_phone = customer.telephone.strip() if customer.telephone else None
            fax = customer.fax_phone.strip() if customer.fax_phone else None
            
            # Override with specific phone types if available
            for phone in phones:
                if phone.type == 'W':  # Main
                    main_phone = phone.phone.strip() if phone.phone else None
                elif phone.type == 'F':  # Fax
                    fax = phone.phone.strip() if phone.phone else None
            
            return {
                "customer_code": str(customer_code),
                "name": customer.name.strip() if customer.name else None,
                "address_1": customer.add1.strip() if customer.add1 else None,
                "address_2": customer.add2.strip() if customer.add2 else None,
                "city": customer.city.strip() if customer.city else None,
                "state": customer.state.strip() if customer.state else None,
                "zip": customer.zip_.strip() if customer.zip_ else None,
                "phone": self._format_phone(main_phone) if main_phone else None,
                "fax": self._format_phone(fax) if fax else None,
                "website": None
            }
            
        except Exception as e:
            logger.error(f"Error getting customer info: {e}")
            return None
    
    def _get_repairer_info(self, repairer_id: str) -> Optional[Dict]:
        """Get repairer/shop information"""
        try:
            if not repairer_id:
                return None
                
            repairers = get_model('PartsTrader_dbo_repairers')  # or whatever your repairer table is
            repairer = self.db.query(repairers).filter(
                repairers.repairer_id == repairer_id
            ).first()
            
            if not repairer:
                return None
            return repairer.to_dict()
            
        except Exception as e:
            logger.error(f"Error getting repairer info: {e}")
            return None
    def _get_requester_info(self, repairer_id: str) -> Optional[Dict]:
        """Get requester information"""
        try:
            if not repairer_id:
                return None
                
            requesters = get_model('PartsTrader_dbo_requesters')
            requester = self.db.query(requesters).filter(
                requesters.repairer_id == repairer_id
            ).first()
            
            if not requester:
                return None
                
            first_name = requester.first_name if requester.first_name else ""
            last_name = requester.last_name if requester.last_name else ""
            full_name = f"{first_name} {last_name}".strip() if (first_name or last_name) else None
            
            return {
                "name": full_name,
                "email": requester.email if requester.email else None,
                "phone": self._format_phone(requester.phone_number) if requester.phone_number else None
            }
            
        except Exception as e:
            logger.error(f"Error getting requester info: {e}")
            return None
    
    def _get_closest_warehouse(self, customer_zip: str) -> Optional[Dict]:
        """Get assigned warehouse for procurement based on customer location"""
        try:
            if not customer_zip:
                return None
            
            # Clean zip to first 5 digits
            zip_code = customer_zip[:5]
            
            BKZIP = get_model('JADVDATA_dbo_BKZIP')
            # Get warehouse assignment from BKZIP
            zip_info = self.db.query(BKZIP).filter(
                BKZIP.zip == zip_code
            ).first()
            
            if not zip_info or not zip_info.warehouse:
                print("didnt find it  zip")
                return None
            print ("SHIit")
                
            warehouse_code = zip_info.warehouse.strip()
            
            locations = get_model('JADVDATA_dbo_locations')
            # Get warehouse details
            location = self.db.query(locations).filter(
                locations.location == warehouse_code,
                locations.warehouse == 1,
                locations.active == 1
            ).first()
            print ("maybe it")
            
            if not location:
                print("didnt find it  location")
                return None
            print ("got it")
            return {
                "code": location.location.strip() if location.location else None,
                "name": location.location_name.strip() if location.location_name else None,
                "address": location.addressstr.strip() if location.addressstr else None,
                "city": location.citystr.strip() if location.citystr else None,
                "state": location.statestr.strip() if location.statestr else None,
                "zip": location.zipstr.strip() if location.zipstr else None,
                "distance_miles": None  # Would calculate if needed
            }
            
        except Exception as e:
            logger.error(f"Error getting warehouse info: {e}")
            return None
    
    def _get_parts_with_procurement_status(self, pr_repair_order_id: int) -> List[Dict]:
        """Get all parts with their procurement/PO status"""
        try:
            parked_parts = get_model('PartsTrader_dbo_parked_order_parts')
            parts = self.db.query(parked_parts).filter(
                parked_parts.pr_repair_order_id == pr_repair_order_id
            ).order_by(parked_parts.line).all()
            
            result = []
            for part in parts:
                part_data = {
                    "line": part.line,
                    "part_number": part.part.strip() if part.part else None,
                    "description": self._get_part_description(part.part),
                    "quantity_needed": part.quantity,
                    "quantity_ordered": 0,
                    "list_price": part.list_price,
                    "sale_price": part.sale_price,
                    "status": "NOT_ORDERED",
                    "sale_price_ext": part.sale_price_ext,
                    "parked_status": part.status,                    
                    "purchase_orders": []
                }
                
                # Get all POs for this part
                purchase_orders = self._get_part_purchase_orders(
                    pr_repair_order_id, 
                    part.line, 
                    part.part
                )

                # Get all SOs for this part
                sales_orders = self._get_part_sales_orders(
                    pr_repair_order_id,
                    part.line,
                    part.part
                )

                # Calculate quantities
                quantity_ordered = sum(po.get("quantity", 0) for po in purchase_orders)
                has_invoices = any(so.get("inv_number") for so in sales_orders)

                # Add to part_data
                part_data["purchase_orders"] = purchase_orders
                part_data["sales_orders"] = sales_orders
                part_data["quantity_ordered"] = quantity_ordered

                # Calculate proper status
                part_data["status"] = self._calculate_part_status(
                    part_data["quantity_needed"],
                    quantity_ordered,
                    has_invoices
                )
                result.append(part_data)
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting parts with procurement status: {e}")
            return []
    
    def _calculate_part_status(self, quantity_needed: int, quantity_ordered: int, has_invoices: bool) -> str:
        """Calculate accurate part status based on quantities"""
        if quantity_ordered == 0:
            return "NOT_ORDERED"
        elif quantity_ordered < quantity_needed:
            if has_invoices:
                return "PARTIAL_INVOICED"
            else:
                return "PARTIAL_ORDERED"
        else:  # quantity_ordered >= quantity_needed
            if has_invoices:
                return "FULLY_INVOICED"
            else:
                return "FULLY_ORDERED"
            
    def _calculate_part_procurement_status(self, needed: int, ordered: int) -> str:
        """Calculate part procurement status"""
        if ordered == 0:
            return "NOT_ORDERED"
        elif ordered < needed:
            return "PARTIAL"
        else:
            return "ORDERED"
    
    def _calculate_procurement_summary(self, parts: List[Dict]) -> Dict:
        """Calculate procurement summary statistics"""
        total_parts = len(parts)
        parts_fully_ordered = sum(1 for p in parts if p["status"] == "ORDERED")
        parts_partially_ordered = sum(1 for p in parts if p["status"] == "PARTIAL")
        parts_not_ordered = sum(1 for p in parts if p["status"] == "NOT_ORDERED")
        total_pos = sum(len(p["purchase_orders"]) for p in parts)
        
        return {
            "total_parts": total_parts,
            "parts_fully_ordered": parts_fully_ordered,
            "parts_partially_ordered": parts_partially_ordered,
            "parts_not_ordered": parts_not_ordered,
            "total_pos_created": total_pos
        }
    
    def _get_part_description(self, part_number: str) -> Optional[str]:
        """Get part description from inventory"""
        try:
            if not part_number:
                return None
                
            # Get the appropriate model for this company
            BKICLOC = self._get_model('BKICLOC')
            
            # Query inventory for part description
            # Note: BKICLOC doesn't have description, so this is a placeholder
            # You might need to query a different table for descriptions
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting part description: {e}")
            return None
    
    def _format_phone(self, phone: str) -> Optional[str]:
        """Format phone number to (XXX) XXX-XXXX"""
        if not phone:
            return None
            
        # Remove non-digits
        digits = ''.join(c for c in phone if c.isdigit())
        
        if len(digits) == 10:
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        elif len(digits) == 7:
            return f"{digits[:3]}-{digits[3:]}"
        else:
            return phone
    
    def get_next_po_number(self) -> int:
        """Get the next available PO number"""
        try:
            BKSYMSTR = self._get_model('BKSYMSTR')
            system_settings = self.db.query(BKSYMSTR).first()
            
            if system_settings:
                return system_settings.appo_num + 1
            else:
                raise ParkedOrderError(
                    ParkedOrderErrorCode.DATABASE_ERROR,
                    additional_info="System settings not found"
                )
                
        except Exception as e:
            logger.error(f"Error getting next PO number: {e}")
            raise ParkedOrderError(
                ParkedOrderErrorCode.DATABASE_ERROR,
                additional_info=str(e)
            )
    
    def create_purchase_order_for_part(self, pr_repair_order_id: int, 
                                     part_line: int, vendor_code: str,
                                     quantity: int, user: str = "SYSTEM") -> Optional[int]:
        """
        Create a new purchase order for a part
        
        Args:
            pr_repair_order_id: Repair order ID
            part_line: Line number of the part
            vendor_code: Vendor code to order from
            quantity: Quantity to order
            user: User creating the PO
            
        Returns:
            New PO number if successful, None otherwise
        """
        try:
            # Get the appropriate models for this company
            BKAPPO = self._get_model('BKAPPO')
            BKAPPOL = self._get_model('BKAPPOL')
            BKSYMSTR = self._get_model('BKSYMSTR')
            
            # This would implement the full PO creation logic
            # Including updating BKSYMSTR, creating BKAPPO/BKAPPOL records
            # and updating parked_order_parts
            
            # Placeholder for now
            logger.info(f"Would create PO for RO {pr_repair_order_id}, "
                       f"part line {part_line}, vendor {vendor_code}, qty {quantity}")
            
            return None
            
        except Exception as e:
            logger.error(f"Error creating PO: {e}")
            raise ParkedOrderError(
                ParkedOrderErrorCode.DATABASE_ERROR,
                additional_info=str(e)
            )
    
    def get_parked_order_by_pt_order(self, pt_order_id: str) -> List[int]:
        """
        Get all PR repair order IDs associated with a PT order ID
        
        Args:
            pt_order_id: PartsTrader order ID
            
        Returns:
            List of pr_repair_order_id values
        """
        try:
            parked_orders = get_model('PartsTrader_dbo_parked_orders')
            orders = self.db.query(parked_orders.pr_repair_order_id).filter(
                parked_orders.pt_order_id == pt_order_id
            ).all()
            
            return [order[0] for order in orders]
            
        except Exception as e:
            logger.error(f"Error getting repair order IDs for PT order {pt_order_id}: {e}")
            return []
        
    def _get_part_purchase_orders(self, pr_repair_order_id: int, line: int, part: str) -> List[Dict]:
        """Get all purchase orders for a specific part line"""
        try:
            parked_orders_po = get_model('PartsTrader_dbo_parked_orders_po')
            pos = self.db.query(parked_orders_po).filter(
                parked_orders_po.pr_repair_order_id == pr_repair_order_id ).all()
            
            result = []
            for po in pos:
                # Get detailed PO info from BKAPPO/BKAPPOL
                result.append({
                    "po_number": po.po_number,
                    "quantity": po.quantity,
                    
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting part purchase orders: {e}")
            return []

    def _get_part_sales_orders(self, pr_repair_order_id: int, line: int, part: str) -> List[Dict]:
        """Get all sales orders for a specific part line"""
        try:
            parked_orders_so = get_model('PartsTrader_dbo_parked_orders_so')
            sos = self.db.query(parked_orders_so).filter(
                parked_orders_so.pr_repair_order_id == pr_repair_order_id,
                parked_orders_so.line == line,
                parked_orders_so.part == part.strip()
            ).all()
            
            result = []
            for so in sos:
                result.append({
                    "so_number": so.so_number,
                    "inv_number": so.inv_number,
                    "quantity": so.quantity,
                    "status": "INVOICED" if so.inv_number else "ORDERED"
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting part sales orders: {e}")
            return []

    def _get_po_details_from_tables(self, po_number: int, part: str, quantity: int) -> Optional[Dict]:
        """Get PO details from BKAPPO/BKAPPOL tables"""
        try:
            BKAPPO = self._get_model('BKAPPO')
            BKAPPOL = self._get_model('BKAPPOL')
            BKAPVEND = self._get_model('BKAPVEND')
            
            # Get PO header
            po = self.db.query(BKAPPO).filter(BKAPPO.num == po_number).first()
            if not po:
                # Check history
                BKAPHPO = self._get_model('BKAPHPO')
                po = self.db.query(BKAPHPO).filter(BKAPHPO.num == po_number).first()
            
            if not po:
                return None
                
            # Get vendor info
            vendor = None
            if po.vndcod:
                vendor = self.db.query(BKAPVEND).filter(
                    BKAPVEND.code == po.vndcod.strip()
                ).first()
            
            return {
                "po_number": po_number,
                "quantity": quantity,
                "vendor_code": po.vndcod.strip() if po.vndcod else None,
                "vendor_name": vendor.name.strip() if vendor and vendor.name else None,
                "order_date": po.orddte.strftime("%Y-%m-%d") if po.orddte else None,
                "warehouse": po.loc.strip() if po.loc else None
            }
            
        except Exception as e:
            logger.error(f"Error getting PO details: {e}")
            return None        