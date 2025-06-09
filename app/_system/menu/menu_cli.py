#!/usr/bin/env python3
"""
Menu System CLI Management Tool
"""

import argparse
import sys
from sqlalchemy import text

# Add app path
sys.path.append('/web/temuragi')
from app.base.cli import BaseCLI

CLI_DESCRIPTION = "Menu configuration"

class MenuCLI(BaseCLI):
    def __init__(self, verbose=False, show_icons=True, table_format=None):
        """Initialize CLI with database connection and logging"""
        # Initialize parent with logging and database
        super().__init__(
            name="menu",
            log_file="logs/menu_cli.log",
            connect_db=True,
            verbose=verbose,
            show_icons=show_icons,
            table_format=table_format
        )

        self.log_info("Starting menu CLI initialization")

        try:
            # Get models from registry
            self.menu_model = self.get_model('Menu')
            self.menu_tier_model = self.get_model('MenuTier')
            self.menu_link_model = self.get_model('MenuLink')
            self.user_quick_link_model = self.get_model('UserQuickLink')
            
            if not all([self.menu_model, self.menu_tier_model, self.menu_link_model]):
                self.log_error("Required menu models not found in registry")
                raise Exception("Required menu models not found in registry")

            self.log_info("Menu models loaded successfully")

        except Exception as e:
            self.log_error(f"Failed to initialize menu CLI: {e}")
            raise

    def show_menu_status(self):
        """Show comprehensive menu system status"""
        self.log_info("Showing menu system status")

        try:
            self.output_info("Menu System Status")

            # Get counts using model queries
            menu_count = self.session.query(self.menu_model).count()
            tier_count = self.session.query(self.menu_tier_model).count()
            link_count = self.session.query(self.menu_link_model).count()
            
            quick_link_count = 0
            if self.user_quick_link_model:
                quick_link_count = self.session.query(self.user_quick_link_model).count()

            headers = ['Component', 'Count']
            rows = [
                ['Menu Types', f"{menu_count:,}"],
                ['Menu Tiers', f"{tier_count:,}"],
                ['Menu Links', f"{link_count:,}"],
                ['User Quick Links', f"{quick_link_count:,}"]
            ]

            total_records = menu_count + tier_count + link_count + quick_link_count

            self.output_info("Menu System Counts:")
            self.output_table(rows, headers=headers)
            self.output_info(f"Total menu records: {total_records:,}")

            # Menu types summary
            self._show_menu_types_summary()

            # Menu hierarchy summary
            self._show_menu_hierarchy_summary()

            return 0

        except Exception as e:
            self.log_error(f"Error showing menu status: {e}")
            self.output_error(f"Error showing menu status: {e}")
            return 1

    def _show_menu_types_summary(self):
        """Show summary of menu types"""
        self.log_debug("Showing menu types summary")

        try:
            self.output_info("Menu Types Summary:")
            
            # Get all menu types with their related counts
            menu_types = self.session.query(self.menu_model).all()
            
            if menu_types:
                headers = ['Type', 'Description', 'Active', 'Tiers', 'Links']
                rows = []
                
                for menu_type in menu_types:
                    # Get tier count for this menu type
                    tier_count = self.session.query(self.menu_tier_model).filter_by(
                        menu_type_uuid=menu_type.uuid
                    ).count()
                    
                    # Get link count through tiers
                    link_count = 0
                    for tier in menu_type.tiers:
                        link_count += len(tier.links)
                    
                    status = "✓" if getattr(menu_type, 'is_active', True) else "✗"
                    desc_short = menu_type.description[:30] + ('...' if len(menu_type.description or '') > 30 else '') if menu_type.description else ''
                    
                    rows.append([menu_type.name, desc_short, status, tier_count, link_count])

                self.output_table(rows, headers=headers)
            else:
                self.output_warning("No menu types found")

        except Exception as e:
            self.log_error(f"Error loading menu types: {e}")
            self.output_error(f"Error loading menu types: {e}")

    def _show_menu_hierarchy_summary(self):
        """Show menu hierarchy summary using model relationships"""
        self.log_debug("Showing menu hierarchy summary")

        try:
            self.output_info("Menu Hierarchy Summary:")
            
            # Get root tiers (no parent)
            root_tiers = self.session.query(self.menu_tier_model).filter_by(parent_uuid=None).all()
            
            if not root_tiers:
                self.output_warning("No menu hierarchy found")
                return

            # Calculate hierarchy depth using recursive traversal
            def get_max_depth(tier, current_depth=0):
                if not tier.children:
                    return current_depth
                return max(get_max_depth(child, current_depth + 1) for child in tier.children)

            max_depth = 0
            level_counts = {}
            
            # Count tiers at each level
            def count_levels(tiers, level=0):
                nonlocal max_depth
                max_depth = max(max_depth, level)
                
                if level not in level_counts:
                    level_counts[level] = 0
                level_counts[level] += len(tiers)
                
                for tier in tiers:
                    if tier.children:
                        count_levels(tier.children, level + 1)

            count_levels(root_tiers)

            self.output_info(f"Maximum depth: {max_depth} levels")

            if level_counts:
                headers = ['Level', 'Tier Count', 'Description']
                rows = []
                for level in sorted(level_counts.keys()):
                    count = level_counts[level]
                    desc = "Root tiers" if level == 0 else f"Level {level} sub-tiers"
                    rows.append([level, count, desc])

                self.output_table(rows, headers=headers)

        except Exception as e:
            self.log_error(f"Error loading hierarchy: {e}")
            self.output_error(f"Error loading hierarchy: {e}")

    def list_menu_types(self):
        """List all menu types with details"""
        self.log_info("Listing menu types")

        try:
            self.output_info("Menu Types")

            menu_types = self.session.query(self.menu_model).order_by(self.menu_model.name).all()

            if not menu_types:
                self.output_warning("No menu types found")
                return 0

            headers = ['Name', 'Status', 'Description', 'Tiers', 'UUID', 'Created']
            rows = []

            for menu_type in menu_types:
                # Count tiers for this menu type
                tier_count = len(menu_type.tiers)
                
                status = "ACTIVE" if getattr(menu_type, 'is_active', True) else "INACTIVE"
                desc_short = menu_type.description[:40] + ('...' if len(menu_type.description or '') > 40 else '') if menu_type.description else ''
                uuid_short = str(menu_type.uuid)[:8] + '...'
                created_short = menu_type.created_at.strftime('%Y-%m-%d') if menu_type.created_at else ''
                
                rows.append([menu_type.name, status, desc_short, tier_count, uuid_short, created_short])

            self.output_table(rows, headers=headers)
            return 0

        except Exception as e:
            self.log_error(f"Error listing menu types: {e}")
            self.output_error(f"Error listing menu types: {e}")
            return 1

    def show_menu_tree(self, menu_type_name=None):
        """Show menu hierarchy as a tree structure using model relationships"""
        self.log_info(f"Showing menu tree for: {menu_type_name or 'all types'}")

        try:
            if menu_type_name:
                self.output_info(f"Menu Tree for '{menu_type_name}'")
                # Filter by specific menu type
                menu_types = self.session.query(self.menu_model).filter_by(name=menu_type_name).all()
                if not menu_types:
                    self.output_error(f"Menu type '{menu_type_name}' not found")
                    return 1
            else:
                self.output_info("Complete Menu Tree (All Types)")
                menu_types = self.session.query(self.menu_model).order_by(self.menu_model.name).all()

            if not menu_types:
                self.output_warning("No menu types found")
                return 0

            def print_tier_tree(tier, level=0):
                """Recursively print tier hierarchy"""
                indent = "  " * level
                link_count = len(tier.links)
                link_info = f" ({link_count} links)" if link_count > 0 else ""
                print(f"{indent}├─ {tier.name}{link_info}")
                
                # Print children
                for child in sorted(tier.children, key=lambda x: x.position):
                    print_tier_tree(child, level + 1)

            for menu_type in menu_types:
                print(f"\n{menu_type.name}:")
                print("-" * (len(menu_type.name) + 1))
                
                # Get root tiers for this menu type
                root_tiers = [tier for tier in menu_type.tiers if tier.parent_uuid is None]
                root_tiers.sort(key=lambda x: x.position)
                
                if root_tiers:
                    for tier in root_tiers:
                        print_tier_tree(tier)
                else:
                    print("  No tiers found")

            return 0

        except Exception as e:
            self.log_error(f"Error showing menu tree: {e}")
            self.output_error(f"Error showing menu tree: {e}")
            return 1

    def create_menu_type(self, name, description, is_active=True):
        """Create a new menu type"""
        self.log_info(f"Creating menu type: {name}")

        try:
            # Check if it already exists
            existing = self.session.query(self.menu_model).filter_by(name=name).first()
            if existing:
                self.output_error(f"Menu type '{name}' already exists")
                return 1

            # Create new menu type
            menu_type = self.menu_model(
                name=name,
                display=description,
                description=description
            )

            self.session.add(menu_type)
            self.session.commit()
            
            self.output_success(f"Created menu type '{name}' with UUID: {menu_type.uuid}")
            return 0

        except Exception as e:
            self.log_error(f"Error creating menu type: {e}")
            self.output_error(f"Error creating menu type: {e}")
            self.session.rollback()
            return 1

    def create_menu_tier(self, name, menu_type_name, parent_tier_name=None, sort_order=100):
        """Create a new menu tier"""
        self.log_info(f"Creating menu tier: {name} in {menu_type_name}")

        try:
            # Get menu type
            menu_type = self.session.query(self.menu_model).filter_by(name=menu_type_name).first()
            if not menu_type:
                self.output_error(f"Menu type '{menu_type_name}' not found")
                return 1

            # Get parent tier UUID if specified
            parent_uuid = None
            if parent_tier_name:
                parent_tier = self.session.query(self.menu_tier_model).filter_by(
                    name=parent_tier_name,
                    menu_type_uuid=menu_type.uuid
                ).first()
                
                if not parent_tier:
                    self.output_error(f"Parent tier '{parent_tier_name}' not found in menu type '{menu_type_name}'")
                    return 1
                
                parent_uuid = parent_tier.uuid

            # Check if tier already exists
            existing = self.session.query(self.menu_tier_model).filter_by(
                name=name,
                menu_type_uuid=menu_type.uuid
            ).first()

            if existing:
                self.output_error(f"Menu tier '{name}' already exists in menu type '{menu_type_name}'")
                return 1

            # Create slug from name
            slug = name.lower().replace(' ', '_').replace('-', '_')

            # Create new tier
            tier = self.menu_tier_model(
                name=name,
                display=name,
                slug=slug,
                menu_type_uuid=menu_type.uuid,
                parent_uuid=parent_uuid,
                position=sort_order
            )

            self.session.add(tier)
            self.session.commit()

            parent_info = f" under '{parent_tier_name}'" if parent_tier_name else " as root tier"
            self.output_success(f"Created menu tier '{name}'{parent_info} in '{menu_type_name}'")
            self.output_info(f"UUID: {tier.uuid}")
            return 0

        except Exception as e:
            self.log_error(f"Error creating menu tier: {e}")
            self.output_error(f"Error creating menu tier: {e}")
            self.session.rollback()
            return 1

    def cleanup_menu_data(self, include_types=False):
        """Clean up menu system data"""
        self.log_info(f"Starting menu cleanup, include_types={include_types}")

        try:
            if include_types:
                self.output_info("Mode: Complete cleanup (including menu types)")
            else:
                self.output_info("Mode: Preserve menu types")

            # Step 1: Remove user quick links
            self.output_info("1. Removing user quick links...")
            if self.user_quick_link_model:
                count = self.session.query(self.user_quick_link_model).count()
                self.session.query(self.user_quick_link_model).delete()
                self.log_info(f"Deleted {count} user quick links")
            else:
                result = self.session.execute(text("DELETE FROM user_quick_links"))
                count = result.rowcount
                self.log_info(f"Deleted {count} user quick links")

            # Step 2: Remove menu links
            self.output_info("2. Removing menu links...")
            count = self.session.query(self.menu_link_model).count()
            self.session.query(self.menu_link_model).delete()
            self.log_info(f"Deleted {count} menu links")

            # Step 3: Remove menu tiers (hierarchical)
            self.output_info("3. Removing menu tiers...")
            self._delete_tiers_hierarchical()

            # Step 4: Optionally remove menu types
            if include_types:
                self.output_info("4. Removing menu types...")
                count = self.session.query(self.menu_model).count()
                self.session.query(self.menu_model).delete()
                self.log_info(f"Deleted {count} menu types")
            else:
                self.output_info("4. Menu types preserved")

            self.session.commit()
            cleanup_type = "Complete" if include_types else "Partial"
            self.output_success(f"{cleanup_type} menu system cleanup completed!")
            return 0

        except Exception as e:
            self.log_error(f"Error during cleanup: {e}")
            self.output_error(f"Error during cleanup: {e}")
            self.session.rollback()
            return 1

    def _delete_tiers_hierarchical(self):
        """Delete menu tiers in hierarchical order using model relationships"""
        try:
            # Use model relationships to delete in proper order
            # SQLAlchemy will handle the cascade properly with the relationships
            deleted_count = 0
            
            # Get all tiers and let SQLAlchemy handle the cascade deletion
            all_tiers = self.session.query(self.menu_tier_model).all()
            
            # Delete from deepest level first by sorting by hierarchy
            def get_tier_depth(tier, depth=0):
                if not tier.children:
                    return depth
                return max(get_tier_depth(child, depth + 1) for child in tier.children)

            # Sort tiers by depth (deepest first)
            tiers_with_depth = [(tier, get_tier_depth(tier)) for tier in all_tiers]
            tiers_with_depth.sort(key=lambda x: x[1], reverse=True)
            
            # Delete tiers
            for tier, depth in tiers_with_depth:
                # Check if tier still exists (might have been deleted by cascade)
                if self.session.query(self.menu_tier_model).filter_by(uuid=tier.uuid).first():
                    self.session.delete(tier)
                    deleted_count += 1

            self.log_info(f"Deleted {deleted_count} tiers hierarchically")

        except Exception as e:
            self.log_warning(f"Error in hierarchical deletion: {e}")
            # Fallback: delete all tiers
            count = self.session.query(self.menu_tier_model).count()
            self.session.query(self.menu_tier_model).delete()
            self.log_info(f"Fallback: Deleted {count} tiers")

    def find_menu_item(self, search_term):
        """Find menu items by search term"""
        self.log_info(f"Finding menu items: {search_term}")

        try:
            # Search in menu types
            menu_types = self.session.query(self.menu_model).filter(
                self.menu_model.name.ilike(f'%{search_term}%') |
                self.menu_model.description.ilike(f'%{search_term}%')
            ).all()

            # Search in menu tiers
            menu_tiers = self.session.query(self.menu_tier_model).filter(
                self.menu_tier_model.name.ilike(f'%{search_term}%') |
                self.menu_tier_model.display.ilike(f'%{search_term}%')
            ).all()

            # Search in menu links
            menu_links = self.session.query(self.menu_link_model).filter(
                self.menu_link_model.name.ilike(f'%{search_term}%') |
                self.menu_link_model.display.ilike(f'%{search_term}%') |
                self.menu_link_model.url.ilike(f'%{search_term}%')
            ).all()

            if not any([menu_types, menu_tiers, menu_links]):
                self.output_warning(f"No menu items found matching: {search_term}")
                return 1

            if menu_types:
                self.output_info("Menu Types Found:")
                headers = ['Name', 'Description', 'UUID']
                rows = []
                for menu_type in menu_types:
                    rows.append([
                        menu_type.name,
                        menu_type.description or '',
                        str(menu_type.uuid)[:8] + '...'
                    ])
                self.output_table(rows, headers=headers)

            if menu_tiers:
                self.output_info("Menu Tiers Found:")
                headers = ['Name', 'Display', 'Slug', 'UUID']
                rows = []
                for tier in menu_tiers:
                    rows.append([
                        tier.name,
                        tier.display,
                        tier.slug,
                        str(tier.uuid)[:8] + '...'
                    ])
                self.output_table(rows, headers=headers)

            if menu_links:
                self.output_info("Menu Links Found:")
                headers = ['Name', 'Display', 'URL', 'UUID']
                rows = []
                for link in menu_links:
                    rows.append([
                        link.name,
                        link.display,
                        link.url[:40] + ('...' if len(link.url) > 40 else ''),
                        str(link.uuid)[:8] + '...'
                    ])
                self.output_table(rows, headers=headers)

            return 0

        except Exception as e:
            self.log_error(f"Error finding menu items: {e}")
            self.output_error(f"Error finding menu items: {e}")
            return 1

    def close(self):
        """Clean up database session"""
        self.log_debug("Closing menu CLI")
        super().close()


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(description='Menu System CLI')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging (debug level)')
    parser.add_argument('--no-icons', action='store_true', help='Disable icons in output')
    parser.add_argument('--table-format', choices=['simple', 'grid', 'pipe', 'orgtbl', 'rst', 'mediawiki', 'html', 'latex'],
                       help='Override table format (default from config)')

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Status and listing
    subparsers.add_parser('status', help='Show comprehensive menu system status')
    subparsers.add_parser('list-types', help='List all menu types with details')

    tree_parser = subparsers.add_parser('show-tree', help='Show menu hierarchy tree')
    tree_parser.add_argument('--type', help='Show tree for specific menu type only')

    # Find command
    find_parser = subparsers.add_parser('find', help='Find menu items by search term')
    find_parser.add_argument('search', help='Search term')

    # Create commands
    create_parser = subparsers.add_parser('create', help='Create menu components')
    create_subs = create_parser.add_subparsers(dest='create_type')

    type_parser = create_subs.add_parser('type', help='Create menu type')
    type_parser.add_argument('name', help='Menu type name')
    type_parser.add_argument('description', help='Menu type description')
    type_parser.add_argument('--inactive', action='store_true', help='Create as inactive')

    tier_parser = create_subs.add_parser('tier', help='Create menu tier')
    tier_parser.add_argument('name', help='Tier name')
    tier_parser.add_argument('menu_type', help='Menu type name')
    tier_parser.add_argument('--parent', help='Parent tier name')
    tier_parser.add_argument('--sort-order', type=int, default=100, help='Sort order (default: 100)')

    # Cleanup commands
    cleanup_parser = subparsers.add_parser('cleanup', help='Clean up menu data')
    cleanup_parser.add_argument('--include-types', action='store_true', help='Also remove menu types')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Initialize CLI
    cli = None
    try:
        cli = MenuCLI(
            verbose=args.verbose,
            show_icons=not args.no_icons,
            table_format=args.table_format
        )
    except Exception as e:
        print(f"Error initializing CLI: {e}")
        return 1

    # Execute commands
    try:
        if args.command == 'status':
            return cli.show_menu_status()

        elif args.command == 'list-types':
            return cli.list_menu_types()

        elif args.command == 'show-tree':
            return cli.show_menu_tree(args.type)

        elif args.command == 'find':
            return cli.find_menu_item(args.search)

        elif args.command == 'create':
            if args.create_type == 'type':
                return cli.create_menu_type(args.name, args.description, not args.inactive)
            elif args.create_type == 'tier':
                return cli.create_menu_tier(args.name, args.menu_type, args.parent, args.sort_order)
            else:
                create_parser.print_help()
                return 1

        elif args.command == 'cleanup':
            return cli.cleanup_menu_data(args.include_types)

        else:
            parser.print_help()
            return 1

    except KeyboardInterrupt:
        if cli:
            cli.log_info("Operation cancelled by user")
        print("\nOperation cancelled")
        return 1
    except Exception as e:
        if cli:
            cli.log_error(f"Unexpected error during command execution: {e}")
        print(f"Error: {e}")
        return 1
    finally:
        # Clean up session
        if cli:
            cli.close()

    return 0


if __name__ == '__main__':
    sys.exit(main())