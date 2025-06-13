import uuid
from sqlalchemy import and_
from typing import List, Dict, Optional, Union

from app.models import Menu, MenuTier, MenuLink, UserQuickLink, RoleMenuPermission, Permission, Role, User

class MenuBuilder:
    def __init__(self, db_session):
        """
        Initialize the MenuBuilder with a database session.

        Args:
            db_session: SQLAlchemy session object
        """
        self.db_session = db_session

    def get_menu_structure(self, menu_name="ADMIN", user_uuid=None):
        """
        Build a complete menu structure from the database.

        Args:
            menu_name: Name of the menu to build
            user_uuid: Optional UUID of user for permission filtering (can be string or UUID)

        Returns:
            Dictionary containing the menu structure
        """
        # Convert string UUID to UUID object if needed
        if user_uuid and isinstance(user_uuid, str):
            user_uuid = uuid.UUID(user_uuid)

        menu = self.db_session.query(Menu).filter_by(name=menu_name).first()
        if not menu:
            return None

        # Get root tiers (those without parents or with parent_uuid=None)
        root_tiers = self.db_session.query(MenuTier).filter(
            and_(
                MenuTier.menu_uuid == menu.uuid,
                MenuTier.parent_uuid == None,
                MenuTier.active == True,
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
            "tiers": [self._build_tier_structure(tier, user_uuid) for tier in root_tiers]
        }

        return menu_structure

    def _build_tier_structure(self, tier, user_uuid=None):
        """
        Recursively build the structure for a tier and its children.

        Args:
            tier: MenuTier object
            user_uuid: Optional UUID of user for permission filtering

        Returns:
            Dictionary representing the tier structure
        """
        tier_structure = {
            "uuid": str(tier.uuid),
            "name": tier.name,
            "display": tier.display,
            "slug": tier.slug,
            "icon": tier.icon,
            "position": tier.position,
            "children": [],
            "links": []
        }

        # Add child tiers
        children = [child for child in tier.children if child.active and child.visible]
        for child in sorted(children, key=lambda x: x.position):
            tier_structure["children"].append(self._build_tier_structure(child, user_uuid))

        # Add links
        links_query = self.db_session.query(MenuLink).filter(
            MenuLink.tier_uuid == tier.uuid,
            MenuLink.active == True,
            MenuLink.visible == True
        ).order_by(MenuLink.position)

        # If user_uuid is provided, filter by permissions
        if user_uuid:
            # First get the user's role_uuid
            user = self.db_session.query(User).filter(User.uuid == user_uuid).first()
            if user:
                # Then filter links by the role's permissions
                links_query = links_query.join(
                    RoleMenuPermission,
                    MenuLink.uuid == RoleMenuPermission.menu_link_uuid
                ).filter(
                    RoleMenuPermission.role_uuid == user.role_uuid
                )

        links = links_query.all()

        for link in links:
            link_structure = {
                "uuid": str(link.uuid),
                "name": link.name,
                "display": link.display,
                "url": link.url,
                "icon": link.icon,
                "description": link.description,
                "position": link.position,
                "new_tab": link.new_tab,
                "has_submenu": link.has_submenu
            }
            tier_structure["links"].append(link_structure)

        return tier_structure

    def get_user_quick_links(self, user_uuid):
        """
        Get a user's quick links.

        Args:
            user_uuid: UUID of the user

        Returns:
            List of MenuLink objects
        """
        quick_links = self.db_session.query(MenuLink).join(
            UserQuickLink,
            and_(
                UserQuickLink.menu_link_uuid == MenuLink.uuid,
                UserQuickLink.user_uuid == user_uuid
            )
        ).filter(
            MenuLink.active == True
        ).order_by(UserQuickLink.position).all()

        return quick_links

    def add_user_quick_link(self, user_uuid, menu_link_uuid, position=None):
        """
        Add a quick link for a user.

        Args:
            user_uuid: UUID of the user
            menu_link_uuid: UUID of the menu link
            position: Optional position for the quick link

        Returns:
            Newly created UserQuickLink or None if it already exists
        """
        # Check if the quick link already exists
        existing = self.db_session.query(UserQuickLink).filter_by(
            user_uuid=user_uuid,
            menu_link_uuid=menu_link_uuid
        ).first()

        if existing:
            return None

        # Determine position if not provided
        if position is None:
            max_position = self.db_session.query(UserQuickLink).filter_by(
                user_uuid=user_uuid
            ).order_by(UserQuickLink.position.desc()).first()

            if max_position:
                position = max_position.position + 1
            else:
                position = 0

        # Create new quick link
        quick_link = UserQuickLink(
            user_uuid=user_uuid,
            menu_link_uuid=menu_link_uuid,
            position=position
        )

        self.db_session.add(quick_link)
        self.db_session.commit()

        return quick_link

    def remove_user_quick_link(self, user_uuid, menu_link_uuid):
        """
        Remove a quick link for a user.

        Args:
            user_uuid: UUID of the user
            menu_link_uuid: UUID of the menu link

        Returns:
            True if removed, False if not found
        """
        quick_link = self.db_session.query(UserQuickLink).filter_by(
            user_uuid=user_uuid,
            menu_link_uuid=menu_link_uuid
        ).first()

        if quick_link:
            self.db_session.delete(quick_link)
            self.db_session.commit()
            return True

        return False