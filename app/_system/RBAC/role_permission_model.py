from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer, Text, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from flask import g

from app.base.model import BaseModel

try:
    from app.classes import Permission
    from app.models import User
except:
    pass

from app.register.database import db_registry

class RolePermission(BaseModel):
    """
    Junction table linking roles to permissions
    """
    __depends_on__ = ['Role', 'Permission','User']
    __tablename__ = 'role_permissions'

    role_id = Column(
        UUID(as_uuid=True),
        ForeignKey('roles.id', name='fk_role_permissions_role'),
        nullable=False
    )
    permission_id = Column(
        UUID(as_uuid=True),
        ForeignKey('permissions.id', name='fk_role_permissions_permission'),
        nullable=False
    )

    # Relationships
    role = relationship("Role", back_populates="permissions")
    permission = relationship("Permission", back_populates="role_permissions")

    __table_args__ = (
        UniqueConstraint('role_id', 'permission_id', name='uq_role_permission'),
        Index('idx_role_permissions_role', 'role_id'),
        Index('idx_role_permissions_permission', 'permission_id'),
    )

    @classmethod
    def grant_permission(cls,  role_id, permission_name):
        """Grant a permission to a role"""
        db_session=db_registry._routing_session()
        # Direct usage now!
        permission = Permission.find_by_name(permission_name)
        if not permission:
            return False, f"Permission not found: {permission_name}"

        # Check if already granted
        existing = db_session.query(cls).filter(
            cls.role_id == role_id,
            cls.permission_id == permission.id
        ).first()

        if existing:
            return False, f"Permission already granted: {permission_name}"

        # Grant permission
        role_permission = cls(
            role_id=role_id,
            permission_id=permission.id
        )

        db_session.add(role_permission)
        db_session.commit()

        return True, role_permission

    @classmethod
    def revoke_permission(cls, role_id, permission_name):
        """Revoke a permission from a role"""
        db_session=db_registry._routing_session()
        permission = Permission.find_by_name( permission_name)
        if not permission:
            return False, f"Permission not found: {permission_name}"

        # Find role permission
        role_permission = db_session.query(cls).filter(
            cls.role_id == role_id,
            cls.permission_id == permission.id
        ).first()

        if not role_permission:
            return False, f"Permission not granted: {permission_name}"

        db_session.delete(role_permission)
        db_session.commit()

        return True, f"Permission revoked: {permission_name}"

    @classmethod
    def user_has_permission(cls, user_id, permission_name):
        """Check if a user has a specific permission through their role"""
        db_session=db_registry._routing_session()
        user = db_session.query(User).filter(User.id == user_id).first()
        if not user or not user.role_id:
            return False

        # Find permission
        permission = Permission.find_by_name(permission_name)
        if not permission:
            return False

        # Check if role has permission
        role_permission = db_session.query(cls).filter(
            cls.role_id == user.role_id,
            cls.permission_id == permission.id
        ).first()

        return role_permission is not None

    @classmethod
    def get_user_permissions(cls, user_id):
        """Get all permissions for a user through their role"""
        self.db_session=db_registry._routing_session()
        user = db_session.query(User).filter(User.id == user_id).first()
        if not user or not user.role_id:
            return []

        permissions = db_session.query(Permission).join(cls).filter(
            cls.role_id == user.role_id
        ).order_by(Permission.service, Permission.action).all()

        return permissions