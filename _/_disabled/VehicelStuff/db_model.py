#!/usr/bin/env python3
"""
Normalized Parts Database Schema
BSD 3-Clause License
"""

import uuid
import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer, Text, Index, UniqueConstraint, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.base.model import BaseModel


class Part(BaseModel):
    """
    Core parts table containing all part metadata
    """
    __tablename__ = 'parts'

    part_number = Column(String(100), nullable=False, unique=True,
                        comment="Primary part number identifier")
    description = Column(Text, nullable=False,
                        comment="Part description")
    condition_type = Column(String(10), nullable=True,
                          comment="Part condition (PAL, PAA, etc)")
    hollander_type = Column(String(20), nullable=True,
                          comment="Hollander classification type")
    cieca_code = Column(String(20), nullable=True,
                       comment="CIECA classification code")
    base_price = Column(Numeric(10, 2), nullable=True,
                       comment="Base price for part")
    weight_lbs = Column(Numeric(8, 2), nullable=True,
                       comment="Part weight in pounds")
    dimensions = Column(String(100), nullable=True,
                       comment="Part dimensions (LxWxH)")
    category = Column(String(50), nullable=True,
                     comment="Part category (engine, body, electrical, etc)")
    subcategory = Column(String(50), nullable=True,
                        comment="Part subcategory")
    manufacturer = Column(String(100), nullable=True,
                         comment="Original manufacturer")
    is_active = Column(Boolean, default=True, nullable=False,
                      comment="Whether part is active in catalog")

    # Relationships
    part_aliases = relationship("PartAlias", back_populates="part", cascade="all, delete-orphan")
    part_vehicles = relationship("PartVehicle", back_populates="part", cascade="all, delete-orphan")
    quote_parts = relationship("QuotePart", back_populates="part")

    __table_args__ = (
        Index('idx_parts_number', 'part_number'),
        Index('idx_parts_hollander', 'hollander_type'),
        Index('idx_parts_category', 'category'),
        Index('idx_parts_description', 'description'),
        Index('idx_parts_active', 'is_active'),
    )


class PartAlias(BaseModel):
    """
    Part number aliases and interchange codes
    """
    __tablename__ = 'part_aliases'

    part_uuid = Column(UUID(as_uuid=True),
                      ForeignKey('parts.uuid', name='fk_part_aliases_part'),
                      nullable=False,
                      comment="Reference to main part")
    alias_number = Column(String(100), nullable=False,
                         comment="Alias or interchange part number")
    alias_type = Column(String(20), nullable=False,
                       comment="Type of alias (OEM, HOLLANDER, AFTERMARKET)")
    source = Column(String(50), nullable=True,
                   comment="Source of alias (manufacturer, interchange guide)")

    # Relationships
    part = relationship("Part", back_populates="part_aliases")

    __table_args__ = (
        Index('idx_part_aliases_part', 'part_uuid'),
        Index('idx_part_aliases_number', 'alias_number'),
        Index('idx_part_aliases_type', 'alias_type'),
        UniqueConstraint('part_uuid', 'alias_number', 'alias_type', name='uq_part_aliases_unique'),
    )


class Vehicle(BaseModel):
    """
    Vehicle information table
    """
    __tablename__ = 'vehicles'

    year = Column(Integer, nullable=False,
                 comment="Vehicle year")
    make = Column(String(50), nullable=False,
                 comment="Vehicle make")
    model = Column(String(100), nullable=False,
                  comment="Vehicle model")
    sub_model = Column(String(100), nullable=True,
                      comment="Vehicle sub-model or trim")
    body_style = Column(String(50), nullable=True,
                       comment="Body style (sedan, coupe, truck, etc)")
    engine = Column(String(100), nullable=True,
                   comment="Engine specification")
    transmission = Column(String(50), nullable=True,
                         comment="Transmission type")
    drive_type = Column(String(20), nullable=True,
                       comment="Drive type (FWD, RWD, AWD)")
    fuel_type = Column(String(20), nullable=True,
                      comment="Fuel type (gas, diesel, hybrid, electric)")
    country_market = Column(String(10), default='US', nullable=False,
                           comment="Market country code")
    is_active = Column(Boolean, default=True, nullable=False,
                      comment="Whether vehicle is active in system")

    # Relationships
    part_vehicles = relationship("PartVehicle", back_populates="vehicle", cascade="all, delete-orphan")
    quote_vehicles = relationship("QuoteVehicle", back_populates="vehicle")

    __table_args__ = (
        Index('idx_vehicles_year', 'year'),
        Index('idx_vehicles_make', 'make'),
        Index('idx_vehicles_model', 'model'),
        Index('idx_vehicles_make_model', 'make', 'model'),
        Index('idx_vehicles_year_make_model', 'year', 'make', 'model'),
        Index('idx_vehicles_active', 'is_active'),
        UniqueConstraint('year', 'make', 'model', 'sub_model', 'engine', 'body_style', name='uq_vehicles_unique'),
    )


class PartVehicle(BaseModel):
    """
    Many-to-many relationship between parts and vehicles
    """
    __tablename__ = 'part_vehicles'

    part_uuid = Column(UUID(as_uuid=True),
                      ForeignKey('parts.uuid', name='fk_part_vehicles_part'),
                      nullable=False,
                      comment="Reference to part")
    vehicle_uuid = Column(UUID(as_uuid=True),
                         ForeignKey('vehicles.uuid', name='fk_part_vehicles_vehicle'),
                         nullable=False,
                         comment="Reference to vehicle")
    fitment_notes = Column(Text, nullable=True,
                          comment="Special fitment notes or requirements")
    position = Column(String(20), nullable=True,
                     comment="Position on vehicle (left, right, front, rear)")
    verified = Column(Boolean, default=False, nullable=False,
                     comment="Whether fitment has been verified")
    verification_source = Column(String(100), nullable=True,
                               comment="Source of fitment verification")

    # Relationships
    part = relationship("Part", back_populates="part_vehicles")
    vehicle = relationship("Vehicle", back_populates="part_vehicles")

    __table_args__ = (
        Index('idx_part_vehicles_part', 'part_uuid'),
        Index('idx_part_vehicles_vehicle', 'vehicle_uuid'),
        Index('idx_part_vehicles_verified', 'verified'),
        UniqueConstraint('part_uuid', 'vehicle_uuid', 'position', name='uq_part_vehicles_unique'),
    )


class Repairer(BaseModel):
    """
    Repairer/shop information
    """
    __tablename__ = 'repairers'

    name = Column(String(200), nullable=False,
                 comment="Repairer business name")
    display_id = Column(String(50), nullable=True,
                       comment="External display ID")
    business_type = Column(String(50), nullable=True,
                          comment="Type of business (collision, mechanical, etc)")
    license_number = Column(String(100), nullable=True,
                           comment="Business license number")
    tax_id = Column(String(50), nullable=True,
                   comment="Tax ID or EIN")
    website = Column(String(200), nullable=True,
                    comment="Business website URL")
    is_active = Column(Boolean, default=True, nullable=False,
                      comment="Whether repairer is active")
    certification_level = Column(String(50), nullable=True,
                               comment="Certification level or rating")

    # Relationships
    addresses = relationship("RepairerAddress", back_populates="repairer", cascade="all, delete-orphan")
    contacts = relationship("RepairerContact", back_populates="repairer", cascade="all, delete-orphan")
    users = relationship("RepairerUser", back_populates="repairer", cascade="all, delete-orphan")
    quotes = relationship("Quote", back_populates="repairer")

    __table_args__ = (
        Index('idx_repairers_name', 'name'),
        Index('idx_repairers_display_id', 'display_id'),
        Index('idx_repairers_active', 'is_active'),
        Index('idx_repairers_type', 'business_type'),
    )


class RepairerAddress(BaseModel):
    """
    Repairer addresses (can have multiple)
    """
    __tablename__ = 'repairer_addresses'

    repairer_uuid = Column(UUID(as_uuid=True),
                          ForeignKey('repairers.uuid', name='fk_repairer_addresses_repairer'),
                          nullable=False,
                          comment="Reference to repairer")
    address_type = Column(String(20), default='business', nullable=False,
                         comment="Type of address (business, billing, shipping)")
    address_line_1 = Column(String(200), nullable=False,
                           comment="Primary address line")
    address_line_2 = Column(String(200), nullable=True,
                           comment="Secondary address line")
    city = Column(String(100), nullable=False,
                 comment="City")
    state_province = Column(String(50), nullable=False,
                           comment="State or province")
    postal_code = Column(String(20), nullable=False,
                        comment="Postal or ZIP code")
    country_code = Column(String(3), default='US', nullable=False,
                         comment="ISO country code")
    is_primary = Column(Boolean, default=False, nullable=False,
                       comment="Whether this is the primary address")
    is_active = Column(Boolean, default=True, nullable=False,
                      comment="Whether address is active")

    # Relationships
    repairer = relationship("Repairer", back_populates="addresses")

    __table_args__ = (
        Index('idx_repairer_addresses_repairer', 'repairer_uuid'),
        Index('idx_repairer_addresses_type', 'address_type'),
        Index('idx_repairer_addresses_primary', 'is_primary'),
        Index('idx_repairer_addresses_city_state', 'city', 'state_province'),
    )


class RepairerContact(BaseModel):
    """
    Repairer contact information (phones, emails, etc)
    """
    __tablename__ = 'repairer_contacts'

    repairer_uuid = Column(UUID(as_uuid=True),
                          ForeignKey('repairers.uuid', name='fk_repairer_contacts_repairer'),
                          nullable=False,
                          comment="Reference to repairer")
    contact_type = Column(String(20), nullable=False,
                         comment="Type of contact (phone, email, fax)")
    contact_value = Column(String(200), nullable=False,
                          comment="Contact value (phone number, email address)")
    label = Column(String(50), nullable=True,
                  comment="Label for contact (main, billing, emergency)")
    is_primary = Column(Boolean, default=False, nullable=False,
                       comment="Whether this is the primary contact for type")
    is_active = Column(Boolean, default=True, nullable=False,
                      comment="Whether contact is active")

    # Relationships
    repairer = relationship("Repairer", back_populates="contacts")

    __table_args__ = (
        Index('idx_repairer_contacts_repairer', 'repairer_uuid'),
        Index('idx_repairer_contacts_type', 'contact_type'),
        Index('idx_repairer_contacts_primary', 'is_primary'),
        Index('idx_repairer_contacts_value', 'contact_value'),
    )


class RepairerUser(BaseModel):
    """
    Users associated with repairers
    """
    __tablename__ = 'repairer_users'

    repairer_uuid = Column(UUID(as_uuid=True),
                          ForeignKey('repairers.uuid', name='fk_repairer_users_repairer'),
                          nullable=False,
                          comment="Reference to repairer")
    first_name = Column(String(100), nullable=False,
                       comment="User first name")
    last_name = Column(String(100), nullable=False,
                      comment="User last name")
    email = Column(String(200), nullable=False,
                  comment="User email address")
    phone = Column(String(20), nullable=True,
                  comment="User phone number")
    role = Column(String(50), nullable=True,
                 comment="User role at repairer")
    department = Column(String(100), nullable=True,
                       comment="User department")
    is_primary_contact = Column(Boolean, default=False, nullable=False,
                               comment="Whether user is primary contact")
    is_active = Column(Boolean, default=True, nullable=False,
                      comment="Whether user is active")
    last_login = Column(DateTime(timezone=True), nullable=True,
                       comment="Last login timestamp")

    # Relationships
    repairer = relationship("Repairer", back_populates="users")

    __table_args__ = (
        Index('idx_repairer_users_repairer', 'repairer_uuid'),
        Index('idx_repairer_users_email', 'email'),
        Index('idx_repairer_users_name', 'last_name', 'first_name'),
        Index('idx_repairer_users_primary', 'is_primary_contact'),
        Index('idx_repairer_users_active', 'is_active'),
        UniqueConstraint('repairer_uuid', 'email', name='uq_repairer_users_email'),
    )


class Quote(BaseModel):
    """
    Quote requests
    """
    __tablename__ = 'quotes'

    quote_invitation_id = Column(String(100), nullable=False, unique=True,
                                comment="External quote invitation ID")
    request_id = Column(String(100), nullable=False,
                       comment="External request ID")
    repairer_uuid = Column(UUID(as_uuid=True),
                          ForeignKey('repairers.uuid', name='fk_quotes_repairer'),
                          nullable=False,
                          comment="Reference to repairer")
    supplier_name = Column(String(200), nullable=True,
                          comment="Supplier name")
    status = Column(String(20), default='open', nullable=False,
                   comment="Quote status")
    currency_code = Column(String(3), default='USD', nullable=False,
                          comment="Currency code")
    date_expected_close = Column(DateTime(timezone=True), nullable=True,
                               comment="Expected close date")
    date_parts_required = Column(DateTime(timezone=True), nullable=True,
                               comment="Date parts required by")
    is_at_risk = Column(Boolean, default=False, nullable=False,
                       comment="Whether quote is at risk of total loss")
    is_insurer_mandated = Column(Boolean, default=False, nullable=False,
                               comment="Whether quote is insurer mandated")
    transaction_fee_percentage = Column(Numeric(5, 4), default=0.0, nullable=False,
                                      comment="Transaction fee percentage")

    # Relationships
    repairer = relationship("Repairer", back_populates="quotes")
    quote_parts = relationship("QuotePart", back_populates="quote", cascade="all, delete-orphan")
    quote_vehicles = relationship("QuoteVehicle", back_populates="quote", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_quotes_invitation_id', 'quote_invitation_id'),
        Index('idx_quotes_request_id', 'request_id'),
        Index('idx_quotes_repairer', 'repairer_uuid'),
        Index('idx_quotes_status', 'status'),
        Index('idx_quotes_date_close', 'date_expected_close'),
    )


class QuoteVehicle(BaseModel):
    """
    Vehicles associated with quotes
    """
    __tablename__ = 'quote_vehicles'

    quote_uuid = Column(UUID(as_uuid=True),
                       ForeignKey('quotes.uuid', name='fk_quote_vehicles_quote'),
                       nullable=False,
                       comment="Reference to quote")
    vehicle_uuid = Column(UUID(as_uuid=True),
                         ForeignKey('vehicles.uuid', name='fk_quote_vehicles_vehicle'),
                         nullable=False,
                         comment="Reference to vehicle")
    vin = Column(String(17), nullable=True,
                comment="Vehicle VIN")
    mileage = Column(Integer, nullable=True,
                    comment="Vehicle mileage")
    exterior_color = Column(String(100), nullable=True,
                           comment="Vehicle exterior color")
    interior_color = Column(String(100), nullable=True,
                           comment="Vehicle interior color")
    insurance_company = Column(String(200), nullable=True,
                              comment="Insurance company name")
    plate_state = Column(String(10), nullable=True,
                        comment="License plate state")

    # Relationships
    quote = relationship("Quote", back_populates="quote_vehicles")
    vehicle = relationship("Vehicle", back_populates="quote_vehicles")

    __table_args__ = (
        Index('idx_quote_vehicles_quote', 'quote_uuid'),
        Index('idx_quote_vehicles_vehicle', 'vehicle_uuid'),
        Index('idx_quote_vehicles_vin', 'vin'),
    )


class QuotePart(BaseModel):
    """
    Parts requested in quotes
    """
    __tablename__ = 'quote_parts'

    quote_uuid = Column(UUID(as_uuid=True),
                       ForeignKey('quotes.uuid', name='fk_quote_parts_quote'),
                       nullable=False,
                       comment="Reference to quote")
    part_uuid = Column(UUID(as_uuid=True),
                      ForeignKey('parts.uuid', name='fk_quote_parts_part'),
                      nullable=False,
                      comment="Reference to part")
    requested_part_id = Column(String(100), nullable=True,
                              comment="External requested part ID")
    quantity = Column(Integer, default=1, nullable=False,
                     comment="Quantity requested")
    unit_price = Column(Numeric(10, 2), nullable=True,
                       comment="Unit price quoted")
    total_price = Column(Numeric(10, 2), nullable=True,
                        comment="Total price for quantity")
    condition_override = Column(String(10), nullable=True,
                               comment="Condition override for this quote")
    comment = Column(Text, nullable=True,
                    comment="Special comments or notes")
    is_filtered = Column(Boolean, default=False, nullable=False,
                        comment="Whether part was filtered in request")
    position = Column(String(20), nullable=True,
                     comment="Position specification (left, right, etc)")

    # Relationships
    quote = relationship("Quote", back_populates="quote_parts")
    part = relationship("Part", back_populates="quote_parts")

    __table_args__ = (
        Index('idx_quote_parts_quote', 'quote_uuid'),
        Index('idx_quote_parts_part', 'part_uuid'),
        Index('idx_quote_parts_requested_id', 'requested_part_id'),
        Index('idx_quote_parts_filtered', 'is_filtered'),
    )