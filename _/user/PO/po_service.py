import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal
from sqlalchemy import and_, or_, func, desc
from sqlalchemy import text
from sqlalchemy.orm import Session
from flask import current_app

from app.register.database import db_registry
from app.models import get_model


from .po_error_class import POErrorCode, get_error_message, format_po_error

logger = logging.getLogger(__name__)


class PurchaseOrderError(Exception):
    """Custom exception for Purchase Order operations"""

    __depends_on__ = ['POErrorCode']  # Depends on error code enum

    def __init__(self, code: POErrorCode, message: str = None, **kwargs):
        self.code = code
        if message:
            self.message = message
        else:
            # Auto-format message based on error code and context
            self.message = format_po_error(
                code,
                po_number=kwargs.get('po_number'),
                part=kwargs.get('part'),
                location=kwargs.get('location'),
                additional_info=kwargs.get('additional_info', '')
            )
        super().__init__(self.message)


class PurchaseOrderService:
    """Service class for handling Purchase Order operations"""

    __depends_on__ = ['PurchaseOrderError', 'POErrorCode']  # Depends on error handling classes

    # Constants
    ABORT_LOCK_TIME = 30  # seconds
    SUCCESS_THRESHOLD = 80  # percent

    def __init__(self, session: Session = None):
        self.db_session = session
        self.po_number = None
        self.company_database = None
        self.fiscal_year = None
        self.errors = []
        self.warnings = []
        self.queries = []
        self.successful_items = 0
        self.requested_items = 0
        self.locked_rows = []  # Track locked rows for cleanup
        self.db_session=db_registry._routing_session()


    def _get_model(self, model_name: str):
        """
        Get the appropriate model based on company database

        Args:
            model_name: Name of the model (e.g., 'BKAPPO', 'BKAPPOL', etc.)

        Returns:
            The appropriate model class for the current company
        """
        if not self.company_database:
            raise PurchaseOrderError(
                POErrorCode.VALIDATE_PO_FAILED,
                additional_info="Company database not set"
            )

        model_map = {
            'GPACIFIC': {
                'BKAPPO': get_model('GPACIFIC_dbo_BKAPPO'),
                'BKAPPOL': get_model('GPACIFIC_dbo_BKAPPOL'),
                'BKPOERD': get_model('GPACIFIC_dbo_BKPOERD'),
                'BKICLOC': get_model('GPACIFIC_dbo_BKICLOC'),
                'BKSYMSTR': get_model('GPACIFIC_dbo_BKSYMSTR'),
                'po_details': get_model('GPACIFIC_dbo_po_details'),
                'BKAPHPO': get_model('GPACIFIC_dbo_BKAPHPO'),
                'BKAPHPOL': get_model('GPACIFIC_dbo_BKAPHPOL')
            },
            'GCANADA': {
                'BKAPPO': get_model('GCANADA_dbo_BKAPPO'),
                'BKAPPOL': get_model('GCANADA_dbo_BKAPPOL'),
                'BKPOERD': get_model('GCANADA_dbo_BKPOERD'),
                'BKICLOC': get_model('GCANADA_dbo_BKICLOC'),
                'BKSYMSTR': get_model('GCANADA_dbo_BKSYMSTR'),
                'po_details': get_model('GCANADA_dbo_po_details'),
                'BKAPHPO': get_model('GCANADA_dbo_BKAPHPO'),
                'BKAPHPOL': get_model('GCANADA_dbo_BKAPHPOL')
            }
        }

        if self.company_database not in model_map:
            raise PurchaseOrderError(
                POErrorCode.VALIDATE_PO_FAILED,
                additional_info=f"Unknown company database: {self.company_database}"
            )

        if model_name not in model_map[self.company_database]:
            raise PurchaseOrderError(
                POErrorCode.VALIDATE_PO_FAILED,
                additional_info=f"Unknown model: {model_name}"
            )

        return model_map[self.company_database][model_name]

    def create_purchase_order(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new purchase order

        Args:
            data: Dictionary containing:
                - user: Username creating the PO
                - company: Company (PACIFIC or CANADA)
                - from: Vendor code
                - to: Destination warehouse
                - vendid: Vendor ID
                - line_items: Dict of items {part_number: {description, ord_qty, rec_qty, price, extended}}
                - billinfo: Billing information
                - shipinfo: Shipping information
                - freight: Freight cost
                - erd: Expected receipt date
                - notes: List of note lines
                - warr_items: Warranty items

        Returns:
            Dict with PO creation results
        """
        try:
            # Validate input data
            self._validate_input_data(data)

            # Fix part numbers - replace underscores with dots
            self._fix_part_numbers(data)

            # Set company based on company parameter
            self._set_company(data['company'])

            # Check if location is locked
            self._check_location_lock(data['to'])

            # Validate fiscal year
            self._validate_fiscal_year()

            # Create PO number
            self.po_number = self._create_po_number()

            # Lock location
            self._lock_location(data['to'], data['user'])

            try:
                # Create PO header
                self._create_po_header(data)

                # Validate PO (check parts exist in destination)
                validated_items = self._validate_po(data['to'], data['line_items'])

                # Create PO lines
                line_count, subtotal = self._create_po_lines(
                    data['to'],
                    validated_items,
                    data.get('warr_items', {}),
                    data.get('notes', []),
                    data.get('erd', datetime.now().date())
                )

                # Update PO header with totals
                total = subtotal + data.get('freight', 0)
                self._update_po_header(data, line_count, subtotal, total)

                # Log the operation
                self._log_operation(data, 'POLIST_NEW')

                # Commit transaction
                self.db_session.commit()

                return {
                    'success': True,
                    'po_number': self.po_number,
                    'company': self.company_database,
                    'line_items': validated_items,
                    'total': total,
                    'warnings': self.warnings
                }

            except Exception as e:
                # Rollback on error
                self.db_session.rollback()
                raise
            finally:
                # Always unlock location and rows
                self._unlock_location(self.po_number)
                self._unlock_all_rows()

        except PurchaseOrderError as e:
            logger.error(f"PO Error {e.code}: {e.message}")
            return {
                'success': False,
                'error_code': e.code,
                'error_message': e.message,
                'errors': self.errors
            }
        except Exception as e:
            logger.exception("Unexpected error creating PO")
            return {
                'success': False,
                'error_message': str(e),
                'errors': self.errors
            }

    def edit_purchase_order(self, po_number: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Edit an existing purchase order"""
        try:
            self.po_number = po_number

            # Fix part numbers - replace underscores with dots
            self._fix_part_numbers(data)

            # Company is required
            if 'company' not in data:
                raise PurchaseOrderError(
                    POErrorCode.VALIDATE_PO_FAILED,
                    additional_info="Company is required (PACIFIC or CANADA)"
                )

            # Set company
            self._set_company(data['company'])

            # Load existing PO
            po_header = self._get_po_header(po_number)
            if not po_header:
                raise PurchaseOrderError(
                    POErrorCode.INVALID_PO_NUMBER,
                    po_number=po_number
                )

            # Lock location
            self._lock_location(po_header.loc, data['user'])

            try:
                # Validate new items
                validated_items = self._validate_po(po_header.loc, data['line_items'])

                # Empty existing PO lines
                self._empty_po(po_number, po_header.loc)

                # Create new PO lines
                line_count, subtotal = self._create_po_lines(
                    po_header.loc,
                    validated_items,
                    data.get('warr_items', {}),
                    data.get('notes', []),
                    data.get('erd', datetime.now().date())
                )

                # Update header
                total = subtotal + data.get('freight', 0)
                self._update_po_header(data, line_count, subtotal, total)

                # Log operation
                self._log_operation(data, 'POLIST_EDIT')

                self.db_session.commit()

                return {
                    'success': True,
                    'po_number': self.po_number,
                    'line_items': validated_items,
                    'total': total
                }

            except Exception:
                self.db_session.rollback()
                raise
            finally:
                self._unlock_location(self.po_number)
                self._unlock_all_rows()

        except PurchaseOrderError as e:
            logger.error(f"PO Edit Error {e.code}: {e.message}")
            return {
                'success': False,
                'error_code': e.code,
                'error_message': e.message
            }

    def delete_purchase_order(self, po_number: int, user: str, company: str) -> Dict[str, Any]:
        """Delete a purchase order"""
        try:
            self.po_number = po_number

            # Set company
            self._set_company(company)

            # Load PO header
            po_header = self._get_po_header(po_number)
            if not po_header:
                raise PurchaseOrderError(
                    POErrorCode.INVALID_PO_NUMBER,
                    po_number=po_number
                )

            # Lock location
            self._lock_location(po_header.loc, user)

            try:
                # Empty PO (removes lines and adjusts inventory)
                self._empty_po(po_number, po_header.loc)

                # Delete header
                self.db_session.delete(po_header)

                # Delete ERD record
                BKPOERD = self._get_model('BKPOERD')
                erd_record = self.db_session.query(BKPOERD).filter_by(
                    num=po_number
                ).first()
                if erd_record:
                    self.db_session.delete(erd_record)

                # Delete po_details
                po_details_model = self._get_model('po_details')
                po_details = self.db_session.query(po_details_model).filter_by(
                    po_num=po_number
                ).first()
                if po_details:
                    self.db_session.delete(po_details)

                # Log operation
                self._log_operation({'user': user, 'po_number': po_number}, 'POLIST_DELETE')

                self.db_session.commit()

                return {
                    'success': True,
                    'message': f'PO {po_number} deleted successfully'
                }

            except Exception:
                self.db_session.rollback()
                raise
            finally:
                self._unlock_location(self.po_number)
                self._unlock_all_rows()

        except PurchaseOrderError as e:
            logger.error(f"PO Delete Error {e.code}: {e.message}")
            return {
                'success': False,
                'error_code': e.code,
                'error_message': e.message
            }

    def mark_as_printed(self, po_number: int, company: str) -> Dict[str, Any]:
        """Mark a PO as printed"""
        try:
            # Set company
            self._set_company(company)

            po_header = self._get_po_header(po_number)
            if not po_header:
                raise PurchaseOrderError(
                    POErrorCode.INVALID_PO_NUMBER,
                    po_number=po_number
                )

            if po_header.prtd == 'Y':
                self.warnings.append("PO already marked as printed")
                return {
                    'success': True,
                    'already_printed': True
                }

            # Lock header before updating
            self._lock_row(self.company_database, 'dbo', 'BKAPPO', po_header.record)

            po_header.prtd = 'Y'
            self.db_session.commit()

            # Unlock after commit
            self._unlock_row(self.company_database, 'dbo', 'BKAPPO', po_header.record)

            return {
                'success': True,
                'message': f'PO {po_number} marked as printed'
            }

        except Exception as e:
            logger.exception(f"Error marking PO {po_number} as printed")
            self._unlock_all_rows()
            return {
                'success': False,
                'error_message': str(e)
            }

    # Row locking helper methods

    def _lock_row(self, database: str, schema: str, table: str, row_id: int):
        """Lock a row for writing using stored procedure"""
        try:
            result = self.db_session.execute(
                text("EXEC [dbo].[_adv_row_lock] :database, :schema, :table, :row_id"),
                {
                    'database': database,
                    'schema': schema,
                    'table': table,
                    'row_id': row_id
                }
            )
            self.locked_rows.append((database, schema, table, row_id))
            logger.debug(f"Locked row: {database}.{schema}.{table} ID={row_id}")
        except Exception as e:
            logger.error(f"Failed to lock row: {database}.{schema}.{table} ID={row_id}: {e}")
            raise PurchaseOrderError(
                POErrorCode.ROW_LOCK_FAILED,
                additional_info=f"{table} row {row_id}"
            )

    def _unlock_row(self, database: str, schema: str, table: str, row_id: int):
        """Unlock a row after writing"""
        try:
            result = self.db_session.execute(
                text("EXEC [dbo].[_adv_row_unlock] :database, :schema, :table, :row_id"),
                {
                    'database': database,
                    'schema': schema,
                    'table': table,
                    'row_id': row_id
                }
            )
            logger.debug(f"Unlocked row: {database}.{schema}.{table} ID={row_id}")
        except Exception as e:
            logger.warning(f"Failed to unlock row: {database}.{schema}.{table} ID={row_id}: {e}")

    def _unlock_all_rows(self):
        """Unlock all locked rows - used in cleanup"""
        for database, schema, table, row_id in self.locked_rows:
            self._unlock_row(database, schema, table, row_id)
        self.locked_rows = []

    def _validate_input_data(self, data: Dict[str, Any]):
        """Validate required input data"""
        required_fields = ['user', 'company', 'from', 'to', 'line_items', 'billinfo', 'shipinfo']
        for field in required_fields:
            if field not in data:
                raise PurchaseOrderError(
                    POErrorCode.VALIDATE_PO_FAILED,
                    additional_info=f"Missing required field: {field}"
                )

        if not data['line_items']:
            raise PurchaseOrderError(
                POErrorCode.VALIDATE_PO_FAILED,
                additional_info="No line items provided"
            )

    def _set_company(self, company: str):
        """Set company database based on company parameter"""
        if company.upper() == 'CANADA':
            self.company_database = 'GCANADA'
        elif company.upper() == 'PACIFIC':
            self.company_database = 'GPACIFIC'
        else:
            raise PurchaseOrderError(
                POErrorCode.VALIDATE_PO_FAILED,
                additional_info=f"Invalid company: {company}. Must be PACIFIC or CANADA"
            )

    def _check_location_lock(self, location: str):
        """Check if location is locked"""
        cutoff_time = datetime.now() - timedelta(seconds=self.ABORT_LOCK_TIME)

        lock = self.db_session.query(JADVDATA_dbo_po_lock).filter(
            and_(
                JADVDATA_dbo_po_lock.loc == location,
                JADVDATA_dbo_po_lock.created_at > cutoff_time
            )
        ).first()

        if lock:
            raise PurchaseOrderError(
                POErrorCode.LOCATION_LOCKED,
                location=location
            )

    def _lock_location(self, location: str, username: str):
        """Lock a location for PO operations"""
        lock = JADVDATA_dbo_po_lock(
            loc=location,
            po_id=str(self.po_number),
            username=username,
            created_at=datetime.now()
        )
        self.db_session.add(lock)
        self.db_session.flush()

    def _unlock_location(self, po_number: int):
        """Unlock location after PO operation"""
        self.db_session.query(JADVDATA_dbo_po_lock).filter_by(
            po_id=str(po_number)
        ).delete()
        self.db_session.flush()

    def _validate_fiscal_year(self):
        """Validate fiscal year is appropriate - MUST be current year"""
        BKSYMSTR = self._get_model('BKSYMSTR')
        sysmstr = self.db_session.query(BKSYMSTR).first()
        if not sysmstr:
            raise PurchaseOrderError(
                POErrorCode.FISCAL_YEAR_LOAD_ERROR
            )

        self.fiscal_year = sysmstr.fiscal_yr

        # Parse fiscal year
        if isinstance(self.fiscal_year, str):
            fiscal_year_start = datetime.strptime(self.fiscal_year, '%Y-%m-%d')
        else:
            fiscal_year_start = self.fiscal_year

        fiscal_year_num = fiscal_year_start.year
        current_year = datetime.now().year

        # ONLY allow current year - no past, no future
        if fiscal_year_num != current_year:
            raise PurchaseOrderError(
                POErrorCode.FISCAL_YEAR_IN_PAST if fiscal_year_num < current_year else POErrorCode.FISCAL_YEAR_IN_FUTURE,
                additional_info=f"POs can only be created for the current year ({current_year}). System fiscal year is {fiscal_year_num}."
            )

    def _create_po_number(self) -> int:
        """Generate next PO number"""
        # Get system master record
        BKSYMSTR = self._get_model('BKSYMSTR')
        sysmstr = self.db_session.query(BKSYMSTR).first()
        if not sysmstr:
            raise PurchaseOrderError(
                POErrorCode.CREATE_PO_NUMBER_FAILED
            )

        # Lock the system master row for update
        self._lock_row(self.company_database, 'dbo', 'BKSYMSTR', sysmstr.record)

        base_number = sysmstr.appo_num

        # Check for highest number in active tables
        BKAPPO = self._get_model('BKAPPO')
        BKAPPOL = self._get_model('BKAPPOL')

        max_po = self.db_session.query(func.max(BKAPPO.num)).scalar() or 0
        max_pol = self.db_session.query(func.max(BKAPPOL.ponm)).scalar() or 0

        # Use highest number + 1
        next_number = max(base_number, max_po, max_pol) + 1

        # Update system master
        sysmstr.appo_num = next_number
        self.db_session.flush()

        return next_number

    def _create_po_header(self, data: Dict[str, Any]):
        """Create PO header record"""
        BKAPPO = self._get_model('BKAPPO')
        po_header = BKAPPO(
            num=self.po_number,
            prtd='',
            vndcod=data['from'],
            vndnme=data['billinfo']['companyName'][:30],
            vnda1=data['billinfo'].get('add1', '')[:30],
            vnda2=data['billinfo'].get('add2', '')[:30],
            vndcty=data['billinfo'].get('city', '')[:15],
            vndst=data['billinfo'].get('state', '')[:2],
            vndzip=data['billinfo'].get('zip', '')[:10],
            vndctry=data['billinfo'].get('country', '')[:30],
            shpcod=data.get('for', ''),
            shpnme=data['shipinfo'].get('name', '')[:30],
            shpa1=data['shipinfo'].get('addr', '')[:30],
            shpa2=data['shipinfo'].get('addr2', '')[:30],
            shpcty=data['shipinfo'].get('city', '')[:15],
            shpst=data['shipinfo'].get('state', '')[:2],
            shpzip=data['shipinfo'].get('zip', '')[:10],
            shpctry=data['shipinfo'].get('country', '')[:30],
            shpvia='COMMON CARRIER',
            termd=data['billinfo'].get('termsDesc', '')[:10],
            termnm=data['billinfo'].get('termsNum', 0),
            entby=data['user'][:5],
            obycus=data.get('for', ''),
            taxable='N',
            confirm='N',
            orddte=datetime.now().date(),
            subtot=0,
            taxamt=0,
            total=0,
            nl=0,
            taxrte=0,
            desc='',
            gldpt='',
            loc=data['to'],
            rni_d=0,
            itotal=0,
            endlne='Y',
            shpatn=data['shipinfo'].get('contact', '')[:25],
            frght=data.get('freight', 0)
        )

        self.db_session.add(po_header)

        # Create ERD record
        BKPOERD = self._get_model('BKPOERD')
        erd_record = BKPOERD(
            num=self.po_number,
            vendor=data['from'],
            erd=data.get('erd', datetime.now().date()),
            allow=0,
            allowam=0
        )
        self.db_session.add(erd_record)
        self.db_session.flush()

    def _validate_po(self, location: str, line_items: Dict[str, Any]) -> Dict[str, Any]:
        """Validate parts exist in destination location"""
        # First validate the location
        if not self._validate_location(location):
            raise PurchaseOrderError(
                POErrorCode.INVALID_TO_WAREHOUSE,
                location=location
            )

        validated_items = {}
        part_numbers = list(line_items.keys())

        # Query for all parts in location
        BKICLOC = self._get_model('BKICLOC')
        icloc_records = self.db_session.query(BKICLOC).filter(
            and_(
                BKICLOC.code == location,
                BKICLOC.prod.in_(part_numbers)
            )
        ).all()

        # Create lookup dict
        icloc_lookup = {rec.prod: rec for rec in icloc_records}

        # Validate each part
        for part, item_data in line_items.items():
            if part in icloc_lookup:
                validated_items[part] = {
                    'valid': True,
                    'db_index': icloc_lookup[part].record,
                    'data': item_data
                }
            else:
                self.errors.append(f"Invalid part {part} for location {location}")
                validated_items[part] = {
                    'valid': False,
                    'data': item_data
                }

        # Check if we have any valid parts
        valid_count = sum(1 for item in validated_items.values() if item['valid'])
        if valid_count == 0:
            raise PurchaseOrderError(
                POErrorCode.VALIDATE_PO_FAILED,
                additional_info="No valid parts found for this location"
            )

        return validated_items

    def _create_po_lines(self, location: str, validated_items: Dict[str, Any],
                        warr_items: Dict[str, Any], notes: List[str],
                        erd: datetime.date) -> Tuple[int, float]:
        """Create PO line items"""
        line_count = 0
        subtotal = 0.0

        # Get model classes
        BKICLOC = self._get_model('BKICLOC')
        BKAPPOL = self._get_model('BKAPPOL')

        # Process regular line items
        for part, item_info in validated_items.items():
            if not item_info['valid']:
                continue

            item_data = item_info['data']
            ord_qty = float(item_data.get('ord_qty', 0))

            # Update UOO (Units on Order)
            if ord_qty > 0:
                icloc = self.db_session.query(BKICLOC).filter_by(
                    record=item_info['db_index']
                ).first()

                if icloc:
                    # Lock the inventory row before updating
                    self._lock_row(self.company_database, 'dbo', 'BKICLOC', icloc.record)
                    icloc.uoo += ord_qty

            # Create line item
            price = float(item_data.get('price', 0))
            extended = float(item_data.get('extended', 0))

            po_line = BKAPPOL(
                ponm=self.po_number,
                erd=erd,
                msg=f"{part}      {item_data.get('description', '')}     "[:45],
                pcode=part[:15],
                pdesc=item_data.get('description', '')[:30],
                pqty=ord_qty,
                pprce=price,
                pdisc=0,
                pext=extended,
                pcogs=0,
                itype='R',
                gla='',
                gldpta='',
                txble='',
                rqty=float(item_data.get('rec_qty', 0)),
                iqty=float(item_data.get('inv_qty', 0)),
                loc=location,
                jobcod='',
                tskcod='',
                jqty=0,
                jamt=0,
                jrqty=0,
                cat='',
                note=0,
                line=0
            )

            self.db_session.add(po_line)
            line_count += 1
            subtotal += extended

        # Process warranty items
        for part, warr_data in warr_items.items():
            amount = float(warr_data.get('amount', 0))
            rec_qty = float(warr_data.get('rec_qty', 0))

            warr_line = BKAPPOL(
                ponm=self.po_number,
                erd=erd,
                msg=f"{part}  Warranty"[:45],
                pcode=part[:15],
                pdesc="Warranty"[:30],
                pqty=-1,
                pprce=amount,
                pdisc=0,
                pext=amount * -1,
                pcogs=0,
                itype='N',
                gla='',
                gldpta='',
                txble='',
                rqty=rec_qty,
                iqty=0,
                loc=location,
                jobcod='',
                tskcod='',
                jqty=0,
                jamt=0,
                jrqty=0,
                cat='',
                note=0,
                line=0
            )

            self.db_session.add(warr_line)
            line_count += 1
            subtotal += (amount * -1)

        # Process notes
        for note in notes:
            note_line = BKAPPOL(
                ponm=self.po_number,
                erd=datetime(2001, 1, 1).date(),
                msg=note[:45],
                pcode=note[:15],
                pdesc=note[:30],
                pqty=0,
                pprce=0,
                pdisc=0,
                pext=0,
                pcogs=0,
                itype='X',
                gla='',
                gldpta='',
                txble='',
                rqty=0,
                iqty=0,
                loc='',
                jobcod='',
                tskcod='',
                jqty=0,
                jamt=0,
                jrqty=0,
                cat='',
                note=0,
                line=0
            )

            self.db_session.add(note_line)
            line_count += 1

        self.db_session.flush()
        return line_count, subtotal

    def _update_po_header(self, data: Dict[str, Any], line_count: int,
                         subtotal: float, total: float):
        """Update PO header with totals"""
        po_header = self._get_po_header(self.po_number)
        if not po_header:
            raise PurchaseOrderError(
                POErrorCode.UPDATE_HEADER_FAILED,
                po_number=self.po_number
            )

        # Lock the header row before updating
        self._lock_row(self.company_database, 'dbo', 'BKAPPO', po_header.record)

        po_header.nl = line_count
        po_header.subtot = subtotal
        po_header.total = total
        po_header.termd = data['billinfo'].get('termsDesc', '')[:10]
        po_header.termnm = data['billinfo'].get('termsNum', 0)
        po_header.shpnme = data['shipinfo'].get('name', '')[:30]
        po_header.shpa1 = data['shipinfo'].get('addr', '')[:30]
        po_header.shpa2 = data['shipinfo'].get('addr2', '')[:30]
        po_header.shpcty = data['shipinfo'].get('city', '')[:15]
        po_header.shpst = data['shipinfo'].get('state', '')[:2]
        po_header.shpzip = data['shipinfo'].get('zip', '')[:10]
        po_header.shpctry = data['shipinfo'].get('country', '')[:30]

        # Update ERD
        BKPOERD = self._get_model('BKPOERD')
        erd_record = self.db_session.query(BKPOERD).filter_by(
            num=self.po_number
        ).first()
        if erd_record:
            # Lock ERD row before updating
            self._lock_row(self.company_database, 'dbo', 'BKPOERD', erd_record.record)
            erd_record.erd = data.get('erd', datetime.now().date())

        # Create or update po_details
        po_details_model = self._get_model('po_details')
        po_details = self.db_session.query(po_details_model).filter_by(
            po_num=self.po_number
        ).first()

        if not po_details:
            po_details = po_details_model(
                po_num=self.po_number,
                vendor_inv=data['billinfo'].get('vendorInv', '')[:50],
                shipment_id=data['billinfo'].get('shipmentID', '')[:100],
                notes=data['billinfo'].get('note', '')[:255]
            )
            self.db_session.add(po_details)
        else:
            po_details.vendor_inv = data['billinfo'].get('vendorInv', '')[:50]
            po_details.shipment_id = data['billinfo'].get('shipmentID', '')[:100]
            po_details.notes = data['billinfo'].get('note', '')[:255]

        self.db_session.flush()

        # Update line ERDs from header
        self._update_line_item_erd()

    def _get_po_header(self, po_number: int):
        """Get PO header record"""
        # Company must be set before calling this
        if not self.company_database:
            raise PurchaseOrderError(
                POErrorCode.VALIDATE_PO_FAILED,
                additional_info="Company must be set before accessing PO"
            )

        BKAPPO = self._get_model('BKAPPO')
        return self.db_session.query(BKAPPO).filter_by(
            num=po_number
        ).first()

    def _get_po_lines(self, po_number: int):
        """Get all lines for a PO"""
        BKAPPOL = self._get_model('BKAPPOL')
        return self.db_session.query(BKAPPOL).filter_by(
            ponm=po_number
        ).all()

    def _empty_po(self, po_number: int, location: str):
        """Empty PO lines and restore inventory"""
        lines = self._get_po_lines(po_number)
        BKICLOC = self._get_model('BKICLOC')

        for line in lines:
            # Skip note lines
            if line.itype == 'X':
                self.db_session.delete(line)
                continue

            # Restore UOO for inventory items
            if line.itype == 'R' and line.pqty > 0:
                icloc = self.db_session.query(BKICLOC).filter_by(
                    code=location,
                    prod=line.pcode
                ).first()

                if icloc:
                    # Lock inventory row before updating
                    self._lock_row(self.company_database, 'dbo', 'BKICLOC', icloc.record)
                    icloc.uoo -= line.pqty

            # Delete line
            self.db_session.delete(line)

        self.db_session.flush()

    def _log_operation(self, data: Dict[str, Any], action: str):
        """Log PO operation"""
        log_entry = JADVDATA_dbo_po_log(
            po_number=self.po_number,
            from_=data.get('from', ''),
            vendid=data.get('vendid', ''),
            to=data.get('to', ''),
            for_=data.get('for', ''),
            user=data.get('user', ''),
            action=action,
            querys='\r'.join(self.queries)[:65535] if self.queries else '',
            errors='\r'.join(self.errors)[:65535] if self.errors else '',
            json=str(data)[:65535],
            date=datetime.now()
        )
        self.db_session.add(log_entry)
        self.db_session.flush()

    def _fix_part_numbers(self, data: Dict[str, Any]):
        """Replace underscores with dots in part numbers"""
        if 'line_items' in data and data['line_items']:
            new_line_items = {}
            for part_key, part_data in data['line_items'].items():
                new_key = part_key.replace('_', '.')
                new_line_items[new_key] = part_data
            data['line_items'] = new_line_items

        if 'warr_items' in data and data['warr_items']:
            new_warr_items = {}
            for part_key, warr_data in data['warr_items'].items():
                new_key = part_key.replace('_', '.')
                new_warr_items[new_key] = warr_data
            data['warr_items'] = new_warr_items

    def _update_line_item_erd(self):
        """Update line item ERD from header ERD for current PO"""
        # Get the ERD record for this PO
        BKPOERD = self._get_model('BKPOERD')
        erd_record = self.db_session.query(BKPOERD).filter_by(
            num=self.po_number
        ).first()

        if erd_record and erd_record.erd and erd_record.erd.year >= 2015:
            # Update all lines for this PO only
            BKAPPOL = self._get_model('BKAPPOL')
            self.db_session.query(BKAPPOL).filter_by(
                ponm=self.po_number
            ).update({
                'erd': erd_record.erd
            })
            self.db_session.flush()

    def _validate_location(self, location: str) -> bool:
        """Validate location is a valid warehouse, rad shop, or CON"""
        loc_record = self.db_session.query(JADVDATA_dbo_locations).filter(
            and_(
                or_(
                    JADVDATA_dbo_locations.warehouse == 1,
                    JADVDATA_dbo_locations.rad_shop == 1,
                ),
                JADVDATA_dbo_locations.active == 1,
                JADVDATA_dbo_locations.location == location
            )
        ).first()

        return loc_record is not None


    def get_po(self,company: str, po_number: int, check_historical: bool = True) -> Dict[str, Any]:
        """
        Get PO from active and/or historical tables
        Handles partially received POs where some lines may be historical

        Args:
            po_number: PO number to retrieve
            check_historical: If True, check historical tables for lines

        Returns:
            Dict with PO header, lines (from both tables), erd, and details records
        """
        try:
            self._set_company(company)

            self.po_number = po_number

            # Get all model references
            BKAPPO = self._get_model('BKAPPO')
            BKAPPOL = self._get_model('BKAPPOL')
            BKAPHPO = self._get_model('BKAPHPO')
            BKAPHPOL = self._get_model('BKAPHPOL')
            BKPOERD = self._get_model('BKPOERD')
            po_details_model = self._get_model('po_details')

            # Try to find header in active table first
            header = self.db_session.query(BKAPPO).filter(
                BKAPPO.num == po_number
            ).first()

            header_is_active = True
            
            # If not in active, check historical
            if not header and check_historical:
                header = self.db_session.query(BKAPHPO).filter(
                    BKAPHPO.num == po_number
                ).first()
                header_is_active = False

            if not header:
                # Not found
                return {
                    'success': False,
                    'error_code': POErrorCode.INVALID_PO_NUMBER,
                    'error_message': f"PO {po_number} not found in {self.company_database}",
                    'po_number': po_number,
                    'company': self.company_database
                }

            # Get lines from BOTH active and historical tables
            all_lines = []
            
            # Get active lines
            active_lines = self.db_session.query(BKAPPOL).filter(
                BKAPPOL.ponm == po_number
            ).order_by(BKAPPOL.record).all()
            
            # Add source info to active lines
            for line in active_lines:
                line._source = "active"
                all_lines.append(line)
            
            # Get historical lines if checking historical
            if check_historical:
                historical_lines = self.db_session.query(BKAPHPOL).filter(
                    BKAPHPOL.ponm == po_number
                ).order_by(BKAPHPOL.record).all()
                
                # Add source info to historical lines
                for line in historical_lines:
                    line._source = "historical"
                    all_lines.append(line)
            
            # Sort all lines by record number to maintain order
            #from pprint import pprint
            #pprint(all_lines)
            all_lines.sort(key=lambda x: x.record)

            # Get ERD - always from active table as it doesn't get archived
            erd = self.db_session.query(BKPOERD).filter(
                BKPOERD.num == po_number
            ).first()

            # Get po_details - also always from active table
            details = self.db_session.query(po_details_model).filter(
                po_details_model.po_num == po_number
            ).first()

            # Count lines by type
            active_line_count = sum(1 for line in all_lines if line._source == "active")
            historical_line_count = sum(1 for line in all_lines if line._source == "historical")
            
            # Determine if PO is partially received
            is_partially_received = active_line_count > 0 and historical_line_count > 0

            return {
                'success': True,
                'company': self.company_database,
                'po_number': po_number,
                'source_info': {
                    'is_active': header_is_active,
                    'has_active_lines': active_line_count > 0,
                    'has_historical_lines': historical_line_count > 0,
                    'is_partially_received': is_partially_received,
                    'active_line_count': active_line_count,
                    'historical_line_count': historical_line_count
                },
                'header': header,
                'lines': all_lines,
                'erd': erd,
                'details': details,
                'line_count': len(all_lines),
                'po_total': header.total,
                'po_subtotal': header.subtot,
                'freight': header.frght,
                'order_date': header.orddte,
                'vendor_code': header.vndcod,
                'location': header.loc,
                'printed': header.prtd == 'Y'
            }

        except Exception as e:
            logger.exception(f"Error retrieving PO {po_number}")
            return {
                'success': False,
                'error_code': POErrorCode.MSSQL_QUERY_FAILED,
                'error_message': str(e),
                'po_number': po_number,
                'company': self.company_database
            }

    def get_historical_po(self, company, po_number):
        """Get historical PO from BKAPHPO/BKAPHPOL tables"""

        return self.get_po(company, po_number, check_historical = True)

    def validate_po_items(self, company: str, location: str, line_items: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate PO items without creating a PO
        
        Args:
            company: Company (PACIFIC or CANADA)
            location: Location to validate against
            line_items: Dict of items to validate
            
        Returns:
            Dict with validation results
        """
        try:
            # Set company
            self._set_company(company)
            
            # Clear any previous errors
            self.errors = []
            
            # Validate the items
            validated_items = self._validate_po(location, line_items)
            
            # Count valid items
            valid_count = sum(1 for item in validated_items.values() if item['valid'])
            invalid_count = len(line_items) - valid_count
            
            return {
                'success': True,
                'validated_items': validated_items,
                'valid_count': valid_count,
                'invalid_count': invalid_count,
                'total_count': len(line_items),
                'errors': self.errors,
                'all_valid': valid_count == len(line_items)
            }
            
        except Exception as e:
            logger.exception("Error validating PO items")
            return {
                'success': False,
                'error_message': str(e),
                'errors': self.errors
            }

    def get_po_details(self, company: str, po_number: int) -> Dict[str, Any]:
        """
        Get formatted PO details for API response
        
        Args:
            company: Company (PACIFIC or CANADA)
            po_number: PO number to retrieve
            
        Returns:
            Dict with formatted PO details
        """
        try:
            # Get the PO using existing method
            result = self.get_po(company, po_number, check_historical=True)
            
            if not result['success']:
                return result
            
            # Format the response for API
            header = result['header']
            lines = result['lines']
            erd = result['erd']
            details = result['details']
            source_info = result['source_info']
            
            formatted_response = {
                'success': True,
                'po_number': po_number,
                'company': company,
                'source_info': source_info,
                'header': {
                    'vendor_code': header.vndcod,
                    'vendor_name': header.vndnme,
                    'location': header.loc,
                    'order_date': header.orddte.isoformat() if header.orddte else None,
                    'printed': header.prtd == 'Y',
                    'subtotal': float(header.subtot),
                    'freight': float(header.frght),
                    'total': float(header.total),
                    'tax_amount': float(header.taxamt),
                    'line_count': header.nl,
                    'entered_by': header.entby,
                    'ship_via': header.shpvia,
                    'terms': header.termd,
                    'billing': {
                        'name': header.vndnme,
                        'address1': header.vnda1,
                        'address2': header.vnda2,
                        'city': header.vndcty,
                        'state': header.vndst,
                        'zip': header.vndzip,
                        'country': header.vndctry
                    },
                    'shipping': {
                        'code': header.shpcod,
                        'name': header.shpnme,
                        'address1': header.shpa1,
                        'address2': header.shpa2,
                        'city': header.shpcty,
                        'state': header.shpst,
                        'zip': header.shpzip,
                        'country': header.shpctry,
                        'attention': header.shpatn
                    }
                },
                'lines': [
                    {
                        '_source': getattr(line, '_source', 'active'),
                        'line_id': line.record,
                        'part': line.pcode.strip(),
                        'description': line.pdesc.strip(),
                        'message': line.msg.strip(),
                        'quantity': float(line.pqty),
                        'price': float(line.pprce),
                        'discount': float(line.pdisc),
                        'extended': float(line.pext),
                        'type': line.itype,
                        'taxable': line.txble == 'Y',
                        'received_qty': float(line.rqty),
                        'invoiced_qty': float(line.iqty),
                        'location': line.loc,
                        'erd': line.erd.isoformat() if line.erd and line.erd.year > 2001 else None
                    }
                    for line in lines
                ],
                'expected_receipt_date': erd.erd.isoformat() if erd and erd.erd else None,
                'additional_details': {
                    'vendor_invoice': details.vendor_inv if details else None,
                    'shipment_id': details.shipment_id if details else None,
                    'notes': details.notes if details else None
                } if details else None
            }
            
            return formatted_response
            
        except Exception as e:
            logger.exception(f"Error getting PO details for {po_number}")
            return {
                'success': False,
                'error_code': POErrorCode.MSSQL_QUERY_FAILED,
                'error_message': str(e)
            }

    def validate_po_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate PO data structure without saving
        
        Args:
            data: PO data to validate
            
        Returns:
            Dict with validation results
        """
        errors = []
        warnings = []
        
        try:
            # Check if it's a new or existing PO
            is_new = not data.get('id')
            
            # Check required fields based on operation
            if is_new:
                required_fields = ['company', 'from', 'to', 'vendid', 'line_items', 'billinfo', 'shipinfo']
            else:
                required_fields = ['id', 'company']
            
            for field in required_fields:
                if field not in data or not data[field]:
                    errors.append(f"Missing required field: {field}")
            
            # Validate company
            if 'company' in data:
                company = data['company'].upper()
                if company not in ['PACIFIC', 'CANADA']:
                    errors.append("Invalid company. Must be PACIFIC or CANADA")
            
            # Validate line items if present
            if 'line_items' in data:
                line_items = data['line_items']
                if not isinstance(line_items, dict):
                    errors.append("line_items must be a dictionary")
                elif not line_items:
                    errors.append("At least one line item is required")
                else:
                    for part, item_data in line_items.items():
                        if not isinstance(item_data, dict):
                            errors.append(f"Invalid data for part {part}")
                            continue
                            
                        # Check line item fields
                        if not item_data.get('ord_qty'):
                            warnings.append(f"Part {part} has no order quantity")
                        if not item_data.get('price'):
                            warnings.append(f"Part {part} has no price")
                        
                        # Validate numeric fields
                        for field in ['ord_qty', 'rec_qty', 'price', 'extended']:
                            if field in item_data:
                                try:
                                    float(item_data[field])
                                except (ValueError, TypeError):
                                    errors.append(f"Part {part}: {field} must be numeric")
            
            # Validate locations
            if data.get('from') and data.get('to'):
                if data['from'] == data['to']:
                    errors.append("From and To locations cannot be the same")
            
            # Validate dates
            if 'erd' in data and data['erd']:
                if isinstance(data['erd'], str):
                    try:
                        datetime.strptime(data['erd'], '%Y-%m-%d')
                    except ValueError:
                        errors.append("ERD must be in YYYY-MM-DD format")
            
            # Validate freight
            if 'freight' in data and data['freight']:
                try:
                    float(data['freight'])
                except (ValueError, TypeError):
                    errors.append("Freight must be numeric")
            
            return {
                'success': len(errors) == 0,
                'valid': len(errors) == 0,
                'errors': errors,
                'warnings': warnings
            }
            
        except Exception as e:
            logger.exception("Error validating PO data")
            return {
                'success': False,
                'valid': False,
                'errors': [f"Validation error: {str(e)}"]
            }