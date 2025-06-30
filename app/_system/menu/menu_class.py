import uuid
from pprint import pprint
from sqlalchemy import and_
from typing import List, Dict, Optional, Union

from app.models import Menu
from app.models import User
from app.models import MenuTier
from app.models import MenuLink
from app.models import UserQuickLink
from app.models import RolePermission
from app.models import Permission
from app.classes import RbacPermissionChecker


from app.register.database import db_registry

class MenuBuilder:

    __depends_on__ = [ 'Menu','MenuTier','MenuLink','UserQuickLink','RolePermission','User','Permission','RbacPermissionChecker' ]
    
    def __init__(self):
        """
        Initialize the MenuBuilder 
        """
        self.rbac_checker = RbacPermissionChecker()
        self.db_session=db_registry._routing_session()

    def get_available_menu_names(self, user_id=None):
        """
        Get list of menu names available to a user.
        
        Args:
            user_id: Optional UUID of user for permission filtering
            
        Returns:
            List of menu names the user can access
        """
        # Convert string UUID to UUID object if needed
        if user_id and isinstance(user_id, str):
            user_id = uuid.UUID(user_id)
        
        # Get all menus
        all_menus = self.db_session.query(Menu).filter(
            Menu.is_active == True
        ).all()
        
        if not user_id:
            # No user specified, return all active menus
            return [menu.name for menu in all_menus]
        
        # Check permissions for each menu
        available_menus = []
        for menu in all_menus:
            permission_name = f"menu:{menu.name.lower()}:view"
            
            # Check if user has permission
            if self._user_has_menu_permission(user_id, menu.name):
                available_menus.append(menu.name)
        
        return available_menus

    def get_available_menus(self, user_id=None):
        """
        Get detailed list of menus available to a user.
        
        Args:
            user_id: Optional UUID of user for permission filtering
            
        Returns:
            List of menu dictionaries with details
        """
        # Convert string UUID to UUID object if needed
        if user_id and isinstance(user_id, str):
            user_id = uuid.UUID(user_id)
        
        # Get all menus
        all_menus = self.db_session.query(Menu).filter(
            Menu.is_active == True
        ).all()
        available_menus = []
        if user_id:
            for menu in all_menus:
                if self._user_has_menu_permission(user_id, menu.name):
                    available_menus.append({
                        'id': str(menu.id),
                        'name': menu.name,
                        'slug':menu.slug,
                        'icon':menu.icon,
                        'display': menu.display,
                        'description': menu.description
                    })
            
        return available_menus

    def get_menu_structure(self, menu_name="ADMIN", user_id=None):
        """
        Build a complete menu structure from the database.

        Args:
            menu_name: Name of the menu to build
            user_id: Optional UUID of user for permission filtering (can be string or UUID)

        Returns:
            Dictionary containing the menu structure or None if no access
        """
        # Convert string UUID to UUID object if needed
        if user_id and isinstance(user_id, str):
            user_id = uuid.UUID(user_id)
        
        # First check if user has access to this menu
        if user_id and not self._user_has_menu_permission(user_id, menu_name):
            return None  # User doesn't have permission to view this menu
        
        menu = self.db_session.query(Menu).filter_by(name=menu_name).first()
        if not menu:
            return None

        # Get root tiers (those without parents or with parent_id=None)
        root_tiers = self.db_session.query(MenuTier).filter(
            and_(
                MenuTier.menu_id == menu.id,
                MenuTier.parent_id == None,
                MenuTier.is_active == True,
                MenuTier.visible == True
            )
        ).order_by(MenuTier.position).all()

        # Build the menu structure recursively
        menu_structure = {
            "menu_type": {
                "name": menu.name,
                "display": menu.display,
                "description": menu.description
            },
            "items": []
        }

        # Build nested structure
        for tier in root_tiers:
            tier_dict = self._build_tier_nested(tier, user_id)
            if tier_dict:  # Only add if tier has content or is visible
                menu_structure["items"].append(tier_dict)

        # pprint(menu_structure)
        return menu_structure

    def _user_has_menu_permission(self, user_id, menu_name):
        """
        Check if user has permission to access a menu.
        
        Args:
            user_id: UUID of the user
            menu_name: Name of the menu
            
        Returns:
            bool: True if user has access
        """
        permission_name = f"menu:{menu_name.lower()}:view"
        
        has_access = self.rbac_checker.check_permission(
            user_id=user_id,
            permission_name=permission_name,
        )
        return has_access
    
    def _build_tier_nested(self, tier, user_id=None):
        """
        Recursively build nested structure for a tier.

        Args:
            tier: MenuTier object
            user_id: Optional UUID of user for permission filtering

        Returns:
            Dictionary representing the tier with nested items
        """
        # Get links for this tier
        links_query = self.db_session.query(MenuLink).filter(
            MenuLink.tier_id == tier.id,
            MenuLink.is_active == True,
            MenuLink.visible == True
        ).order_by(MenuLink.position)

        # For now, we'll show all links if user has menu access
        # You can later add per-link permission checking here
        links = links_query.all()

        # Get child tiers
        child_tiers = [child for child in tier.children if child.is_active and child.visible]
        child_tiers.sort(key=lambda x: x.position)

        # Build items list combining links and child tiers
        items = []

        # Add links as items
        for link in links:
            # Optional: Add per-link permission checking here
            # permission_name = f"menu:link:{link.name.lower()}:view"
            # if user_id and not self.rbac_checker.check_permission(user_id, permission_name):
            #     continue
            
            link_item = {
                "type": "link",
                "id": str(link.id),
                "name": link.name,
                "display": link.display,
                "url": link.url,
                "url_for": link.url_for,
                "icon": link.icon,
                "description": link.description,
                "position": link.position,
                "new_tab": link.new_tab,
                "has_submenu": link.has_submenu
            }
            items.append(link_item)

        # Add child tiers as nested items
        for child_tier in child_tiers:
            child_dict = self._build_tier_nested(child_tier, user_id)
            if child_dict:
                items.append(child_dict)

        # Create tier dictionary
        tier_dict = {
            "type": "tier",
            "id": str(tier.id),
            "name": tier.name,
            "display": tier.display,
            "slug": tier.slug,
            "icon": tier.icon,
            "position": tier.position,
            "items": items
        }

        return tier_dict

    def get_user_quick_links(self, user_id):
        """
        Get a user's quick links.

        Args:
            user_id: UUID of the user

        Returns:
            List of MenuLink objects
        """
        quick_links = self.db_session.query(MenuLink).join(
            UserQuickLink,
            and_(
                UserQuickLink.menu_link_id == MenuLink.id,
                UserQuickLink.user_id == user_id
            )
        ).filter(
            MenuLink.is_active == True
        ).order_by(UserQuickLink.position).all()

        return quick_links

    def add_user_quick_link(self, user_id, menu_link_id, position=None):
        """
        Add a quick link for a user.

        Args:
            user_id: UUID of the user
            menu_link_id: UUID of the menu link
            position: Optional position for the quick link

        Returns:
            Newly created UserQuickLink or None if it already exists
        """
        # Check if the quick link already exists
        existing = self.db_session.query(UserQuickLink).filter_by(
            user_id=user_id,
            menu_link_id=menu_link_id
        ).first()

        if existing:
            return None

        # Determine position if not provided
        if position is None:
            max_position = self.db_session.query(UserQuickLink).filter_by(
                user_id=user_id
            ).order_by(UserQuickLink.position.desc()).first()

            if max_position:
                position = max_position.position + 1
            else:
                position = 0

        # Create new quick link
        quick_link = UserQuickLink(
            user_id=user_id,
            menu_link_id=menu_link_id,
            position=position
        )

        self.db_session.add(quick_link)
        self.db_session.commit()

        return quick_link

    def remove_user_quick_link(self, user_id, menu_link_id):
        """
        Remove a quick link for a user.

        Args:
            user_id: UUID of the user
            menu_link_id: UUID of the menu link

        Returns:
            True if removed, False if not found
        """
        quick_link = self.db_session.query(UserQuickLink).filter_by(
            user_id=user_id,
            menu_link_id=menu_link_id
        ).first()

        if quick_link:
            self.db_session.delete(quick_link)
            self.db_session.commit()
            return True

        return False