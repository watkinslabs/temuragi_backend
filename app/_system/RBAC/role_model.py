import uuid
import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer, Text, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app._system._core.base import BaseModel


class Role(BaseModel):
    __tablename__ = 'roles'

    name = Column(String(100), unique=True, nullable=False)
    display = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    is_admin = Column(Boolean, default=False, nullable=False)

    # Relationships
    users = relationship("User", back_populates="role")
    permissions = relationship("RolePermission", back_populates="role", cascade="all, delete-orphan")

    @classmethod
    def create_initial_data(cls, session):
        """Create initial admin role with basic permissions"""
        existing = session.query(cls).filter_by(name='admin').first()
        if not existing:
            admin_role = cls(
                name='admin',
                display='Administrator',
                description='Full system administrator',
                is_admin=True
            )
            session.add(admin_role)
            session.commit()
            
            # Create some basic admin permissions
            basic_permissions = [
                ('user', 'read', None, 'View users'),
                ('user', 'write', None, 'Manage users'),
                ('role', 'read', None, 'View roles'),
                ('role', 'write', None, 'Manage roles'),
                ('permission', 'read', None, 'View permissions'),
                ('permission', 'write', None, 'Manage permissions'),
            ]
            
            for service, action, resource, description in basic_permissions:
                success, perm = Permission.create_permission(
                    session, service, action, resource, description
                )
                if success:
                    RolePermission.grant_permission(session, admin_role.uuid, perm.name)

    def has_permission(self, session, permission_name):
        """Check if this role has a specific permission"""
        permission = Permission.find_by_name(session, permission_name)
        if not permission:
            return False
        
        role_permission = session.query(RolePermission).filter(
            RolePermission.role_uuid == self.uuid,
            RolePermission.permission_uuid == permission.uuid
        ).first()
        
        return role_permission is not None

    def get_permissions(self, session):
        """Get all permissions for this role"""
        return session.query(Permission).join(RolePermission).filter(
            RolePermission.role_uuid == self.uuid
        ).order_by(Permission.service, Permission.action).all()