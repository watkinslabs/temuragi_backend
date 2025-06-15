import re
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, func, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship, validates
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB

from app.base.model import BaseModel


class Report(BaseModel):

    """Model for storing reports with SQL queries and configuration"""
    __tablename__ = 'reports'
    __depends_on__ = ['Connection', 'DatabaseType', 'DataType', 'VariableType', 'Permission']
    
    # Core fields
    slug = Column(String(255), nullable=False, unique=True)  # Immutable identifier for permissions
    name = Column(String(255), nullable=False)  # Display name that can change
    display = Column(String(255), nullable=True)  # Optional longer display name
    query = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    
    # Database connection
    connection_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey('connections.uuid', ondelete='RESTRICT'),
        nullable=False
    )
    
    # Configuration fields
    category = Column(String(100), nullable=True)
    tags = Column(JSONB, nullable=True)
    icon = Column(String(50), nullable=True)
    color = Column(String(7), nullable=True)
    
    related_report_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey('reports.uuid', ondelete='SET NULL'),
        nullable=True
    )
    
    # Boolean flags
    is_wide = Column(Boolean, default=False)
    is_ajax = Column(Boolean, default=False)
    is_auto_run = Column(Boolean, default=False)
    is_searchable = Column(Boolean, default=True)
    is_public = Column(Boolean, default=False)
    is_download_csv = Column(Boolean, default=False)
    is_download_xlsx = Column(Boolean, default=False)
    is_system = Column(Boolean, default=False)
    
    # Permission tracking
    permissions_created = Column(Boolean, default=False)  # Track if permissions were created
    
    # Options
    options = Column(JSONB, nullable=True)
    
    # Tracking
    last_run = Column(DateTime, nullable=True)
    version = Column(Integer, default=1)
    
    # Relationships
    connection = relationship("Connection", foreign_keys=[connection_id])
    columns = relationship(
        "ReportColumn", 
        back_populates="report", 
        cascade="all, delete-orphan",
        order_by="ReportColumn.order_index"
    )
    variables = relationship(
        "ReportVariable", 
        back_populates="report", 
        cascade="all, delete-orphan",
        order_by="ReportVariable.order_index"
    )
    executions = relationship(
        "ReportExecution", 
        back_populates="report", 
        cascade="all, delete-orphan"
    )
    schedules = relationship(
        "ReportSchedule", 
        back_populates="report", 
        cascade="all, delete-orphan"
    )
    
    # Self-referential relationship
    related_report = relationship(
        "Report", 
        remote_side='Report.uuid',
        foreign_keys=[related_report_id]
    )
    
    # Indexes
    __table_args__ = (
        Index('idx_report_slug', 'slug'),
        Index('idx_report_name', 'name'),
        Index('idx_report_category', 'category'),
        Index('idx_report_public', 'is_public'),
    )
    
    def __init__(self, **kwargs):
        # Auto-generate slug if not provided
        if 'slug' not in kwargs and 'name' in kwargs:
            kwargs['slug'] = self.generate_slug(kwargs['name'])
        
        # Apply default values for JSON columns
        if 'options' not in kwargs or kwargs['options'] is None:
            kwargs['options'] = self.get_default_options()
        else:
            self._ensure_options_structure(kwargs['options'])
        
        if 'tags' not in kwargs:
            kwargs['tags'] = []
        
        super(Report, self).__init__(**kwargs)
    
    @staticmethod
    def generate_slug(name, session=None, existing_slug=None):
        """Generate a URL-safe slug from a name"""
        # Convert to lowercase
        slug = name.lower()
        # Replace spaces and underscores with hyphens
        slug = re.sub(r'[\s_]+', '-', slug)
        # Remove all non-alphanumeric characters except hyphens
        slug = re.sub(r'[^a-z0-9\-]', '', slug)
        # Remove multiple consecutive hyphens
        slug = re.sub(r'-+', '-', slug)
        # Strip hyphens from start and end
        slug = slug.strip('-')
        
        # If we have a session, ensure uniqueness
        if session and slug != existing_slug:
            base_slug = slug
            counter = 1
            while session.query(Report).filter_by(slug=slug).first():
                slug = f"{base_slug}-{counter}"
                counter += 1
        
        return slug
    
    @validates('slug')
    def validate_slug(self, key, slug):
        """Validate slug format and prevent changes after creation"""
        if not slug:
            raise ValueError("Slug cannot be empty")
        
        # Check if this is an update (object already has an ID)
        if self.uuid and hasattr(self, '_sa_instance_state'):
            # Get the current value from the database
            history = self._sa_instance_state.attrs.slug.history
            if history.unchanged and history.unchanged[0] != slug:
                raise ValueError("Slug cannot be changed after creation. Create a new report instead.")
        
        # Validate slug format
        if not re.match(r'^[a-z0-9\-]+$', slug):
            raise ValueError("Slug can only contain lowercase letters, numbers, and hyphens")
        
        return slug
    
    def save(self, session=None):
        """Override save to handle permission creation"""
        is_new = not self.uuid
        old_name = None
        old_display = None
        
        # Track name changes for existing reports
        if not is_new and hasattr(self, '_sa_instance_state'):
            name_history = self._sa_instance_state.attrs.name.history
            display_history = self._sa_instance_state.attrs.display.history
            
            if name_history.has_changes() and name_history.deleted:
                old_name = name_history.deleted[0]
            
            if display_history.has_changes() and display_history.deleted:
                old_display = display_history.deleted[0]
        
        # Call parent save
        super().save(session)
        
        # Handle post-save operations
        if session:
            if is_new and not self.permissions_created:
                # Create permissions for new report
                self.create_permissions(session)
                self.permissions_created = True
                session.commit()
            elif (old_name or old_display) and self.permissions_created:
                # Update permission descriptions for name changes
                self.update_permission_descriptions(session)
    
    def delete(self, session=None):
        """Override delete to handle permission cleanup"""
        if session and self.permissions_created:
            self.delete_permissions(session)
        
        # Call parent delete
        super().delete(session)
    
    @classmethod
    def create_report(cls, session, **kwargs):
        """Factory method to create a report with permissions"""
        report = cls(**kwargs)
        session.add(report)
        session.commit()
        
        # Create permissions
        if not report.permissions_created:
            report.create_permissions(session)
            report.permissions_created = True
            session.commit()
        
        return report
    
    def get_default_options(self):
        """Return default options structure"""
        return {
            "results_limit": 0,
            "is_datatable": True,
            "datatable": {
                "is_live": False,
                "is_searchable": True,
                "is_filterable": True,
                "is_exportable": True,
                "export_formats": "csv,xlsx,pdf"
            },
            "cache_enabled": False,
            "cache_duration_minutes": 60,
            "timeout_seconds": 300,
            "refresh_interval": 0,
            "row_limit": 10000,
        }
    
    def _ensure_options_structure(self, options):
        """Ensure options has all required fields with default values"""
        defaults = self.get_default_options()
        
        for key, value in defaults.items():
            if key not in options:
                options[key] = value
            elif isinstance(value, dict) and key in options:
                for nested_key, nested_value in value.items():
                    if nested_key not in options[key]:
                        options[key][nested_key] = nested_value
        
        return options
    
    def get_database_type(self):
        """Get the database type from the connection"""
        if self.connection:
            return self.connection.db_type.lower()
        return None
    
    def get_connection_string(self):
        """Get the full connection string from the connection"""
        if self.connection:
            return self.connection.get_connection_string()
        return None
    
    @classmethod
    def create_initial_data(cls, session):
        """Create initial report management permissions"""
        from app.register.database import get_model
        
        Permission = get_model('Permission')
        if not Permission:
            return
        
        # Create general report management permissions
        management_permissions = [
            ('report', 'system', 'create', 'Create new reports'),
            ('report', 'system', 'manage', 'Manage all reports'),
            ('report', 'system', 'delete_any', 'Delete any report'),
            ('report', 'system', 'edit_any', 'Edit any report'),
            ('report', 'system', 'view_all', 'View all reports regardless of assignment'),
        ]
        
        for service, resource, action, description in management_permissions:
            permission_name = f"{service}:{resource}:{action}"
            existing = session.query(Permission).filter_by(name=permission_name).first()
            if not existing:
                Permission.create_permission(
                    session=session,
                    service=service,
                    action=action,
                    resource=resource,
                    description=description
                )
    
    def create_permissions(self, session):
        """Create permissions for this specific report using slug"""
        from app.register.database import get_model
        
        Permission = get_model('Permission')
        if not Permission:
            return False, "Permission model not available"
        
        # Skip if already created
        if self.permissions_created:
            return False, "Permissions already created"
        
        report_actions = [
            ('view', f'View report: {self.display or self.name}'),
            ('execute', f'Execute report: {self.display or self.name}'),
            ('export', f'Export data from report: {self.display or self.name}'),
            ('schedule', f'Schedule report: {self.display or self.name}'),
            ('edit', f'Edit report: {self.display or self.name}'),
            ('delete', f'Delete report: {self.display or self.name}'),
            ('share', f'Share report: {self.display or self.name}'),
        ]
        
        created_permissions = []
        
        for action, description in report_actions:
            permission_name = f"report:{self.slug}:{action}"
            
            existing = session.query(Permission).filter_by(name=permission_name).first()
            if not existing:
                success, result = Permission.create_permission(
                    session=session,
                    service='report',
                    action=action,
                    resource=self.slug,
                    description=description
                )
                if success:
                    created_permissions.append(result)
        
        return True, created_permissions
    
    def update_permission_descriptions(self, session):
        """Update permission descriptions when report name changes"""
        from app.register.database import get_model
        Permission = get_model('Permission')
        
        if not Permission:
            return False, "Permission model not available"
        
        permissions = session.query(Permission).filter(
            Permission.service == 'report',
            Permission.resource == self.slug
        ).all()
        
        for perm in permissions:
            action_descriptions = {
                'view': f'View report: {self.display or self.name}',
                'execute': f'Execute report: {self.display or self.name}',
                'export': f'Export data from report: {self.display or self.name}',
                'schedule': f'Schedule report: {self.display or self.name}',
                'edit': f'Edit report: {self.display or self.name}',
                'delete': f'Delete report: {self.display or self.name}',
                'share': f'Share report: {self.display or self.name}',
            }
            
            if perm.action in action_descriptions:
                perm.description = action_descriptions[perm.action]
        
        session.commit()
        return True, f"Updated {len(permissions)} permission descriptions"
    
    def delete_permissions(self, session):
        """Delete all permissions for this report"""
        from app.register.database import get_model
        Permission = get_model('Permission')
        
        if not Permission:
            return False, "Permission model not available"
        
        permissions = session.query(Permission).filter(
            Permission.service == 'report',
            Permission.resource == self.slug
        ).all()
        
        # Also need to delete RolePermission entries
        RolePermission = get_model('RolePermission')
        if RolePermission:
            for perm in permissions:
                role_perms = session.query(RolePermission).filter(
                    RolePermission.permission_uuid == perm.uuid
                ).all()
                for rp in role_perms:
                    session.delete(rp)
        
        for perm in permissions:
            session.delete(perm)
        
        session.commit()
        return True, f"Deleted {len(permissions)} permissions"
    
    @classmethod
    def check_permission(cls, session, user_uuid, report_slug, action='view'):
        """Check if user has permission for specific report action"""
        from app._system.RBAC.permission_class import RbacPermissionChecker
        
        permission_name = f"report:{report_slug}:{action}"
        
        checker = RbacPermissionChecker(session)
        
        report = session.query(cls).filter_by(slug=report_slug).first()
        
        has_permission = checker.check_permission(
            user_uuid=user_uuid,
            permission_name=permission_name,
            resource_type='report',
            resource_name=report.name if report else report_slug,
            resource_id=str(report.uuid) if report else None,
            action_attempted=action
        )
        
        # Public reports allow view/execute
        if report and report.is_public and action in ['view', 'execute']:
            return True
        
        # Check admin permissions
        if action in ['edit', 'delete'] and not has_permission:
            admin_permission = f"report:system:{action}_any"
            has_permission = checker.check_permission(
                user_uuid=user_uuid,
                permission_name=admin_permission,
                resource_type='report',
                resource_name=report.name if report else report_slug,
                action_attempted=action
            )
        
        # Check view_all permission
        if action == 'view' and not has_permission:
            view_all_permission = "report:system:view_all"
            has_permission = checker.check_permission(
                user_uuid=user_uuid,
                permission_name=view_all_permission,
                resource_type='report',
                resource_name=report.name if report else report_slug,
                action_attempted=action
            )
        
        return has_permission
    
    @classmethod
    def get_user_reports(cls, session, user_uuid):
        """Get all reports a user has permission to view"""
        from app.register.database import get_model
        
        RolePermission = get_model('RolePermission')
        Permission = get_model('Permission')
        User = get_model('User')
        
        if not all([RolePermission, Permission, User]):
            return []
        
        user = session.query(User).filter_by(uuid=user_uuid).first()
        if not user or not user.role_uuid:
            return session.query(cls).filter(cls.is_public == True).all()
        
        # Check view_all permission
        view_all_perm = session.query(Permission).join(RolePermission).filter(
            RolePermission.role_uuid == user.role_uuid,
            Permission.name == 'report:system:view_all'
        ).first()
        
        if view_all_perm:
            return session.query(cls).all()
        
        # Get report view permissions
        report_permissions = session.query(Permission).join(RolePermission).filter(
            RolePermission.role_uuid == user.role_uuid,
            Permission.service == 'report',
            Permission.action == 'view'
        ).all()
        
        report_slugs = [perm.resource for perm in report_permissions 
                       if perm.resource and perm.resource != 'system']
        
        reports = session.query(cls).filter(
            cls.slug.in_(report_slugs)
        ).all()
        
        public_reports = session.query(cls).filter(
            cls.is_public == True
        ).all()
        
        all_reports = {r.uuid: r for r in reports + public_reports}
        
        return list(all_reports.values())
    
    def assign_to_role(self, session, role_uuid, actions=None):
        """Assign this report to a role with specified actions"""
        from app.register.database import get_model
        
        RolePermission = get_model('RolePermission')
        if not RolePermission:
            return False, "RolePermission model not available"
        
        # Ensure permissions exist first
        if not self.permissions_created:
            self.create_permissions(session)
            self.permissions_created = True
            session.commit()
        
        if actions is None:
            actions = ['view', 'execute', 'export']
        
        granted = []
        failed = []
        
        for action in actions:
            permission_name = f"report:{self.slug}:{action}"
            success, result = RolePermission.grant_permission(
                session, role_uuid, permission_name
            )
            if success:
                granted.append(action)
            else:
                failed.append(f"{action}: {result}")
        
        if failed:
            return False, f"Granted: {', '.join(granted)}. Failed: {'; '.join(failed)}"
        
        return True, f"Granted actions: {', '.join(granted)}"
    
    def remove_from_role(self, session, role_uuid, actions=None):
        """Remove this report from a role"""
        from app.register.database import get_model
        
        RolePermission = get_model('RolePermission')
        if not RolePermission:
            return False, "RolePermission model not available"
        
        if actions is None:
            actions = ['view', 'execute', 'export', 'schedule', 'edit', 'delete', 'share']
        
        revoked = []
        for action in actions:
            permission_name = f"report:{self.slug}:{action}"
            success, result = RolePermission.revoke_permission(
                session, role_uuid, permission_name
            )
            if success:
                revoked.append(action)
        
        return True, f"Revoked actions: {', '.join(revoked)}"
    
    def get_roles_with_access(self, session, action='view'):
        """Get all roles that have access to this report"""
        from app.register.database import get_model
        
        Permission = get_model('Permission')
        RolePermission = get_model('RolePermission')
        Role = get_model('Role')
        
        if not all([Permission, RolePermission, Role]):
            return []
        
        permission_name = f"report:{self.slug}:{action}"
        
        roles = session.query(Role).join(RolePermission).join(Permission).filter(
            Permission.name == permission_name
        ).all()
        
        return roles
    
    def duplicate(self, session, new_name, new_slug=None):
        """Create a copy of this report with a new name and slug"""
        if not new_slug:
            new_slug = self.generate_slug(new_name, session)
        
        existing = session.query(Report).filter_by(slug=new_slug).first()
        if existing:
            return None, f"Report with slug '{new_slug}' already exists"
        
        new_report = Report(
            slug=new_slug,
            name=new_name,
            display=f"{self.display or self.name} (Copy)",
            query=self.query,
            description=self.description,
            connection_id=self.connection_id,
            category=self.category,
            tags=self.tags.copy() if self.tags else [],
            is_wide=self.is_wide,
            is_ajax=self.is_ajax,
            is_auto_run=self.is_auto_run,
            is_searchable=self.is_searchable,
            is_public=False,
            is_download_csv=self.is_download_csv,
            is_download_xlsx=self.is_download_xlsx,
            options=self.options.copy() if self.options else self.get_default_options()
        )
        
        session.add(new_report)
        session.flush()
        
        from app.models import ReportColumn, ReportVariable

        # Copy columns
        for col in self.columns:
            new_col = ReportColumn(
                report_id=new_report.uuid,
                name=col.name,
                display_name=col.display_name,
                data_type_id=col.data_type_id,
                is_searchable=col.is_searchable,
                search_type=col.search_type,
                is_visible=col.is_visible,
                is_sortable=col.is_sortable,
                format_string=col.format_string,
                width=col.width,
                alignment=col.alignment,
                options=col.options.copy() if col.options else {},
                order_index=col.order_index,
                validation_regex=col.validation_regex,
                validation_message=col.validation_message
            )
            session.add(new_col)
        
        # Copy variables
        for var in self.variables:
            new_var = ReportVariable(
                report_id=new_report.uuid,
                name=var.name,
                display_name=var.display_name,
                variable_type_id=var.variable_type_id,
                data_type_id=var.data_type_id,
                default_value=var.default_value,
                placeholder=var.placeholder,
                help_text=var.help_text,
                is_required=var.is_required,
                is_hidden=var.is_hidden,
                limits=var.limits.copy() if var.limits else {},
                depends_on=var.depends_on,
                dependency_condition=var.dependency_condition.copy() if var.dependency_condition else None,
                order_index=var.order_index
            )
            session.add(new_var)
        
        session.commit()
        
        # Create permissions
        new_report.create_permissions(session)
        new_report.permissions_created = True
        session.commit()
        
        return new_report, "Report duplicated successfully"
    
    def __repr__(self):
        return f"<Report {self.slug} - {self.name}>"