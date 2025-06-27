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

class MenuBuilder:
    
    __depends_on__ = [ 'Menu','MenuTier','MenuLink','UserQuickLink','RolePermission','User' ]
    def __init__(self, db_session):
        """
        Initialize the MenuBuilder with a database session.

        Args:
            db_session: SQLAlchemy session object
        """
        self.db_session = db_session

    def get_menu_structure(self, menu_name="ADMIN", user_id=None):
       """
       Build a complete menu structure from the database.

       Args:
           menu_name: Name of the menu to build
           user_id: Optional UUID of user for permission filtering (can be string or UUID)

       Returns:
           Dictionary containing the menu structure
       """
       # Convert string UUID to UUID object if needed
       if user_id and isinstance(user_id, str):
           user_id = uuid.UUID(user_id)

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

       # If user_id is provided, filter by permissions
       if user_id:
           user = self.db_session.query(User).filter(User.id == user_id).first()
           if user:
               links_query = links_query.join(
                   RolePermission,
                   MenuLink.id == RolePermission.menu_link_id
               ).filter(
                   RolePermission.role_id == user.role_id
               )

       links = links_query.all()

       # Get child tiers
       child_tiers = [child for child in tier.children if child.is_active and child.visible]
       child_tiers.sort(key=lambda x: x.position)

       # Build items list combining links and child tiers
       items = []
       
       # Add links as items
       for link in links:
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