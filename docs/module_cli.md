#!/usr/bin/env python3
"""
Menu System CLI Management Tool
Manage menu system data and resolve foreign key constraints
"""

import argparse
import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from tabulate import tabulate

# Add your app path to import the models and config
sys.path.append('/web/temuragi')
from app.config import config


class MenuCLI:
    def __init__(self, db_config=None):
        """Initialize CLI with database connection"""
        if db_config:
            self.engine = create_engine(db_config)
        else:
            # Use config.py database URI
            self.engine = create_engine(config['DATABASE_URI'])
        
        session_factory = sessionmaker(bind=self.engine)
        self.session = session_factory()
    
    def show_table_counts(self):
        """Show current record counts in menu tables"""
        tables = [
            "menu_types",
            "menu_tiers", 
            "menu_links",
            "role_menu_permissions",
            "user_quick_links"
        ]
        
        print("Current menu table counts:")
        headers = ['Table', 'Count']
        rows = []
        
        for table in tables:
            try:
                result = self.session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                rows.append([table, count])
            except Exception as e:
                rows.append([table, f"Error: {e}"])
        
        print(tabulate(rows, headers=headers, tablefmt='grid'))
        return 0
    
    def list_blueprints(self):
        """List all blueprints that have menu items"""
        try:
            query = text("""
                SELECT DISTINCT blueprint_name, COUNT(*) as link_count
                FROM menu_links 
                WHERE blueprint_name IS NOT NULL
                GROUP BY blueprint_name
                ORDER BY blueprint_name
            """)
            
            results = self.session.execute(query).fetchall()
            
            if not results:
                print("No blueprints found with menu items")
                return 0
            
            headers = ['Blueprint', 'Menu Links']
            rows = [[bp, count] for bp, count in results]
            
            print(tabulate(rows, headers=headers, tablefmt='grid'))
            return 0
            
        except Exception as e:
            print(f"✗ Error listing blueprints: {e}")
            return 1
    
    def list_menu_types(self):
        """List all menu types and their tier counts"""
        try:
            query = text("""
                SELECT mt.name, mt.display, mt.description, COUNT(tier.uuid) as tier_count
                FROM menu_types mt
                LEFT JOIN menu_tiers tier ON mt.uuid = tier.menu_type_uuid
                GROUP BY mt.uuid, mt.name, mt.display, mt.description
                ORDER BY mt.name
            """)
            
            results = self.session.execute(query).fetchall()
            
            if not results:
                print("No menu types found")
                return 0
            
            headers = ['Name', 'Display', 'Description', 'Tiers']
            rows = []
            
            for name, display, desc, tier_count in results:
                rows.append([name, display, desc or '', tier_count])
            
            print(tabulate(rows, headers=headers, tablefmt='grid'))
            return 0
            
        except Exception as e:
            print(f"✗ Error listing menu types: {e}")
            return 1
    
    def cleanup_full_system(self):
        """Clean up entire menu system respecting foreign key constraints"""
        try:
            print("Starting full menu system cleanup...")
            
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
            print("6. Menu types left intact (use --include-types to remove)")
            
            self.session.commit()
            print("\n✓ Full menu system cleanup completed successfully!")
            return 0
            
        except Exception as e:
            print(f"✗ Error during cleanup: {e}")
            self.session.rollback()
            return 1
    
    def cleanup_include_types(self):
        """Clean up entire menu system including menu types"""
        try:
            result = self.cleanup_full_system()
            if result != 0:
                return result
            
            print("6. Removing menu types...")
            result = self.session.execute(text("DELETE FROM menu_types"))
            print(f"   ✓ Deleted {result.rowcount} menu types")
            
            self.session.commit()
            print("✓ Complete cleanup with menu types finished!")
            return 0
            
        except Exception as e:
            print(f"✗ Error during complete cleanup: {e}")
            self.session.rollback()
            return 1
    
    def cleanup_blueprint(self, blueprint_name):
        """Clean up menu items for a specific blueprint"""
        try:
            print(f"Cleaning up menu items for blueprint: {blueprint_name}")
            
            # Get menu links for this blueprint
            links_query = text("SELECT uuid FROM menu_links WHERE blueprint_name = :blueprint_name")
            link_results = self.session.execute(links_query, {"blueprint_name": blueprint_name})
            link_uuids = [str(row[0]) for row in link_results]
            
            if not link_uuids:
                print(f"No menu links found for blueprint '{blueprint_name}'")
                return 0
            
            print(f"Found {len(link_uuids)} links to clean up")
            
            # Remove dependencies for each link
            total_quick_links = 0
            total_permissions = 0
            total_page_refs = 0
            
            for uuid in link_uuids:
                # Remove quick links
                result = self.session.execute(
                    text("DELETE FROM user_quick_links WHERE menu_link_uuid = :uuid"),
                    {"uuid": uuid}
                )
                total_quick_links += result.rowcount
                
                # Remove permissions
                result = self.session.execute(
                    text("DELETE FROM role_menu_permissions WHERE menu_link_uuid = :uuid"),
                    {"uuid": uuid}
                )
                total_permissions += result.rowcount
                
                # Clear page references
                result = self.session.execute(
                    text("UPDATE menu_tiers SET page_uuid = NULL WHERE page_uuid = :uuid"),
                    {"uuid": uuid}
                )
                total_page_refs += result.rowcount
            
            print(f"   ✓ Removed {total_quick_links} quick links")
            print(f"   ✓ Removed {total_permissions} permissions")
            print(f"   ✓ Cleared {total_page_refs} page references")
            
            # Remove the links
            result = self.session.execute(
                text("DELETE FROM menu_links WHERE blueprint_name = :blueprint_name"),
                {"blueprint_name": blueprint_name}
            )
            print(f"   ✓ Deleted {result.rowcount} menu links")
            
            # Remove empty tier for this blueprint
            tier_result = self.session.execute(
                text("""
                    DELETE FROM menu_tiers 
                    WHERE name = :tier_name 
                    AND uuid NOT IN (SELECT DISTINCT tier_uuid FROM menu_links WHERE tier_uuid IS NOT NULL)
                """),
                {"tier_name": blueprint_name.upper()}
            )
            if tier_result.rowcount > 0:
                print(f"   ✓ Removed empty tier: {blueprint_name.upper()}")
            
            self.session.commit()
            print(f"✓ Cleanup completed for blueprint: {blueprint_name}")
            return 0
            
        except Exception as e:
            print(f"✗ Error during blueprint cleanup: {e}")
            self.session.rollback()
            return 1
    
    def cleanup_menu_type(self, menu_type_name):
        """Clean up all data for a specific menu type"""
        try:
            print(f"Cleaning up menu type: {menu_type_name}")
            
            # Get menu type UUID
            type_query = text("SELECT uuid FROM menu_types WHERE name = :name")
            type_result = self.session.execute(type_query, {"name": menu_type_name}).first()
            
            if not type_result:
                print(f"Menu type '{menu_type_name}' not found")
                return 1
            
            type_uuid = str(type_result[0])
            
            # Get all tiers for this menu type
            tiers_query = text("SELECT uuid FROM menu_tiers WHERE menu_type_uuid = :type_uuid")
            tier_results = self.session.execute(tiers_query, {"type_uuid": type_uuid})
            tier_uuids = [str(row[0]) for row in tier_results]
            
            if tier_uuids:
                print(f"Found {len(tier_uuids)} tiers to clean up")
                
                # Get all links in these tiers
                tier_placeholders = ','.join([f"'{uuid}'" for uuid in tier_uuids])
                links_query = text(f"SELECT uuid FROM menu_links WHERE tier_uuid IN ({tier_placeholders})")
                link_results = self.session.execute(links_query)
                link_uuids = [str(row[0]) for row in link_results]
                
                if link_uuids:
                    print(f"Found {len(link_uuids)} links to clean up")
                    
                    # Clean up link dependencies
                    for uuid in link_uuids:
                        self.session.execute(
                            text("DELETE FROM user_quick_links WHERE menu_link_uuid = :uuid"),
                            {"uuid": uuid}
                        )
                        self.session.execute(
                            text("DELETE FROM role_menu_permissions WHERE menu_link_uuid = :uuid"),
                            {"uuid": uuid}
                        )
                    
                    # Clear page references
                    self.session.execute(
                        text("UPDATE menu_tiers SET page_uuid = NULL WHERE menu_type_uuid = :type_uuid"),
                        {"type_uuid": type_uuid}
                    )
                    
                    # Remove links
                    link_placeholders = ','.join([f"'{uuid}'" for uuid in link_uuids])
                    self.session.execute(text(f"DELETE FROM menu_links WHERE uuid IN ({link_placeholders})"))
                    print(f"   ✓ Cleaned up {len(link_uuids)} links")
                
                # Remove tiers (hierarchical)
                self._delete_tiers_for_type(type_uuid)
                print(f"   ✓ Cleaned up {len(tier_uuids)} tiers")
            
            # Remove the menu type
            self.session.execute(
                text("DELETE FROM menu_types WHERE uuid = :uuid"),
                {"uuid": type_uuid}
            )
            print(f"   ✓ Removed menu type: {menu_type_name}")
            
            self.session.commit()
            print(f"✓ Cleanup completed for menu type: {menu_type_name}")
            return 0
            
        except Exception as e:
            print(f"✗ Error during menu type cleanup: {e}")
            self.session.rollback()
            return 1
    
    def reset_sequences(self):
        """Reset auto-increment sequences (PostgreSQL)"""
        print("Resetting sequences...")
        
        # First, discover what sequences actually exist
        try:
            query = text("""
                SELECT sequence_name 
                FROM information_schema.sequences 
                WHERE sequence_schema = current_schema()
                AND sequence_name LIKE '%menu%' 
                OR sequence_name LIKE '%quick_links%'
                OR sequence_name LIKE '%permissions%'
                ORDER BY sequence_name
            """)
            
            existing_sequences = self.session.execute(query).fetchall()
            
            if not existing_sequences:
                print("   No menu-related sequences found")
                return 0
            
            print(f"   Found {len(existing_sequences)} sequences:")
            for seq in existing_sequences:
                print(f"     - {seq[0]}")
            
            reset_count = 0
            for seq_row in existing_sequences:
                seq_name = seq_row[0]
                try:
                    # Use separate transaction for each sequence
                    self.session.execute(text(f"ALTER SEQUENCE {seq_name} RESTART WITH 1"))
                    self.session.commit()
                    reset_count += 1
                    print(f"   ✓ Reset {seq_name}")
                except Exception as e:
                    self.session.rollback()
                    print(f"   ✗ Could not reset {seq_name}: {e}")
            
            print(f"✓ Reset {reset_count} sequences")
            return 0
            
        except Exception as e:
            print(f"✗ Error discovering sequences: {e}")
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
            print(f"   Error in hierarchical tier deletion: {e}")
            # Fallback to simple delete
            result = self.session.execute(text("DELETE FROM menu_tiers"))
            print(f"   ✓ Fallback: Deleted {result.rowcount} tiers")
    
    def _delete_tiers_for_type(self, type_uuid):
        """Delete tiers for a specific menu type hierarchically"""
        try:
            depth_query = text("""
                WITH RECURSIVE tier_hierarchy AS (
                    SELECT uuid, name, parent_uuid, 0 as depth
                    FROM menu_tiers 
                    WHERE parent_uuid IS NULL AND menu_type_uuid = :type_uuid
                    
                    UNION ALL
                    
                    SELECT t.uuid, t.name, t.parent_uuid, th.depth + 1
                    FROM menu_tiers t
                    JOIN tier_hierarchy th ON t.parent_uuid = th.uuid
                    WHERE t.menu_type_uuid = :type_uuid
                )
                SELECT uuid, depth FROM tier_hierarchy ORDER BY depth DESC
            """)
            
            tiers_by_depth = self.session.execute(depth_query, {"type_uuid": type_uuid}).fetchall()
            
            for tier_uuid, depth in tiers_by_depth:
                self.session.execute(
                    text("DELETE FROM menu_tiers WHERE uuid = :uuid"),
                    {"uuid": str(tier_uuid)}
                )
            
        except Exception as e:
            # Fallback
            self.session.execute(
                text("DELETE FROM menu_tiers WHERE menu_type_uuid = :type_uuid"),
                {"type_uuid": type_uuid}
            )


def main():
    """Entry point for master CLI loader"""
    parser = argparse.ArgumentParser(description='Menu System CLI Management Tool')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show current menu system status')
    
    # List commands
    list_parser = subparsers.add_parser('list', help='List menu system components')
    list_subparsers = list_parser.add_subparsers(dest='list_type', help='What to list')
    list_subparsers.add_parser('blueprints', help='List blueprints with menu items')
    list_subparsers.add_parser('types', help='List menu types')
    
    # Cleanup commands
    cleanup_parser = subparsers.add_parser('cleanup', help='Clean up menu system data')
    cleanup_subparsers = cleanup_parser.add_subparsers(dest='cleanup_type', help='Cleanup type')
    
    # Full cleanup
    full_parser = cleanup_subparsers.add_parser('full', help='Clean up entire menu system')
    full_parser.add_argument('--include-types', action='store_true', help='Also remove menu types')
    
    # Blueprint cleanup
    bp_parser = cleanup_subparsers.add_parser('blueprint', help='Clean up specific blueprint')
    bp_parser.add_argument('name', help='Blueprint name to clean up')
    
    # Menu type cleanup
    type_parser = cleanup_subparsers.add_parser('type', help='Clean up specific menu type')
    type_parser.add_argument('name', help='Menu type name to clean up')
    
    # Create tables command
    create_parser = subparsers.add_parser('create-tables', help='Create menu tables if they don\'t exist')
    
    # Reset sequences
    reset_parser = subparsers.add_parser('reset', help='Reset database sequences')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Initialize CLI
    try:
        cli = MenuCLI()
    except Exception as e:
        print(f"✗ Error: {e}")
        return 1
    
    # Execute command
    try:
        if args.command == 'status':
            return cli.show_table_counts()
        
        elif args.command == 'list':
            if args.list_type == 'blueprints':
                return cli.list_blueprints()
            elif args.list_type == 'types':
                return cli.list_menu_types()
            else:
                list_parser.print_help()
                return 1
        
        elif args.command == 'cleanup':
            if args.cleanup_type == 'full':
                if args.include_types:
                    return cli.cleanup_include_types()
                else:
                    return cli.cleanup_full_system()
            elif args.cleanup_type == 'blueprint':
                return cli.cleanup_blueprint(args.name)
            elif args.cleanup_type == 'type':
                return cli.cleanup_menu_type(args.name)
            else:
                cleanup_parser.print_help()
                return 1
        
        elif args.command == 'reset':
            return cli.reset_sequences()
        
        elif args.command == 'create-tables':
            if cli.ensure_tables_exist():
                print("✓ Menu tables created/verified successfully")
                return 0
            else:
                print("✗ Failed to create menu tables")
                return 1
    
    except KeyboardInterrupt:
        print("\n✗ Operation cancelled")
        return 1
    except Exception as e:
        print(f"✗ Error: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())