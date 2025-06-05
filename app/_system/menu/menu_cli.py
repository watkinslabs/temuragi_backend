#!/usr/bin/env python3
"""
Menu System CLI Management Tool
"""

import argparse
import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from tabulate import tabulate
import uuid

# Add app path
sys.path.append('/web/temuragi')

try:
    from app.config import config
except ImportError:
    print("Error: Could not import app.config")
    sys.exit(1)


class MenuCLI:
    def __init__(self, db_config=None):
        """Initialize CLI with database connection"""
        if db_config:
            self.engine = create_engine(db_config)
        else:
            self.engine = create_engine(config['DATABASE_URI'])

        session_factory = sessionmaker(bind=self.engine)
        self.session = session_factory()

    def show_menu_status(self):
        """Show comprehensive menu system status"""
        try:
            print("Menu System Status")
            print("=" * 60)
            
            # Menu table counts
            menu_tables = [
                ("menu_types", "Menu type definitions"),
                ("menu_tiers", "Menu tier hierarchy"), 
                ("menu_links", "Individual menu links"),
                ("role_menu_permissions", "Role-based permissions"),
                ("user_quick_links", "User quick access links")
            ]

            print("\nTable Counts:")
            headers = ['Table', 'Description', 'Count']
            rows = []

            total_records = 0
            for table, description in menu_tables:
                try:
                    result = self.session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.scalar()
                    rows.append([table, description, f"{count:,}"])
                    total_records += count
                except Exception as e:
                    rows.append([table, description, f"Error: {e}"])

            print(tabulate(rows, headers=headers, tablefmt='simple'))
            print(f"\nTotal menu records: {total_records:,}")
            
            # Menu types summary
            self._show_menu_types_summary()
            
            # Menu hierarchy summary  
            self._show_menu_hierarchy_summary()
            
            return 0

        except Exception as e:
            print(f"Error: {e}")
            return 1

    def _show_menu_types_summary(self):
        """Show summary of menu types"""
        try:
            print("\nMenu Types Summary:")
            result = self.session.execute(text("""
                SELECT 
                    mt.name,
                    mt.description,
                    mt.is_active,
                    COUNT(DISTINCT tier.uuid) as tier_count,
                    COUNT(DISTINCT link.uuid) as link_count
                FROM menu_types mt
                LEFT JOIN menu_tiers tier ON tier.menu_type_uuid = mt.uuid
                LEFT JOIN menu_links link ON link.tier_uuid = tier.uuid
                GROUP BY mt.uuid, mt.name, mt.description, mt.is_active
                ORDER BY mt.name
            """))
            
            types_data = result.fetchall()
            if types_data:
                headers = ['Type', 'Description', 'Active', 'Tiers', 'Links']
                rows = []
                for name, desc, active, tiers, links in types_data:
                    status = "✓" if active else "✗"
                    rows.append([name, desc[:30] + ('...' if len(desc) > 30 else ''), status, tiers, links])
                
                print(tabulate(rows, headers=headers, tablefmt='simple'))
            else:
                print("  No menu types found")
                
        except Exception as e:
            print(f"  Error loading menu types: {e}")

    def _show_menu_hierarchy_summary(self):
        """Show menu hierarchy summary"""
        try:
            print("\nMenu Hierarchy Summary:")
            result = self.session.execute(text("""
                WITH RECURSIVE menu_tree AS (
                    SELECT 
                        uuid,
                        name,
                        parent_uuid,
                        menu_type_uuid,
                        0 as level
                    FROM menu_tiers
                    WHERE parent_uuid IS NULL
                    
                    UNION ALL
                    
                    SELECT 
                        t.uuid,
                        t.name,
                        t.parent_uuid,
                        t.menu_type_uuid,
                        mt.level + 1
                    FROM menu_tiers t
                    JOIN menu_tree mt ON t.parent_uuid = mt.uuid
                )
                SELECT 
                    level,
                    COUNT(*) as count,
                    MAX(level) OVER() as max_depth
                FROM menu_tree
                GROUP BY level
                ORDER BY level
            """))
            
            hierarchy_data = result.fetchall()
            if hierarchy_data:
                max_depth = hierarchy_data[0][2] if hierarchy_data else 0
                print(f"  Maximum depth: {max_depth} levels")
                
                headers = ['Level', 'Tier Count', 'Description']
                rows = []
                for level, count, _ in hierarchy_data:
                    desc = "Root tiers" if level == 0 else f"Level {level} sub-tiers"
                    rows.append([level, count, desc])
                
                print(tabulate(rows, headers=headers, tablefmt='simple'))
            else:
                print("  No menu hierarchy found")
                
        except Exception as e:
            print(f"  Error loading hierarchy: {e}")

    def list_menu_types(self):
        """List all menu types with details"""
        try:
            print("Menu Types")
            print("=" * 50)
            
            result = self.session.execute(text("""
                SELECT 
                    mt.uuid,
                    mt.name,
                    mt.description,
                    mt.is_active,
                    mt.created_at,
                    COUNT(DISTINCT tier.uuid) as tier_count
                FROM menu_types mt
                LEFT JOIN menu_tiers tier ON tier.menu_type_uuid = mt.uuid
                GROUP BY mt.uuid, mt.name, mt.description, mt.is_active, mt.created_at
                ORDER BY mt.name
            """))
            
            types_data = result.fetchall()
            if not types_data:
                print("No menu types found")
                return 0
            
            for uuid_val, name, desc, active, created, tier_count in types_data:
                status = "ACTIVE" if active else "INACTIVE"
                print(f"\n{name} ({status})")
                print(f"  UUID: {uuid_val}")
                print(f"  Description: {desc}")
                print(f"  Tiers: {tier_count}")
                print(f"  Created: {created}")
            
            return 0
            
        except Exception as e:
            print(f"Error: {e}")
            return 1

    def show_menu_tree(self, menu_type_name=None):
        """Show menu hierarchy as a tree structure"""
        try:
            if menu_type_name:
                print(f"Menu Tree for '{menu_type_name}'")
            else:
                print("Complete Menu Tree (All Types)")
            print("=" * 60)
            
            # Build the tree query
            where_clause = ""
            params = {}
            if menu_type_name:
                where_clause = "AND mt.name = :menu_type"
                params['menu_type'] = menu_type_name
            
            result = self.session.execute(text(f"""
                WITH RECURSIVE menu_tree AS (
                    SELECT 
                        tier.uuid,
                        tier.name,
                        tier.parent_uuid,
                        tier.menu_type_uuid,
                        tier.sort_order,
                        mt.name as menu_type_name,
                        0 as level,
                        tier.name as path
                    FROM menu_tiers tier
                    JOIN menu_types mt ON tier.menu_type_uuid = mt.uuid
                    WHERE tier.parent_uuid IS NULL {where_clause}
                    
                    UNION ALL
                    
                    SELECT 
                        t.uuid,
                        t.name,
                        t.parent_uuid,
                        t.menu_type_uuid,
                        t.sort_order,
                        tree.menu_type_name,
                        tree.level + 1,
                        tree.path || ' > ' || t.name
                    FROM menu_tiers t
                    JOIN menu_tree tree ON t.parent_uuid = tree.uuid
                ),
                tree_with_links AS (
                    SELECT 
                        tree.*,
                        COUNT(link.uuid) as link_count
                    FROM menu_tree tree
                    LEFT JOIN menu_links link ON link.tier_uuid = tree.uuid
                    GROUP BY tree.uuid, tree.name, tree.parent_uuid, tree.menu_type_uuid, 
                             tree.sort_order, tree.menu_type_name, tree.level, tree.path
                )
                SELECT * FROM tree_with_links
                ORDER BY menu_type_name, level, sort_order, name
            """), params)
            
            tree_data = result.fetchall()
            if not tree_data:
                type_msg = f" for menu type '{menu_type_name}'" if menu_type_name else ""
                print(f"No menu hierarchy found{type_msg}")
                return 0
            
            current_type = None
            for row in tree_data:
                uuid_val, name, parent_uuid, menu_type_uuid, sort_order, menu_type_name, level, path, link_count = row
                
                # Show menu type header
                if current_type != menu_type_name:
                    if current_type is not None:
                        print()  # Blank line between types
                    print(f"\n{menu_type_name}:")
                    print("-" * (len(menu_type_name) + 1))
                    current_type = menu_type_name
                
                # Show the tier with indentation
                indent = "  " * level
                link_info = f" ({link_count} links)" if link_count > 0 else ""
                print(f"{indent}├─ {name}{link_info}")
            
            return 0
            
        except Exception as e:
            print(f"Error: {e}")
            return 1

    def create_menu_type(self, name, description, is_active=True):
        """Create a new menu type"""
        try:
            print(f"Creating menu type: {name}")
            
            # Check if it already exists
            result = self.session.execute(text("""
                SELECT uuid FROM menu_types WHERE name = :name
            """), {"name": name})
            
            if result.fetchone():
                print(f"Error: Menu type '{name}' already exists")
                return 1
            
            # Create new menu type
            new_uuid = str(uuid.uuid4())
            self.session.execute(text("""
                INSERT INTO menu_types (uuid, name, description, is_active, created_at, updated_at)
                VALUES (:uuid, :name, :description, :is_active, NOW(), NOW())
            """), {
                "uuid": new_uuid,
                "name": name,
                "description": description,
                "is_active": is_active
            })
            
            self.session.commit()
            print(f"✓ Created menu type '{name}' with UUID: {new_uuid}")
            return 0
            
        except Exception as e:
            print(f"Error: {e}")
            self.session.rollback()
            return 1

    def create_menu_tier(self, name, menu_type_name, parent_tier_name=None, sort_order=100):
        """Create a new menu tier"""
        try:
            print(f"Creating menu tier: {name}")
            
            # Get menu type UUID
            result = self.session.execute(text("""
                SELECT uuid FROM menu_types WHERE name = :name
            """), {"name": menu_type_name})
            
            menu_type_row = result.fetchone()
            if not menu_type_row:
                print(f"Error: Menu type '{menu_type_name}' not found")
                return 1
            
            menu_type_uuid = menu_type_row[0]
            
            # Get parent tier UUID if specified
            parent_uuid = None
            if parent_tier_name:
                result = self.session.execute(text("""
                    SELECT uuid FROM menu_tiers 
                    WHERE name = :name AND menu_type_uuid = :menu_type_uuid
                """), {"name": parent_tier_name, "menu_type_uuid": menu_type_uuid})
                
                parent_row = result.fetchone()
                if not parent_row:
                    print(f"Error: Parent tier '{parent_tier_name}' not found in menu type '{menu_type_name}'")
                    return 1
                
                parent_uuid = parent_row[0]
            
            # Check if tier already exists
            result = self.session.execute(text("""
                SELECT uuid FROM menu_tiers 
                WHERE name = :name AND menu_type_uuid = :menu_type_uuid
            """), {"name": name, "menu_type_uuid": menu_type_uuid})
            
            if result.fetchone():
                print(f"Error: Menu tier '{name}' already exists in menu type '{menu_type_name}'")
                return 1
            
            # Create new tier
            new_uuid = str(uuid.uuid4())
            self.session.execute(text("""
                INSERT INTO menu_tiers (uuid, name, menu_type_uuid, parent_uuid, sort_order, created_at, updated_at)
                VALUES (:uuid, :name, :menu_type_uuid, :parent_uuid, :sort_order, NOW(), NOW())
            """), {
                "uuid": new_uuid,
                "name": name,
                "menu_type_uuid": menu_type_uuid,
                "parent_uuid": parent_uuid,
                "sort_order": sort_order
            })
            
            self.session.commit()
            
            parent_info = f" under '{parent_tier_name}'" if parent_tier_name else " as root tier"
            print(f"✓ Created menu tier '{name}'{parent_info} in '{menu_type_name}'")
            print(f"  UUID: {new_uuid}")
            return 0
            
        except Exception as e:
            print(f"Error: {e}")
            self.session.rollback()
            return 1

    def cleanup_menu_data(self, include_types=False):
        """Clean up menu system data"""
        try:
            print("Starting menu system cleanup...")
            
            if include_types:
                print("Mode: Complete cleanup (including menu types)")
            else:
                print("Mode: Preserve menu types")
            
            print("-" * 50)

            # Step 1: Remove user quick links
            print("1. Removing user quick links...")
            result = self.session.execute(text("DELETE FROM user_quick_links"))
            print(f"   ✓ Deleted {result.rowcount} user quick links")

            # Step 2: Remove role menu permissions  
            print("2. Removing role menu permissions...")
            result = self.session.execute(text("DELETE FROM role_menu_permissions"))
            print(f"   ✓ Deleted {result.rowcount} role menu permissions")

            # Step 3: Clear page references in tiers
            print("3. Clearing menu tier page references...")
            result = self.session.execute(text("UPDATE menu_tiers SET page_uuid = NULL WHERE page_uuid IS NOT NULL"))
            print(f"   ✓ Cleared {result.rowcount} page references")

            # Step 4: Remove menu links
            print("4. Removing menu links...")
            result = self.session.execute(text("DELETE FROM menu_links"))
            print(f"   ✓ Deleted {result.rowcount} menu links")

            # Step 5: Remove menu tiers (hierarchical)
            print("5. Removing menu tiers...")
            self._delete_tiers_hierarchical()

            # Step 6: Optionally remove menu types
            if include_types:
                print("6. Removing menu types...")
                result = self.session.execute(text("DELETE FROM menu_types"))
                print(f"   ✓ Deleted {result.rowcount} menu types")
            else:
                print("6. Menu types preserved")

            self.session.commit()
            cleanup_type = "Complete" if include_types else "Partial"
            print(f"\n✓ {cleanup_type} menu system cleanup completed!")
            return 0

        except Exception as e:
            print(f"Error: {e}")
            self.session.rollback()
            return 1

    def _delete_tiers_hierarchical(self):
        """Delete menu tiers in hierarchical order (children first)"""
        try:
            # Get tiers by depth (deepest first)
            depth_query = text("""
                WITH RECURSIVE tier_hierarchy AS (
                    SELECT uuid, name, parent_uuid, 0 as depth
                    FROM menu_tiers
                    WHERE parent_uuid IS NULL

                    UNION ALL

                    SELECT t.uuid, t.name, t.parent_uuid, th.depth + 1
                    FROM menu_tiers t
                    JOIN tier_hierarchy th ON t.parent_uuid = th.uuid
                )
                SELECT uuid, depth FROM tier_hierarchy ORDER BY depth DESC
            """)

            tiers_by_depth = self.session.execute(depth_query).fetchall()

            for tier_uuid, depth in tiers_by_depth:
                self.session.execute(
                    text("DELETE FROM menu_tiers WHERE uuid = :uuid"),
                    {"uuid": str(tier_uuid)}
                )

            print(f"   ✓ Deleted {len(tiers_by_depth)} tiers hierarchically")

        except Exception as e:
            print(f"   Error in hierarchical deletion: {e}")
            # Fallback
            result = self.session.execute(text("DELETE FROM menu_tiers"))
            print(f"   ✓ Fallback: Deleted {result.rowcount} tiers")

    def export_menu_structure(self, menu_type_name=None, format_type='json'):
        """Export menu structure to file"""
        try:
            print(f"Exporting menu structure to {format_type.upper()}...")
            
            # TODO: Implement export functionality
            print("Export functionality not yet implemented")
            return 1
            
        except Exception as e:
            print(f"Error: {e}")
            return 1

    def import_menu_structure(self, file_path):
        """Import menu structure from file"""
        try:
            print(f"Importing menu structure from {file_path}...")
            
            # TODO: Implement import functionality
            print("Import functionality not yet implemented")
            return 1
            
        except Exception as e:
            print(f"Error: {e}")
            return 1


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(description='Menu System CLI')
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Status and listing
    subparsers.add_parser('status', help='Show comprehensive menu system status')
    subparsers.add_parser('list-types', help='List all menu types with details')
    
    tree_parser = subparsers.add_parser('show-tree', help='Show menu hierarchy tree')
    tree_parser.add_argument('--type', help='Show tree for specific menu type only')

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

    # Import/Export (future)
    # export_parser = subparsers.add_parser('export', help='Export menu structure')
    # export_parser.add_argument('--type', help='Export specific menu type only')
    # export_parser.add_argument('--format', choices=['json', 'yaml'], default='json', help='Output format')
    # 
    # import_parser = subparsers.add_parser('import', help='Import menu structure')
    # import_parser.add_argument('file', help='File to import from')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Initialize CLI
    try:
        cli = MenuCLI()
    except Exception as e:
        print(f"Error initializing: {e}")
        return 1

    # Execute commands
    try:
        if args.command == 'status':
            return cli.show_menu_status()
        
        elif args.command == 'list-types':
            return cli.list_menu_types()
        
        elif args.command == 'show-tree':
            return cli.show_menu_tree(args.type)
        
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
        
        # elif args.command == 'export':
        #     return cli.export_menu_structure(args.type, args.format)
        # 
        # elif args.command == 'import':
        #     return cli.import_menu_structure(args.file)
        
        else:
            parser.print_help()
            return 1

    except KeyboardInterrupt:
        print("\nCancelled")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())