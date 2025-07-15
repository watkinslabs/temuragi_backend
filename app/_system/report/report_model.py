import re
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, func, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship, validates
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB

from app.base.model import BaseModel

from app.classes import Permission,RolePermission,User
from app.register.database import db_registry

class Report(BaseModel):

    """Model for storing reports with SQL queries and configuration"""
    __tablename__ = 'reports'
    __depends_on__ = [
        'Connection',
        'DataType',
        'VariableType',
        'Permission',
        'RolePermission',
        'User',
        'Model',
    ]    
    # Core fields
    slug = Column(String(255), nullable=False, unique=True)  # Immutable identifier for permissions
    name = Column(String(255), nullable=False)  # Display name that can change
    label = Column(String(255), nullable=True)  # Optional longer display name
    query = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    model_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey('models.id', ondelete='CASCADE'),
        nullable=True
    )
    
    # Database connection
    connection_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey('connections.id', ondelete='RESTRICT'),
        nullable=True
    )
    
    # Configuration fields
    category = Column(String(100), nullable=True)
    tags = Column(JSONB, nullable=True)
    icon = Column(String(50), nullable=True)
    color = Column(String(7), nullable=True)
    
    
    # Boolean flags
    is_wide = Column(Boolean, default=False)
    is_ajax = Column(Boolean, default=False)
    is_auto_run = Column(Boolean, default=False)
    is_searchable = Column(Boolean, default=True)
    is_public = Column(Boolean, default=False)
    is_published = Column(Boolean, default=False)  # Controls draft/published state
    is_download_csv = Column(Boolean, default=False)
    is_download_xlsx = Column(Boolean, default=False)
    is_system = Column(Boolean, default=False)
    is_model = Column(Boolean, nullable=False, default=False)
    is_auto_refresh = Column(Boolean, nullable=False, default=False)
    
    
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
    model = relationship("Model", foreign_keys=[model_id])

    
    
    report_template_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey('report_templates.id', ondelete='SET NULL'),
        nullable=True
    )

    report_template = relationship("ReportTemplate", foreign_keys=[report_template_id])
    
    page_actions = relationship(
        "PageAction",
        back_populates="report",
        cascade="all, delete-orphan",
        order_by="PageAction.order_index"
    )
        
    # Indexes
    __table_args__ = (
        Index('idx_report_slug', 'slug'),
        Index('idx_report_name', 'name'),
        Index('idx_report_category', 'category'),
        Index('idx_report_public', 'is_public'),
        Index('idx_report_published', 'is_published'),
        Index('idx_report_published_public', 'is_published', 'is_public'),
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
    def generate_slug(name,  existing_slug=None):
        """Generate a URL-safe slug from a name"""
        db_session=db_registry._routing_session()
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
        
        # If we have a db_session, ensure uniqueness
        if db_session and slug != existing_slug:
            base_slug = slug
            counter = 1
            while db_session.query(Report).filter_by(slug=slug).first():
                slug = f"{base_slug}-{counter}"
                counter += 1
        
        return slug
    
    #@validates('slug')
    def validate_slug(self, key, slug):
        """Validate slug format and prevent changes after creation"""
        db_session=db_registry._routing_session()
        if not slug:
            raise ValueError("Slug cannot be empty")
            
        # Validate slug format first
        if not re.match(r'^[a-z0-9\-/]+$', slug):
            raise ValueError("Slug can only contain lowercase letters, numbers, hyphens, and slashes")        
      
        
        return slug

    def save(self):
        """Override save to handle permission creation"""
        db_session=db_registry._routing_session()
        is_new = not self.id
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
        super().save()
        
        # Handle post-save operations
        if db_session:
            if is_new and not self.permissions_created:
                # Create permissions for new report
                self.create_permissions()
                self.permissions_created = True
                db_session.commit()
            elif (old_name or old_display) and self.permissions_created:
                # Update permission descriptions for name changes
                self.update_permission_descriptions()
    
    def delete(self):
        """Override delete to handle permission cleanup"""
        db_session=db_registry._routing_session()
        if db_session and self.permissions_created:
            self.delete_permissions()
        
        # Call parent delete
        super().delete()
    
    @classmethod
    def create_report(cls,  **kwargs):
        """Factory method to create a report with permissions"""
        db_session=db_registry._routing_session()
        report = cls(**kwargs)
        db_session.add(report)
        db_session.commit()
        
        # Create permissions
        if not report.permissions_created:
            report.create_permissions()
            report.permissions_created = True
            db_session.commit()
        
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
    
    
    def create_permissions(self):
        """Create permissions for this specific report using slug"""
        db_session=db_registry._routing_session()

        if self.permissions_created:
            return False, "Permissions already created"
        
        report_actions = [
            ('view', f'View report: {self.label or self.name}'),
            ('execute', f'Execute report: {self.label or self.name}'),
            ('export', f'Export data from report: {self.label or self.name}'),
            ('schedule', f'Schedule report: {self.label or self.name}'),
            ('edit', f'Edit report: {self.label or self.name}'),
            ('delete', f'Delete report: {self.label or self.name}'),
            ('share', f'Share report: {self.label or self.name}'),
        ]
        
        created_permissions = []
        
        for action, description in report_actions:
            permission_name = f"report:{self.slug}:{action}"
            
            existing = db_session.query(Permission).filter_by(name=permission_name).first()
            if not existing:
                success, result = Permission.create_permission(
                    service='report',
                    action=action,
                    resource=self.slug,
                    description=description
                )
                if success:
                    created_permissions.append(result)
        
        return True, created_permissions
    
    def update_permission_descriptions(self):
        """Update permission descriptions when report name changes"""
        db_session=db_registry._routing_session()
        
        permissions = db_session.query(Permission).filter(
            Permission.service == 'report',
            Permission.resource == self.slug
        ).all()
        
        for perm in permissions:
            action_descriptions = {
                'view': f'View report: {self.label or self.name}',
                'execute': f'Execute report: {self.label or self.name}',
                'export': f'Export data from report: {self.label or self.name}',
                'schedule': f'Schedule report: {self.label or self.name}',
                'edit': f'Edit report: {self.label or self.name}',
                'delete': f'Delete report: {self.label or self.name}',
                'share': f'Share report: {self.label or self.name}',
            }
            
            if perm.action in action_descriptions:
                perm.description = action_descriptions[perm.action]
        
        db_session.commit()
        return True, f"Updated {len(permissions)} permission descriptions"
    
    def delete_permissions(self):
        """Delete all permissions for this report"""
        db_session=db_registry._routing_session()
        
        permissions = db_session.query(Permission).filter(
            Permission.service == 'report',
            Permission.resource == self.slug
        ).all()
        
        # Also need to delete RolePermission entries
        if RolePermission:
            for perm in permissions:
                role_perms = db_session.query(RolePermission).filter(
                    RolePermission.permission_id == perm.id
                ).all()
                for rp in role_perms:
                    db_session.delete(rp)
        
        for perm in permissions:
            db_session.delete(perm)
        
        db_session.commit()
        return True, f"Deleted {len(permissions)} permissions"
    
    @classmethod
    def check_permission(cls, user_id, report_slug, action='view'):
        """Check if user has permission for specific report action"""
        db_session=db_registry._routing_session()
        from app._system.RBAC.permission_class import RbacPermissionChecker
        
        permission_name = f"report:{report_slug}:{action}"
        
        checker = RbacPermissionChecker()
        
        report = db_session.query(cls).filter_by(slug=report_slug).first()
        
        # Check if report exists and is published (unless user has edit permission)
        if report and not report.is_published and action in ['view', 'execute', 'export']:
            # Allow viewing unpublished reports only if user has edit permission
            edit_permission = f"report:{report_slug}:edit"
            can_edit = checker.check_permission(
                user_id=user_id,
                permission_name=edit_permission,
                resource_type='report',
                resource_name=report.name,
                resource_id=str(report.id),
                action_attempted='edit'
            )
            
            # Also check for admin edit_any permission
            if not can_edit:
                admin_edit_permission = "report:system:edit_any"
                can_edit = checker.check_permission(
                    user_id=user_id,
                    permission_name=admin_edit_permission,
                    resource_type='report',
                    resource_name=report.name,
                    action_attempted='edit'
                )
            
            if not can_edit:
                return False  # Deny access to unpublished reports
        
        has_permission = checker.check_permission(
            user_id=user_id,
            permission_name=permission_name,
            resource_type='report',
            resource_name=report.name if report else report_slug,
            resource_id=str(report.id) if report else None,
            action_attempted=action
        )
        
        # Public reports allow view/execute (only if published)
        if report and report.is_public and report.is_published and action in ['view', 'execute']:
            return True
        
        # Check admin permissions
        if action in ['edit', 'delete'] and not has_permission:
            admin_permission = f"report:system:{action}_any"
            has_permission = checker.check_permission(
                user_id=user_id,
                permission_name=admin_permission,
                resource_type='report',
                resource_name=report.name if report else report_slug,
                action_attempted=action
            )
        
        # Check view_all permission
        if action == 'view' and not has_permission:
            view_all_permission = "report:system:view_all"
            has_permission = checker.check_permission(
                user_id=user_id,
                permission_name=view_all_permission,
                resource_type='report',
                resource_name=report.name if report else report_slug,
                action_attempted=action
            )
        
        return has_permission
    
    @classmethod
    def get_user_reports(cls, user_id, include_unpublished=False):
        """Get all reports a user has permission to view"""
        db_session=db_registry._routing_session()
        
        if not all([RolePermission, Permission, User]):
            return []
        
        user = db_session.query(User).filter_by(id=user_id).first()
        if not user or not user.role_id:
            # Anonymous users only see published public reports
            return db_session.query(cls).filter(
                cls.is_public == True,
                cls.is_published == True
            ).all()
        
        # Check if user has edit permissions
        can_edit_any = False
        if include_unpublished:
            edit_any_perm = db_session.query(Permission).join(RolePermission).filter(
                RolePermission.role_id == user.role_id,
                Permission.name == 'report:system:edit_any'
            ).first()
            can_edit_any = bool(edit_any_perm)
        
        # Check view_all permission
        view_all_perm = db_session.query(Permission).join(RolePermission).filter(
            RolePermission.role_id == user.role_id,
            Permission.name == 'report:system:view_all'
        ).first()
        
        if view_all_perm:
            query = db_session.query(cls)
            if not can_edit_any and not include_unpublished:
                query = query.filter(cls.is_published == True)
            return query.all()
        
        # Get report permissions
        report_permissions = db_session.query(Permission).join(RolePermission).filter(
            RolePermission.role_id == user.role_id,
            Permission.service == 'report',
            Permission.action.in_(['view', 'edit'])
        ).all()
        
        # Separate view and edit permissions
        view_slugs = []
        edit_slugs = []
        for perm in report_permissions:
            if perm.resource and perm.resource != 'system':
                if perm.action == 'edit':
                    edit_slugs.append(perm.resource)
                elif perm.action == 'view':
                    view_slugs.append(perm.resource)
        
        # Build queries
        reports = []
        
        # Reports user can edit (see even if unpublished)
        if edit_slugs:
            edit_reports = db_session.query(cls).filter(
                cls.slug.in_(edit_slugs)
            ).all()
            reports.extend(edit_reports)
        
        # Reports user can only view (must be published)
        if view_slugs:
            view_reports = db_session.query(cls).filter(
                cls.slug.in_(view_slugs),
                cls.is_published == True
            ).all()
            reports.extend(view_reports)
        
        # Public reports (must be published)
        public_reports = db_session.query(cls).filter(
            cls.is_public == True,
            cls.is_published == True
        ).all()
        
        # Combine and deduplicate
        all_reports = {r.id: r for r in reports + public_reports}
        
        return list(all_reports.values())
    
    def assign_to_role(self,  role_id, actions=None):
        """Assign this report to a role with specified actions"""
        db_session=db_registry._routing_session()
        
        # Ensure permissions exist first
        if not self.permissions_created:
            self.create_permissions()
            self.permissions_created = True
            db_session.commit()
        
        if actions is None:
            actions = ['view', 'execute', 'export']
        
        granted = []
        failed = []
        
        for action in actions:
            permission_name = f"report:{self.slug}:{action}"
            success, result = RolePermission.grant_permission(role_id, permission_name)
            if success:
                granted.append(action)
            else:
                failed.append(f"{action}: {result}")
        
        if failed:
            return False, f"Granted: {', '.join(granted)}. Failed: {'; '.join(failed)}"
        
        return True, f"Granted actions: {', '.join(granted)}"
    
    def remove_from_role(self, role_id, actions=None):
        """Remove this report from a role"""
        db_session=db_registry._routing_session()
        
        if actions is None:
            actions = ['view', 'execute', 'export', 'schedule', 'edit', 'delete', 'share']
        
        revoked = []
        for action in actions:
            permission_name = f"report:{self.slug}:{action}"
            success, result = RolePermission.revoke_permission(
                db_session, role_id, permission_name
            )
            if success:
                revoked.append(action)
        
        return True, f"Revoked actions: {', '.join(revoked)}"
    
    def get_roles_with_access(self, action='view'):
        """Get all roles that have access to this report"""
        db_session=db_registry._routing_session()
        
        if not all([Permission, RolePermission, Role]):
            return []
        
        permission_name = f"report:{self.slug}:{action}"
        
        roles = db_session.query(Role).join(RolePermission).join(Permission).filter(
            Permission.name == permission_name
        ).all()
        
        return roles
    
    # Update the duplicate method in the Report model (report_model.py):

    def duplicate(self, new_name, new_slug=None):
        """Create a copy of this report with a new name and slug"""
        db_session=db_registry._routing_session()

        if not new_slug:
            new_slug = self.generate_slug(new_name)

        existing = db_session.query(Report).filter_by(slug=new_slug).first()
        if existing:
            return None, f"Report with slug '{new_slug}' already exists"

        new_report = Report(
            slug=new_slug,
            name=new_name,
            label=f"{self.label or self.name} (Copy)",
            query=self.query,
            description=self.description,
            connection_id=self.connection_id,
            model_id=self.model_id,
            category=self.category,
            tags=self.tags.copy() if self.tags else [],
            icon=self.icon,
            color=self.color,
            is_wide=self.is_wide,
            is_ajax=self.is_ajax,
            is_auto_run=self.is_auto_run,
            is_searchable=self.is_searchable,
            is_public=False,
            is_published=False,  # New reports start as draft
            is_download_csv=self.is_download_csv,
            is_download_xlsx=self.is_download_xlsx,
            is_model=self.is_model,
            options=self.options.copy() if self.options else self.get_default_options()
        )

        db_session.add(new_report)
        db_session.flush()

        from app.models import ReportColumn, ReportVariable, PageAction

        # Copy columns
        for col in self.columns:
            new_col = ReportColumn(
                report_id=new_report.id,
                name=col.name,
                label=col.label,
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
            db_session.add(new_col)

        # Copy variables
        for var in self.variables:
            new_var = ReportVariable(
                report_id=new_report.id,
                name=var.name,
                label=var.label,
                variable_type_id=var.variable_type_id,
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
            db_session.add(new_var)

        # Copy page actions
        for action in self.page_actions:
            new_action = PageAction(
                report_id=new_report.id,
                name=action.name,
                icon=action.icon,
                color=action.color,
                title=action.title,
                url=action.url,
                url_for=action.url_for,
                method=action.method,
                target=action.target,
                headers=action.headers.copy() if action.headers else {},
                payload=action.payload.copy() if action.payload else {},
                confirm=action.confirm,
                confirm_message=action.confirm_message,
                order_index=action.order_index
            )
            db_session.add(new_action)

        db_session.commit()

        # Create permissions
        new_report.create_permissions(db_session)
        new_report.permissions_created = True
        db_session.commit()

        return new_report, "Report duplicated successfully"
    
    def publish(self):
        """Publish this report"""
        db_session=db_registry._routing_session()
        self.is_published = True
        self.save()
        return True, "Report published successfully"
    
    def unpublish(self):
        """Unpublish this report (set to draft)"""
        db_session=db_registry._routing_session()
        self.is_published = False
        self.save()
        return True, "Report unpublished successfully"
    
    def __repr__(self):
        return f"<Report {self.slug} - {self.name}>"