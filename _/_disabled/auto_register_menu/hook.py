import re
import uuid
import datetime
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer, Text, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from flask import Flask, Blueprint, current_app, g
import inspect


from app._system.menu.menu_type_model import MenuType
from app._system.menu.menu_tier_model import MenuTier
from app._system.menu.menu_link_model import MenuLink
from app._system.menu.menu_quick_link_model import UserQuickLink
from app._system.role.role_permission_model import RoleMenuPermission
from app._system.role.role_model import Role
from app._system.user.user_model import User



# Now let's create the Flask hook for route registration

def register_menu_init(app):
    """
    Flask hook to register all routes as menu items.
    
    Args:
        app: The Flask application
        db_session: SQLAlchemy session
    """
    include_patterns = [r'*']
    exclude_patterns = [r'static\\..*', r'.*\\.\\.*', r'*_ajax']
    endpoint_exclude_patterns = [r'*_ajax']
    
    with app.app_context():
        db_session = app.db_session
        
                
        
        main_menu_type = db_session.query(MenuType).filter_by(name='ADMIN').first()
        if not main_menu_type:
            app.logger.error("Main menu type not found! Please ensure menu_types table is populated.")
            return
        
        # Track existing routes to handle deletion of unused routes
        existing_routes = set()
        
        # Process all blueprints
        for blueprint_name, blueprint in app.blueprints.items():
            # Skip blueprints we don't want to include
            if blueprint_name.startswith('_'):
                continue
                
            # Find or create the tier for this blueprint
            tier = db_session.query(MenuTier).filter_by(
                name=blueprint_name.upper(),
                menu_type_uuid=main_menu_type.uuid
            ).first()
            
            if not tier:
                # Get parent tier (ROOT)
                root_tier = db_session.query(MenuTier).filter_by(
                    name='ADMIN',
                    menu_type_uuid=main_menu_type.uuid
                ).first()
                
                if not root_tier:
                    # Create root tier if it doesn't exist
                    root_tier = MenuTier(
                        name='ADMIN',
                        display='Main Menu',
                        slug='main-menu',
                        menu_type_uuid=main_menu_type.uuid,
                        active=True,
                        visible=True
                    )
                    db_session.add(root_tier)
                    db_session.flush()
                
                # Create the blueprint tier
                display_name = ' '.join(word.capitalize() for word in blueprint_name.split('_'))
                tier = MenuTier(
                    name=blueprint_name.upper(),
                    display=display_name,
                    slug=blueprint_name.lower(),
                    menu_type_uuid=main_menu_type.uuid,
                    parent_uuid=root_tier.uuid,
                    active=True,
                    visible=True
                )
                db_session.add(tier)
                db_session.flush()
            
            # Process all routes in this blueprint
            for rule in app.url_map.iter_rules():
                # Check if this route belongs to this blueprint
                if rule.endpoint.startswith(blueprint_name + '.'):
                    route_name = rule.endpoint.split('.')[1]
                    url = str(rule)
                    
                    if route_name.endswith('_ajax'):
                        continue
                    
                    if 'static' in url:
                        continue
                    
                    # Skip routes with parameters if they're the default routes
                    if '<' in url and route_name in ('get', 'post', 'put', 'delete', 'patch'):
                        continue
                    
                    # Format display name from route name
                    display_name = f"{blueprint_name} {route_name}"
                    display_name=' '.join(word.capitalize() for word in display_name.split('_'))
                    
                    # Check if we already have this route
                    menu_link = db_session.query(MenuLink).filter_by(
                        endpoint=rule.endpoint
                    ).first()
                    
                    if menu_link:
                        # Update existing route
                        menu_link.url = url
                        menu_link.blueprint_name = blueprint_name
                        # Don't update name/display to preserve customizations
                    else:
                        # Create new route
                        menu_link = MenuLink(
                            name=display_name.replace(' ','_').lower(),
                            display=display_name,
                            url=url,
                            tier_uuid=tier.uuid,
                            blueprint_name=blueprint_name,
                            endpoint=rule.endpoint,
                            active=True,
                            visible=True
                        )
                        db_session.add(menu_link)
                    
                    # Track this endpoint
                    existing_routes.add(rule.endpoint)
            
        # Find routes that no longer exist and mark them inactive
        orphaned_routes = db_session.query(MenuLink).filter(
            MenuLink.endpoint.isnot(None),
            ~MenuLink.endpoint.in_(existing_routes)
        ).all()
        
        for route in orphaned_routes:
            route.active = False

        db_session.commit()
        
        # 3. Grant ADMIN role permissions to all menu items
        # Flush first to ensure all links have UUIDs
        db_session.flush()
        

        admin_role = db_session.query(Role).filter_by(name='admin').first()
        if not admin_role:
            admin_role = Role(
                name='admin',
                display='Administrator',
                description='Full system administration access',
                active=True
            )
            db_session.add(admin_role)
            db_session.flush()
            app.logger.info("Created ADMIN role")
        

        # Get all active menu links
        active_links = db_session.query(MenuLink).filter_by(active=True).all()
        
        # Assign permissions for each link to the ADMIN role
        for link in active_links:
            # Check if permission already exists
            permission = db_session.query(RoleMenuPermission).filter_by(
                role_uuid=admin_role.uuid,
                menu_link_uuid=link.uuid
            ).first()
            try:
                if not permission:
                    permission = RoleMenuPermission(
                        role_uuid=admin_role.uuid,
                        menu_link_uuid=link.uuid,
                    )
                    db_session.add(permission)
                    app.logger.info(f"Added permission for link: {link.name} ({link.uuid})")
            except Exception as e:
                app.logger.error(f"Failed to add permission for link {link.name} ({link.uuid}): {str(e)}")


        db_session.commit()
        db_session.flush()

        app.logger.info(f"Menu system updated: {len(existing_routes)} active routes, {len(orphaned_routes)} deactivated")

