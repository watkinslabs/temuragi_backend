import ipaddress
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Text, func, desc
from sqlalchemy.dialects.postgresql import UUID, CIDR
from sqlalchemy.orm import relationship

from app.base.model import BaseModel
from app.register.database import db_registry

class Firewall(BaseModel):
    """Model for storing IP whitelist/blacklist patterns with order priority"""
    __tablename__ = 'firewall'
    __depends_on__=[]
    
    ip_pattern = Column(String(50), nullable=False, unique=True)
    ip_type = Column(String(10), nullable=False)  # 'allow' or 'block'
    description = Column(String(255), nullable=True)
    order = Column(Integer, nullable=False, default=100)  # Lower values = higher priority

    def __repr__(self):
        """String representation of the IP pattern"""
        return f"<Firewall {self.ip_pattern} ({self.ip_type})>"

    @staticmethod
    def validate_ip_pattern(pattern):
        """
        Validates an IP pattern (single IP or CIDR notation)
        
        Args:
            pattern (str): The IP pattern to validate
            
        Returns:
            tuple: (valid, message)
                - valid (bool): True if valid, False otherwise
                - message (str): Validation message or error
        """
        try:
            # Check if it's a CIDR notation
            if '/' in pattern:
                ipaddress.ip_network(pattern, strict=False)
                return True, "Valid CIDR pattern"
            else:
                # It's a single IP address
                ipaddress.ip_address(pattern)
                return True, "Valid IP address"
        except ValueError:
            # Create simplified error message without technical details
            return False, f"Invalid IP pattern"
    
    @classmethod
    def create_initial_data(cls):
        """Create initial firewall rules"""
        db_session=db_registry._routing_session()
        initial_rules = [
            ('99.64.82.20', 'allow', 'High priority admin IP', True, 10),
            ('10.6.0.0/24', 'allow', 'Lab Network', True, 10),
            ('0.0.0.0/0', 'block', 'Block all IPv4 traffic by default', True, 1000)
        ]
        
        for ip_pattern, ip_type, description, active, order in initial_rules:
            existing = db_session.query(cls).filter_by(ip_pattern=ip_pattern).first()
            if not existing:
                firewall_rule = cls(
                    ip_pattern=ip_pattern,
                    ip_type=ip_type,
                    description=description,
                    is_active=active,
                    order=order
                )
                db_session.add(firewall_rule)
        
    @classmethod
    def get_all_patterns(cls):
        db_session=db_registry._routing_session()
        """Get all IP patterns ordered by priority (order) and pattern"""
        patterns = db_session.query(cls).filter(cls.is_active == True).order_by(cls.order, cls.ip_pattern).all()
        return patterns

    @classmethod
    def get_active_patterns(cls, pattern_type=None):
        """Get active IP patterns with optional type filter"""
        query = db_session.query(cls).filter(cls.is_active == True)
        
        if pattern_type:
            query = query.filter(cls.ip_type == pattern_type)
            
        return query.order_by(cls.order, cls.ip_pattern).all()

    @classmethod
    def find_by_pattern(cls, pattern):
        """Find IP filter by exact pattern"""
        db_session=db_registry._routing_session()
        return db_session.query(cls).filter(cls.ip_pattern == pattern).first()

    @classmethod
    def find_by_id(cls, pattern_id):
        """Find IP filter by ID"""
        db_session=db_registry._routing_session()
        return db_session.query(cls).filter(cls.id == pattern_id).first()

    @classmethod
    def add_pattern(cls, ip_pattern, ip_type, description=None, order=100):
        """Add a new IP pattern if it doesn't exist and it's valid"""
        db_session=db_registry._routing_session()
        # First validate the IP pattern
        is_valid, validation_message = cls.validate_ip_pattern(ip_pattern)
        if not is_valid:
            return False, "Invalid IP format"
        
        # Check if pattern already exists
        existing = cls.find_by_pattern( ip_pattern)
        if existing:
            if not existing.active:
                # Reactivate the existing pattern
                existing.active = True
                existing.ip_type = ip_type
                existing.order = order
                if description:
                    existing.description = description
                db_session.commit()
                return True, f"Reactivated {ip_type} pattern"
            return False, f"IP pattern already exists"
        
        # Create new pattern
        new_pattern = cls(
            ip_pattern=ip_pattern,
            ip_type=ip_type,
            description=description,
            order=order
        )
        
        try:
            db_session.add(new_pattern)
            db_session.commit()
            return True, f"Added {ip_type} pattern"
        except Exception as e:
            db_session.rollback()
            return False, f"Database error"

    @classmethod
    def update_pattern(cls, pattern_id, ip_type=None, description=None, active=None, order=None):
        """Update an IP pattern"""
        db_session=db_registry._routing_session()
        pattern = cls.find_by_id(db_session, pattern_id)
        if not pattern:
            return False, "Pattern not found"
        
        # Update provided fields
        if ip_type is not None:
            pattern.ip_type = ip_type
        
        if description is not None:
            pattern.description = description
            
        if active is not None:
            pattern.active = active
            
        if order is not None:
            pattern.order = order
        
        try:
            db_session.commit()
            return True, "Pattern updated successfully"
        except Exception as e:
            db_session.rollback()
            return False, "Database error"

    @classmethod
    def delete_pattern(cls, pattern_id):
        """Soft delete an IP pattern by ID (mark as inactive)"""
        db_session=db_registry._routing_session()
        pattern = cls.find_by_id( pattern_id)
        if not pattern:
            return False, "Pattern not found"
        
        try:
            pattern.active = False
            db_session.commit()
            return True, "Pattern deleted successfully"
        except Exception as e:
            db_session.rollback()
            return False, "Database error"
            
    @classmethod
    def hard_delete_pattern(cls,  pattern_id):
        """Permanently delete an IP pattern by ID"""
        db_session=db_registry._routing_session()
        pattern = cls.find_by_id( pattern_id)
        if not pattern:
            return False, "Pattern not found"
        
        try:
            db_session.delete(pattern)
            db_session.commit()
            return True, "Pattern permanently deleted"
        except Exception as e:
            db_session.rollback()
            return False, "Database error"

    @classmethod
    def check_ip_access(cls, ip_address):
        """Check if an IP address should be allowed access based on rule order
        
        Returns:
            tuple: (allowed, reason)
                - allowed (bool): True if access is allowed, False if blocked
                - reason (str): Description of why access was allowed/blocked
        """
        db_session=db_registry._routing_session()
        # Get all active patterns ordered by priority (lower order value = higher priority)
        patterns = db_session.query(cls).filter(cls.is_active == True).order_by(cls.order).all()
        
        # If no patterns defined, allow by default
        if not patterns:
            return True, "Access allowed by default (no patterns defined)"
        
        # Check patterns in order of priority
        for pattern in patterns:
            if cls._ip_matches_pattern(ip_address, pattern.ip_pattern):
                if pattern.ip_type == 'allow':
                    return True, f"IP allowed by pattern: {pattern.ip_pattern} (order: {pattern.order})"
                else:
                    return False, f"IP blocked by pattern: {pattern.ip_pattern} (order: {pattern.order})"
        
        # If no patterns matched, use a default deny policy when allow rules exist
        allow_exists = db_session.query(cls).filter(cls.is_active == True, cls.ip_type == 'allow').first() is not None
        if allow_exists:
            return False, "IP not in allowed list"
        else:
            return True, "Access allowed by default (no matching rules)"
    
    @staticmethod
    def _ip_matches_pattern(ip, pattern):
        """Check if an IP matches a pattern (CIDR or exact match)"""
        try:
            if '/' in pattern:  # CIDR notation
                return ipaddress.ip_address(ip) in ipaddress.ip_network(pattern, strict=False)
            else:
                # Exact match
                return ip == pattern
        except ValueError:
            # Invalid IP format - cannot match
            return False