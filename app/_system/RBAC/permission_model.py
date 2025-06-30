from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer, Text, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.base.model import BaseModel

from app.register.database import db_registry

class Permission(BaseModel):
    """
    Ppermissions: service:action format
    Examples: accounting:read, customer:update, invoice:approve
    """
    __tablename__ = 'permissions'
    __depends_on_ = []
    
    name = Column(String(100), unique=True, nullable=False)  # "accounting:read"
    service = Column(String(50), nullable=False)             # "accounting"
    action = Column(String(50), nullable=False)              # "read", "write", "create", "delete", "approve"
    resource = Column(String(100), nullable=True)            # Optional: specific resource like "invoice_123"
    description = Column(Text, nullable=True)                # Human-readable description

    # Relationships
    role_permissions = relationship("RolePermission", back_populates="permission", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_permissions_name', 'name'),
        Index('idx_permissions_service', 'service'),
        Index('idx_permissions_service_action', 'service', 'action'),
    )

    @classmethod
    def create_permission(cls, service, action, resource=None, description=None):
        """Create a new permission with 3-position name format"""
        db_session=db_registry._routing_session()
        if not resource:
            return False, "Resource is required for 3-position permission format"
        
        # Permission name is always lowercase, but individual fields preserve case
        name = f"{service.lower()}:{resource.lower()}:{action.lower()}"

        existing = db_session.query(cls).filter(cls.name == name).first()
        if existing:
            return False, f"Permission already exists: {name}"

        permission = cls(
            name=name,
            service=service,  
            action=action,    
            resource=resource,
            description=description
        )

        db_session.add(permission)
        db_session.commit()

        return True, permission

    @classmethod
    def find_by_name(cls, name):
        """Find permission by name"""
        db_session=db_registry._routing_session()
        return db_session.query(cls).filter(cls.name == name).first()

    @classmethod
    def find_by_service(cls, service):
        """Find all permissions for a service"""
        db_session=db_registry._routing_session()
        return db_session.query(cls).filter(cls.service == service).order_by(cls.action).all()

    @classmethod
    def find_by_service_action(cls, service, action):
        """Find permission by service and action"""
        db_session=db_registry._routing_session()
        return db_session.query(cls).filter(
            cls.service == service,
            cls.action == action
        ).first()

    def to_dict(self):
        """Convert permission to dictionary"""
        return {
            'id': str(self.id),
            'name': self.name,
            'service': self.service,
            'action': self.action,
            'resource': self.resource,
            'description': self.description,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


