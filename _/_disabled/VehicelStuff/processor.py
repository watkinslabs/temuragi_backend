#!/usr/bin/env python3
"""
Parts Data Processor Service
BSD 3-Clause License
"""

import uuid
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import or_

# Import the models from the schema file
from .normalized_parts_schema import (
    Part, PartAlias, Vehicle, PartVehicle, Repairer, RepairerAddress,
    RepairerContact, RepairerUser, Quote, QuoteVehicle, QuotePart
)


class parts_data_processor:
    """Service to process and normalize parts data from JSON quotes"""
    
    def __init__(self, db_session: Session):
        self.session = db_session
    
    def process_quote_json(self, quote_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process complete quote JSON and populate normalized tables
        Returns summary of created/updated records
        """
        results = {
            'parts_created': 0,
            'parts_updated': 0,
            'vehicles_created': 0,
            'vehicles_updated': 0,
            'repairers_created': 0,
            'repairers_updated': 0,
            'quotes_created': 0,
            'aliases_created': 0,
            'part_vehicles_created': 0
        }
        
        try:
            # Process repairer first
            repairer = self._process_repairer(quote_data.get('repairer', {}))
            if repairer:
                results['repairers_created'] += 1
            
            # Process vehicle
            vehicle = self._process_vehicle(quote_data.get('vehicle', {}))
            if vehicle:
                results['vehicles_created'] += 1
            
            # Process quote
            quote = self._process_quote(quote_data, repairer)
            if quote:
                results['quotes_created'] += 1
            
            # Process parts and relationships
            for part_data in quote_data.get('requestedParts', []):
                part_results = self._process_part_with_relationships(
                    part_data, vehicle, quote
                )
                results['parts_created'] += part_results['part_created']
                results['aliases_created'] += part_results['aliases_created']
                results['part_vehicles_created'] += part_results['part_vehicle_created']
            
            self.session.commit()
            
        except Exception as e:
            self.session.rollback()
            raise e
        
        return results
    
    def _process_repairer(self, repairer_data: Dict[str, Any]) -> Optional[Repairer]:
        """Process repairer data and create/update repairer record"""
        if not repairer_data:
            return None
        
        display_id = repairer_data.get('repairerDisplayId')
        name = repairer_data.get('name')
        
        if not name:
            return None
        
        # Check if repairer exists
        repairer = None
        if display_id:
            repairer = self.session.query(Repairer).filter_by(display_id=display_id).first()
        
        if not repairer:
            repairer = self.session.query(Repairer).filter_by(name=name).first()
        
        if not repairer:
            repairer = Repairer(
                uuid=uuid.uuid4(),
                name=name,
                display_id=display_id,
                is_active=True
            )
            self.session.add(repairer)
            self.session.flush()  # Get the UUID
        
        # Process address if provided
        address_data = repairer_data.get('address', {})
        if address_data and address_data.get('address'):
            self._process_repairer_address(repairer, address_data)
        
        # Process phone if provided
        phone = repairer_data.get('phoneNumber')
        if phone:
            self._process_repairer_contact(repairer, 'phone', phone, 'main')
        
        return repairer
    
    def _process_repairer_address(self, repairer: Repairer, address_data: Dict[str, Any]):
        """Process repairer address"""
        address_line_1 = address_data.get('address')
        if not address_line_1:
            return
        
        # Check if address already exists
        existing_address = self.session.query(RepairerAddress).filter_by(
            repairer_uuid=repairer.uuid,
            address_line_1=address_line_1
        ).first()
        
        if not existing_address:
            address = RepairerAddress(
                uuid=uuid.uuid4(),
                repairer_uuid=repairer.uuid,
                address_type='business',
                address_line_1=address_line_1,
                address_line_2=address_data.get('address2', ''),
                city=address_data.get('city', ''),
                state_province=address_data.get('stateProvince', ''),
                postal_code=address_data.get('postalCode', ''),
                country_code=address_data.get('countryCode', 'US'),
                is_primary=True,
                is_active=True
            )
            self.session.add(address)
    
    def _process_repairer_contact(self, repairer: Repairer, contact_type: str, 
                                 contact_value: str, label: str):
        """Process repairer contact information"""
        # Check if contact already exists
        existing_contact = self.session.query(RepairerContact).filter_by(
            repairer_uuid=repairer.uuid,
            contact_type=contact_type,
            contact_value=contact_value
        ).first()
        
        if not existing_contact:
            contact = RepairerContact(
                uuid=uuid.uuid4(),
                repairer_uuid=repairer.uuid,
                contact_type=contact_type,
                contact_value=contact_value,
                label=label,
                is_primary=True,
                is_active=True
            )
            self.session.add(contact)
    
    def _process_vehicle(self, vehicle_data: Dict[str, Any]) -> Optional[Vehicle]:
        """Process vehicle data and create/update vehicle record"""
        if not vehicle_data:
            return None
        
        year = vehicle_data.get('yearInteger')
        make = vehicle_data.get('make')
        model = vehicle_data.get('model')
        sub_model = vehicle_data.get('subModel')
        
        if not all([year, make, model]):
            return None
        
        # Check if vehicle exists
        vehicle = self.session.query(Vehicle).filter_by(
            year=year,
            make=make,
            model=model,
            sub_model=sub_model
        ).first()
        
        if not vehicle:
            vehicle = Vehicle(
                uuid=uuid.uuid4(),
                year=year,
                make=make,
                model=model,
                sub_model=sub_model,
                body_style=vehicle_data.get('type'),
                country_market='US',
                is_active=True
            )
            self.session.add(vehicle)
            self.session.flush()
        
        return vehicle
    
    def _process_quote(self, quote_data: Dict[str, Any], repairer: Repairer) -> Optional[Quote]:
        """Process quote data"""
        quote_invitation_id = quote_data.get('quoteInvitationId')
        if not quote_invitation_id or not repairer:
            return None
        
        # Check if quote exists
        quote = self.session.query(Quote).filter_by(
            quote_invitation_id=quote_invitation_id
        ).first()
        
        if not quote:
            quote = Quote(
                uuid=uuid.uuid4(),
                quote_invitation_id=quote_invitation_id,
                request_id=quote_data.get('requestId', ''),
                repairer_uuid=repairer.uuid,
                supplier_name=quote_data.get('supplier', {}).get('name'),
                status=quote_data.get('status', 'open').lower(),
                currency_code=quote_data.get('currencyCode', 'USD'),
                is_at_risk=quote_data.get('isAtRiskOfTotalLoss', False),
                is_insurer_mandated=quote_data.get('isInsurerMandated', False),
                transaction_fee_percentage=Decimal(str(quote_data.get('indicativeTransactionFeePercentage', 0.0)))
            )
            
            # Parse dates
            if quote_data.get('dateExpectedToClose'):
                try:
                    quote.date_expected_close = datetime.fromisoformat(
                        quote_data['dateExpectedToClose'].replace('Z', '+00:00')
                    )
                except:
                    pass
            
            if quote_data.get('datePartsRequiredBy'):
                try:
                    quote.date_parts_required = datetime.fromisoformat(
                        quote_data['datePartsRequiredBy'].replace('Z', '+00:00')
                    )
                except:
                    pass
            
            self.session.add(quote)
            self.session.flush()
        
        return quote
    
    def _process_part_with_relationships(self, part_data: Dict[str, Any], 
                                       vehicle: Optional[Vehicle], 
                                       quote: Optional[Quote]) -> Dict[str, int]:
        """Process part and create all related records"""
        results = {
            'part_created': 0,
            'aliases_created': 0,
            'part_vehicle_created': 0
        }
        
        part_number = part_data.get('requestedPartNumber')
        if not part_number:
            return results
        
        # Check if part exists
        part = self.session.query(Part).filter_by(part_number=part_number).first()
        
        if not part:
            part = Part(
                uuid=uuid.uuid4(),
                part_number=part_number,
                description=part_data.get('description', ''),
                condition_type=part_data.get('estimatePartConditionType'),
                hollander_type=part_data.get('partClassifications', {}).get('hollanderType'),
                cieca_code=part_data.get('partClassifications', {}).get('cieca'),
                is_active=True
            )
            
            # Try to parse base price
            try:
                price_str = part_data.get('estimateUnitPrice', '0')
                if price_str:
                    part.base_price = Decimal(str(price_str))
            except:
                part.base_price = Decimal('0')
            
            # Extract category from description
            desc = part_data.get('description', '').upper()
            if 'FRONT' in desc:
                if 'LAMP' in desc or 'LIGHT' in desc:
                    part.category = 'lighting'
                    part.subcategory = 'headlamp'
                elif 'DOOR' in desc:
                    part.category = 'body'
                    part.subcategory = 'door'
                elif 'FENDER' in desc:
                    part.category = 'body'
                    part.subcategory = 'fender'
            
            self.session.add(part)
            self.session.flush()
            results['part_created'] = 1
        
        # Process aliases
        aliases = part_data.get('partNumberAlias', {})
        
        # OEM aliases
        for oem_alias in aliases.get('oem', []):
            if self._create_part_alias(part, oem_alias, 'OEM'):
                results['aliases_created'] += 1
        
        # Hollander interchange codes
        for hollander_code in aliases.get('hollanderInterchangeCode', []):
            if hollander_code != 'OTHER' and self._create_part_alias(part, hollander_code, 'HOLLANDER'):
                results['aliases_created'] += 1
        
        # Create part-vehicle relationship
        if vehicle and self._create_part_vehicle_relationship(part, vehicle):
            results['part_vehicle_created'] = 1
        
        # Create quote part record
        if quote:
            self._create_quote_part(quote, part, part_data)
        
        return results
    
    def _create_part_alias(self, part: Part, alias_number: str, alias_type: str) -> bool:
        """Create part alias if it doesn't exist"""
        existing_alias = self.session.query(PartAlias).filter_by(
            part_uuid=part.uuid,
            alias_number=alias_number,
            alias_type=alias_type
        ).first()
        
        if not existing_alias:
            alias = PartAlias(
                uuid=uuid.uuid4(),
                part_uuid=part.uuid,
                alias_number=alias_number,
                alias_type=alias_type
            )
            self.session.add(alias)
            return True
        return False
    
    def _create_part_vehicle_relationship(self, part: Part, vehicle: Vehicle) -> bool:
        """Create part-vehicle relationship if it doesn't exist"""
        existing_rel = self.session.query(PartVehicle).filter_by(
            part_uuid=part.uuid,
            vehicle_uuid=vehicle.uuid
        ).first()
        
        if not existing_rel:
            part_vehicle = PartVehicle(
                uuid=uuid.uuid4(),
                part_uuid=part.uuid,
                vehicle_uuid=vehicle.uuid,
                verified=False
            )
            self.session.add(part_vehicle)
            return True
        return False
    
    def _create_quote_part(self, quote: Quote, part: Part, part_data: Dict[str, Any]):
        """Create quote part record"""
        # Check if quote part already exists
        existing_quote_part = self.session.query(QuotePart).filter_by(
            quote_uuid=quote.uuid,
            part_uuid=part.uuid,
            requested_part_id=part_data.get('requestedPartId')
        ).first()
        
        if not existing_quote_part:
            quote_part = QuotePart(
                uuid=uuid.uuid4(),
                quote_uuid=quote.uuid,
                part_uuid=part.uuid,
                requested_part_id=part_data.get('requestedPartId'),
                quantity=part_data.get('quantity', 1),
                condition_override=part_data.get('estimatePartConditionType'),
                comment=part_data.get('comment'),
                is_filtered=part_data.get('isPartFiltered', False)
            )
            
            # Parse prices
            try:
                unit_price = part_data.get('estimateUnitPrice')
                if unit_price:
                    quote_part.unit_price = Decimal(str(unit_price))
                    quote_part.total_price = quote_part.unit_price * quote_part.quantity
            except:
                pass
            
            self.session.add(quote_part)


class parts_lookup_service:
    """Service for looking up parts from normalized tables"""
    
    def __init__(self, db_session: Session):
        self.session = db_session
    
    def find_part_by_number(self, part_number: str) -> Optional[Part]:
        """Find part by exact part number or alias"""
        # Try exact match first
        part = self.session.query(Part).filter_by(part_number=part_number).first()
        
        if not part:
            # Try alias lookup
            alias = self.session.query(PartAlias).filter_by(alias_number=part_number).first()
            if alias:
                part = alias.part
        
        return part
    
    def find_parts_for_vehicle(self, year: int, make: str, model: str, 
                              sub_model: Optional[str] = None) -> List[Part]:
        """Find all parts that fit a specific vehicle"""
        vehicle_query = self.session.query(Vehicle).filter_by(
            year=year,
            make=make,
            model=model
        )
        
        if sub_model:
            vehicle_query = vehicle_query.filter_by(sub_model=sub_model)
        
        vehicles = vehicle_query.all()
        
        if not vehicles:
            return []
        
        vehicle_uuids = [v.uuid for v in vehicles]
        
        part_vehicles = self.session.query(PartVehicle).filter(
            PartVehicle.vehicle_uuid.in_(vehicle_uuids)
        ).all()
        
        part_uuids = [pv.part_uuid for pv in part_vehicles]
        
        parts = self.session.query(Part).filter(
            Part.uuid.in_(part_uuids),
            Part.is_active == True
        ).all()
        
        return parts
    
    def search_parts_by_description(self, search_term: str) -> List[Part]:
        """Search parts by description"""
        return self.session.query(Part).filter(
            Part.description.ilike(f'%{search_term}%'),
            Part.is_active == True
        ).all()
    
    def find_parts_by_hollander_type(self, hollander_type: str) -> List[Part]:
        """Find parts by Hollander type"""
        return self.session.query(Part).filter_by(
            hollander_type=hollander_type,
            is_active=True
        ).all()
    
    def get_part_vehicles(self, part_uuid: uuid.UUID) -> List[Vehicle]:
        """Get all vehicles that a part fits"""
        part_vehicles = self.session.query(PartVehicle).filter_by(
            part_uuid=part_uuid
        ).all()
        
        vehicle_uuids = [pv.vehicle_uuid for pv in part_vehicles]
        
        vehicles = self.session.query(Vehicle).filter(
            Vehicle.uuid.in_(vehicle_uuids),
            Vehicle.is_active == True
        ).all()
        
        return vehicles
    
    def get_part_aliases(self, part_uuid: uuid.UUID) -> List[PartAlias]:
        """Get all aliases for a part"""
        return self.session.query(PartAlias).filter_by(part_uuid=part_uuid).all()