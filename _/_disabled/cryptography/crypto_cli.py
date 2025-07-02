#!/usr/bin/env python3
"""
Crypto CLI - Manage database credential encryption
Provides encryption key management and credential encryption operations
"""

import sys
import os
import json
import argparse
import getpass
from tabulate import tabulate
from datetime import datetime
import base64
from cryptography.fernet import Fernet

from app.base.cli_v1 import BaseCLI
from app.config import config

CLI_DESCRIPTION = "Manage database credential encryption"


class CryptoCLI(BaseCLI):
    def __init__(self, verbose=False, show_icons=True, table_format=None):
        """Initialize CLI with encryption utilities"""
        super().__init__(
            name="crypto",
            log_file="logs/crypto_cli.log",
            connect_db=True,
            verbose=verbose,
            show_icons=show_icons,
            table_format=table_format
        )

        self.log_info("Starting crypto CLI initialization")

        # Get models
        self.connection_model = self.get_model('Connection')
        if not self.connection_model:
            self.log_critical("Failed to load Connection model")
            raise RuntimeError("Required models not found")

        # Setup encryption
        try:
            from app.classes import CredentialCipher
            self.cipher = None
            self.cipher_class = CredentialCipher
            self.log_info("Encryption utilities loaded")
        except Exception as e:
            self.log_error(f"Failed to load encryption utilities: {e}")
            raise

    def icon(self, icon_type):
        """Get icon for display"""
        if not self.show_icons:
            return ''

        icons = {
            'check': '✓',
            'cross': '✗',
            'warning': '⚠',
            'key': '🔑',
            'lock': '🔒',
            'unlock': '🔓',
            'shield': '🛡️'
        }
        return icons.get(icon_type, '')

    # =====================================================================
    # KEY MANAGEMENT OPERATIONS
    # =====================================================================

    def check_key(self):
        """Check if encryption key is configured"""
        self.log_info("Checking encryption key configuration")

        try:
            cipher_key = config.get('DB_CIPHER_KEY')
            
            if not cipher_key:
                self.output_error("DB_CIPHER_KEY not found in configuration")
                self.output_info("Run 'crypto generate-key' to create a new encryption key")
                return 1

            self.output_success(f"{self.icon('key')} Encryption key is configured")

            # Try to initialize cipher to validate key
            try:
                from app.classes import CredentialCipher
                cipher = CredentialCipher()
                self.output_success(f"{self.icon('lock')} Cipher initialized successfully")
                
                # Show key info
                key_info = [
                    ['Key Present', f"{self.icon('check')} Yes"],
                    ['Key Length', f"{len(cipher_key)} characters"],
                    ['Cipher Type', 'Fernet (AES-128)'],
                    ['Status', f"{self.icon('shield')} Active"]
                ]
                
                self.output_info("\nEncryption Configuration:")
                self.output_table(key_info, headers=['Property', 'Value'])
                
                return 0
                
            except Exception as e:
                self.output_error(f"Failed to initialize cipher: {e}")
                self.output_warning("Key may be invalid or corrupted")
                return 1

        except Exception as e:
            self.log_error(f"Error checking key: {e}")
            self.output_error(f"Error checking key: {e}")
            return 1

    def generate_key(self, output_file=None, force=False):
        """Generate a new encryption key"""
        self.log_info("Generating new encryption key")

        try:
            # Check if key already exists
            existing_key = config.get('DB_CIPHER_KEY')
            if existing_key and not force:
                self.output_warning("DB_CIPHER_KEY already exists in configuration")
                response = input("Generate new key anyway? This will invalidate existing encrypted data! (y/N): ")
                if response.lower() != 'y':
                    self.output_info("Key generation cancelled")
                    return 0

            # Generate new key
            new_key = Fernet.generate_key()
            key_str = new_key.decode('utf-8')

            self.output_success(f"{self.icon('key')} Generated new encryption key")
            
            # Display key info
            self.output_info("\n" + "=" * 60)
            self.output_info("NEW ENCRYPTION KEY:")
            self.output_info(key_str)
            self.output_info("=" * 60)

            # Configuration instructions
            self.output_info("\nAdd this to your configuration:")
            self.output_info(f"DB_CIPHER_KEY = '{key_str}'")

            # Save to file if requested
            if output_file:
                with open(output_file, 'w') as f:
                    f.write(key_str)
                
                # Set restrictive permissions on Fedora/Linux
                os.chmod(output_file, 0o600)
                
                self.output_success(f"\n{self.icon('check')} Key saved to: {output_file}")
                self.output_info("File permissions set to 600 (owner read/write only)")
                
                # Show how to load from file
                self.output_info("\nTo use from file in your config:")
                self.output_info(f"with open('{output_file}', 'r') as f:")
                self.output_info("    DB_CIPHER_KEY = f.read().strip()")

            # Security warning
            self.output_warning(f"\n{self.icon('warning')} IMPORTANT SECURITY NOTES:")
            self.output_warning("1. Keep this key secure and backed up")
            self.output_warning("2. Never commit the key to version control")
            self.output_warning("3. Losing this key means losing access to all encrypted data")
            self.output_warning("4. All team members need the same key")

            return 0

        except Exception as e:
            self.log_error(f"Error generating key: {e}")
            self.output_error(f"Error generating key: {e}")
            return 1

    def rotate_key(self, new_key_file=None):
        """Rotate encryption key and re-encrypt all credentials"""
        self.log_info("Starting key rotation")

        try:
            # Check current key
            old_key = config.get('DB_CIPHER_KEY')
            if not old_key:
                self.output_error("No existing DB_CIPHER_KEY found")
                return 1

            # Get or generate new key
            if new_key_file:
                try:
                    with open(new_key_file, 'r') as f:
                        new_key = f.read().strip()
                except FileNotFoundError:
                    self.output_error(f"Key file not found: {new_key_file}")
                    return 1
            else:
                new_key = Fernet.generate_key().decode('utf-8')
                self.output_info(f"Generated new key: {new_key}")

            # Initialize ciphers
            from app.classes import CredentialCipher
            
            # Old cipher with current key
            old_cipher = CredentialCipher()
            
            # New cipher with new key - we'll need to monkey-patch for testing
            # In production, you'd update the config and restart
            self.output_warning("Key rotation in CLI is for testing only")
            self.output_warning("In production, update config and restart services")

            # Count connections with credentials
            connections = self.session.query(self.connection_model).filter(
                self.connection_model._credentials.isnot(None)
            ).all()

            if not connections:
                self.output_warning("No connections with credentials found")
                return 0

            self.output_info(f"Found {len(connections)} connections to re-encrypt")

            # Confirm rotation
            self.output_warning(f"\n{self.icon('warning')} This will re-encrypt all credentials!")
            response = input("Continue with key rotation? (y/N): ")
            if response.lower() != 'y':
                self.output_info("Key rotation cancelled")
                return 0

            # Perform rotation
            success_count = 0
            failed_count = 0

            for conn in connections:
                try:
                    # Decrypt with old key
                    decrypted = old_cipher.decrypt_dict(conn._credentials)
                    
                    # For testing, we'll just show what would happen
                    self.output_info(f"  {conn.name}: Would re-encrypt credentials")
                    success_count += 1
                    
                except Exception as e:
                    self.output_error(f"  {conn.name}: Failed - {e}")
                    failed_count += 1

            # Summary
            self.output_info(f"\nRotation simulation complete:")
            self.output_info(f"  Success: {success_count}")
            self.output_info(f"  Failed: {failed_count}")

            self.output_info(f"\nTo complete rotation:")
            self.output_info(f"1. Update config: DB_CIPHER_KEY = '{new_key}'")
            self.output_info(f"2. Run migration script to re-encrypt all data")
            self.output_info(f"3. Restart all services")

            return 0

        except Exception as e:
            self.log_error(f"Error rotating key: {e}")
            self.output_error(f"Error rotating key: {e}")
            return 1

    # =====================================================================
    # ENCRYPTION OPERATIONS
    # =====================================================================

    def test_encryption(self):
        """Test encryption functionality"""
        self.log_info("Testing encryption functionality")

        try:
            from app.classes import CredentialCipher

            # Initialize cipher
            try:
                cipher = CredentialCipher()
                self.output_success(f"{self.icon('check')} Cipher initialized")
            except Exception as e:
                self.output_error(f"Failed to initialize cipher: {e}")
                return 1

            # Test 1: Basic encryption/decryption
            self.output_info("\n1. Testing basic encryption/decryption:")
            test_password = "test_password_123!@#"
            
            encrypted = cipher.encrypt_value(test_password)
            self.output_info(f"   Original:  {test_password}")
            self.output_info(f"   Encrypted: {encrypted[:30]}...")
            
            decrypted = cipher.decrypt_value(encrypted)
            self.output_info(f"   Decrypted: {decrypted}")
            
            if decrypted == test_password:
                self.output_success(f"   {self.icon('check')} Basic encryption test passed")
            else:
                self.output_error(f"   {self.icon('cross')} Basic encryption test failed")
                return 1

            # Test 2: Dictionary encryption
            self.output_info("\n2. Testing credential dictionary encryption:")
            test_creds = {
                'user': 'db_user',
                'password': 'super_secret_pass',
                'host': 'localhost',
                'api_key': 'sk-1234567890'
            }

            encrypted_creds = cipher.encrypt_dict(test_creds)
            
            # Check what got encrypted
            encrypted_fields = []
            for field in cipher.ENCRYPTED_FIELDS:
                if field in test_creds and encrypted_creds.get(field) != test_creds.get(field):
                    encrypted_fields.append(field)

            self.output_info(f"   Encrypted fields: {', '.join(encrypted_fields)}")
            
            decrypted_creds = cipher.decrypt_dict(encrypted_creds)
            
            if decrypted_creds == test_creds:
                self.output_success(f"   {self.icon('check')} Dictionary encryption test passed")
            else:
                self.output_error(f"   {self.icon('cross')} Dictionary encryption test failed")
                return 1

            # Test 3: Empty value handling
            self.output_info("\n3. Testing empty value handling:")
            
            none_result = cipher.encrypt_value(None)
            empty_result = cipher.encrypt_value("")
            
            if none_result is None and empty_result == "":
                self.output_success(f"   {self.icon('check')} Empty value test passed")
            else:
                self.output_error(f"   {self.icon('cross')} Empty value test failed")
                return 1

            # Test 4: Error handling
            self.output_info("\n4. Testing error handling:")
            
            try:
                cipher.decrypt_value("invalid_encrypted_data")
                self.output_error(f"   {self.icon('cross')} Should have raised an error")
                return 1
            except ValueError:
                self.output_success(f"   {self.icon('check')} Error handling test passed")

            # Overall summary
            self.output_success(f"\n{self.icon('shield')} All encryption tests passed!")
            
            # Show encryption info
            info = [
                ['Encryption Algorithm', 'Fernet (AES-128)'],
                ['Key Derivation', 'PBKDF2-SHA256 (if needed)'],
                ['Encrypted Fields', ', '.join(sorted(cipher.ENCRYPTED_FIELDS))],
                ['Encoding', 'Base64 URL-safe']
            ]
            
            self.output_info("\nEncryption Details:")
            self.output_table(info, headers=['Property', 'Value'])

            return 0

        except Exception as e:
            self.log_error(f"Error testing encryption: {e}")
            self.output_error(f"Error testing encryption: {e}")
            return 1

    def encrypt_value(self, value=None, field_type='password'):
        """Encrypt a single value"""
        self.log_info(f"Encrypting {field_type}")

        try:
            from app.classes import CredentialCipher
            cipher = CredentialCipher()

            # Get value interactively if not provided
            if value is None:
                if field_type == 'password':
                    value = getpass.getpass(f"Enter {field_type} to encrypt: ")
                else:
                    value = input(f"Enter {field_type} to encrypt: ")

            if not value:
                self.output_warning("No value provided")
                return 1

            # Encrypt
            encrypted = cipher.encrypt_value(value)

            self.output_success(f"{self.icon('lock')} Value encrypted successfully")
            self.output_info("\nEncrypted value:")
            self.output_info(encrypted)

            # Offer to verify
            verify = input("\nVerify by decrypting? (Y/n): ")
            if verify.lower() != 'n':
                decrypted = cipher.decrypt_value(encrypted)
                if field_type == 'password':
                    self.output_success(f"{self.icon('unlock')} Decryption successful (password hidden)")
                else:
                    self.output_success(f"{self.icon('unlock')} Decrypted: {decrypted}")

            return 0

        except Exception as e:
            self.log_error(f"Error encrypting value: {e}")
            self.output_error(f"Error encrypting value: {e}")
            return 1

    def decrypt_value(self, encrypted_value):
        """Decrypt a single value"""
        self.log_info("Decrypting value")

        try:
            from app.classes import CredentialCipher
            cipher = CredentialCipher()

            decrypted = cipher.decrypt_value(encrypted_value)

            self.output_success(f"{self.icon('unlock')} Decryption successful")
            self.output_info(f"Decrypted value: {decrypted}")

            return 0

        except ValueError as e:
            self.output_error(f"{self.icon('cross')} Decryption failed: {e}")
            self.output_warning("Possible causes:")
            self.output_warning("  - Wrong encryption key")
            self.output_warning("  - Corrupted encrypted data")
            self.output_warning("  - Data was not encrypted")
            return 1
        except Exception as e:
            self.log_error(f"Error decrypting value: {e}")
            self.output_error(f"Error decrypting value: {e}")
            return 1

    # =====================================================================
    # CONNECTION OPERATIONS
    # =====================================================================

    def check_connections(self, show_details=False):
        """Check encryption status of all connections"""
        self.log_info("Checking connection encryption status")

        try:
            from app.classes import CredentialCipher
            
            # Initialize cipher
            try:
                cipher = CredentialCipher()
            except Exception as e:
                self.output_error(f"Cannot check connections - cipher initialization failed: {e}")
                return 1

            # Get all connections
            connections = self.session.query(self.connection_model).order_by(
                self.connection_model.name
            ).all()

            if not connections:
                self.output_warning("No connections found")
                return 0

            # Analyze connections
            encrypted_count = 0
            unencrypted_count = 0
            no_creds_count = 0
            connection_status = []

            for conn in connections:
                if not conn._credentials:
                    status = 'No credentials'
                    icon = self.icon('warning')
                    no_creds_count += 1
                else:
                    # Check if credentials are encrypted
                    is_encrypted = False
                    for field in cipher.ENCRYPTED_FIELDS:
                        if field in conn._credentials and conn._credentials[field]:
                            if cipher.is_encrypted(str(conn._credentials[field])):
                                is_encrypted = True
                                break
                    
                    if is_encrypted:
                        status = 'Encrypted'
                        icon = self.icon('lock')
                        encrypted_count += 1
                    else:
                        status = 'NOT ENCRYPTED'
                        icon = self.icon('unlock')
                        unencrypted_count += 1

                connection_status.append({
                    'conn': conn,
                    'status': status,
                    'icon': icon,
                    'is_encrypted': status == 'Encrypted'
                })

            # Display summary
            self.output_info("Connection Encryption Status:")
            self.output_info("=" * 60)

            summary = [
                ['Total Connections', len(connections)],
                ['Encrypted', f"{self.icon('lock')} {encrypted_count}"],
                ['Not Encrypted', f"{self.icon('unlock')} {unencrypted_count}"],
                ['No Credentials', f"{self.icon('warning')} {no_creds_count}"]
            ]
            self.output_table(summary, headers=['Metric', 'Count'])

            # Show details if requested
            if show_details or unencrypted_count > 0:
                self.output_info("\nConnection Details:")
                
                headers = ['Name', 'Type', 'Status', 'User']
                rows = []
                
                for item in connection_status:
                    conn = item['conn']
                    user = conn._credentials.get('user', 'N/A') if conn._credentials else 'N/A'
                    
                    rows.append([
                        conn.name,
                        conn.database_type.name,
                        f"{item['icon']} {item['status']}",
                        user
                    ])

                self.output_table(rows, headers=headers)

            # Warnings
            if unencrypted_count > 0:
                self.output_warning(f"\n{self.icon('warning')} {unencrypted_count} connections have unencrypted credentials!")
                self.output_info("Run 'crypto migrate' to encrypt them")

            return 0

        except Exception as e:
            self.log_error(f"Error checking connections: {e}")
            self.output_error(f"Error checking connections: {e}")
            return 1

    def migrate_connections(self, dry_run=False):
        """Migrate unencrypted connections to encrypted"""
        self.log_info(f"Migrating connections - dry_run: {dry_run}")

        try:
            from app.classes import CredentialCipher
            cipher = CredentialCipher()

            # Find connections needing migration
            connections = self.session.query(self.connection_model).filter(
                self.connection_model._credentials.isnot(None)
            ).all()

            to_migrate = []
            
            for conn in connections:
                needs_migration = False
                creds = conn._credentials
                
                # Check each encryptable field
                for field in cipher.ENCRYPTED_FIELDS:
                    if field in creds and creds[field]:
                        if not cipher.is_encrypted(str(creds[field])):
                            needs_migration = True
                            break
                
                if needs_migration:
                    to_migrate.append(conn)

            if not to_migrate:
                self.output_success(f"{self.icon('check')} All connections already encrypted")
                return 0

            # Show what will be migrated
            self.output_info(f"Found {len(to_migrate)} connections to encrypt:")
            
            for conn in to_migrate:
                fields_to_encrypt = []
                for field in cipher.ENCRYPTED_FIELDS:
                    if field in conn._credentials and conn._credentials[field]:
                        if not cipher.is_encrypted(str(conn._credentials[field])):
                            fields_to_encrypt.append(field)
                
                self.output_info(f"  {conn.name}: {', '.join(fields_to_encrypt)}")

            if dry_run:
                self.output_info(f"\n{self.icon('info')} Dry run - no changes made")
                return 0

            # Confirm migration
            response = input(f"\nEncrypt credentials for {len(to_migrate)} connections? (y/N): ")
            if response.lower() != 'y':
                self.output_info("Migration cancelled")
                return 0

            # Perform migration
            success_count = 0
            for conn in to_migrate:
                try:
                    # Get current credentials
                    current_creds = conn._credentials.copy()
                    
                    # Set through property to trigger encryption
                    conn.credentials = current_creds
                    
                    self.output_success(f"  {self.icon('lock')} {conn.name}: Encrypted")
                    success_count += 1
                    
                except Exception as e:
                    self.output_error(f"  {self.icon('cross')} {conn.name}: Failed - {e}")

            # Commit changes
            if success_count > 0:
                self.session.commit()
                self.output_success(f"\n{self.icon('check')} Migration complete: {success_count} connections encrypted")
            else:
                self.session.rollback()
                self.output_error("No connections were migrated successfully")
                return 1

            return 0

        except Exception as e:
            self.session.rollback()
            self.log_error(f"Error migrating connections: {e}")
            self.output_error(f"Error migrating connections: {e}")
            return 1

    # =====================================================================
    # UTILITY OPERATIONS
    # =====================================================================

    def stats(self):
        """Show encryption statistics"""
        self.log_info("Generating encryption statistics")

        try:
            # Check if cipher is available
            from app.classes import CredentialCipher
            
            try:
                cipher = CredentialCipher()
                cipher_available = True
                cipher_error = None
            except Exception as e:
                cipher_available = False
                cipher_error = str(e)

            self.output_info("Encryption System Statistics")
            self.output_info("=" * 60)

            # System status
            system_status = [
                ['Encryption Key', f"{self.icon('check') if config.get('DB_CIPHER_KEY') else self.icon('cross')} {'Configured' if config.get('DB_CIPHER_KEY') else 'Not configured'}"],
                ['Cipher Status', f"{self.icon('check') if cipher_available else self.icon('cross')} {'Active' if cipher_available else f'Failed: {cipher_error}'}"],
                ['Algorithm', 'Fernet (AES-128)' if cipher_available else 'N/A']
            ]
            
            self.output_info("\nSystem Status:")
            self.output_table(system_status, headers=['Component', 'Status'])

            if cipher_available:
                # Connection statistics
                total_connections = self.session.query(self.connection_model).count()
                with_creds = self.session.query(self.connection_model).filter(
                    self.connection_model._credentials.isnot(None)
                ).count()
                
                # Check encryption status
                connections = self.session.query(self.connection_model).filter(
                    self.connection_model._credentials.isnot(None)
                ).all()
                
                encrypted_count = 0
                for conn in connections:
                    for field in cipher.ENCRYPTED_FIELDS:
                        if field in conn._credentials and conn._credentials[field]:
                            if cipher.is_encrypted(str(conn._credentials[field])):
                                encrypted_count += 1
                                break

                conn_stats = [
                    ['Total Connections', total_connections],
                    ['With Credentials', with_creds],
                    ['Encrypted', encrypted_count],
                    ['Unencrypted', with_creds - encrypted_count]
                ]
                
                self.output_info("\nConnection Statistics:")
                self.output_table(conn_stats, headers=['Metric', 'Count'])

                # Encrypted fields
                self.output_info("\nEncrypted Fields:")
                fields = sorted(cipher.ENCRYPTED_FIELDS)
                field_rows = [[field] for field in fields]
                self.output_table(field_rows, headers=['Field Name'])

            return 0

        except Exception as e:
            self.log_error(f"Error generating statistics: {e}")
            self.output_error(f"Error generating statistics: {e}")
            return 1

    def close(self):
        """Clean up resources"""
        self.log_debug("Closing crypto CLI")
        super().close()


def main():
    """Entry point for crypto CLI"""
    parser = argparse.ArgumentParser(
        description=CLI_DESCRIPTION,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  crypto check                  # Check encryption key configuration
  crypto generate-key           # Generate new encryption key
  crypto test                   # Test encryption functionality
  crypto check-connections      # Check connection encryption status
  crypto migrate                # Encrypt unencrypted credentials
  crypto stats                  # Show encryption statistics
        """
    )

    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    parser.add_argument('--no-icons', action='store_true', help='Disable icons in output')
    parser.add_argument('--table-format', choices=['simple', 'grid', 'pipe', 'orgtbl'],
                       help='Table format')

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Check command
    check_parser = subparsers.add_parser('check', help='Check encryption key configuration')

    # Generate key command
    genkey_parser = subparsers.add_parser('generate-key', help='Generate new encryption key')
    genkey_parser.add_argument('--output', '-o', help='Save key to file')
    genkey_parser.add_argument('--force', '-f', action='store_true', help='Force overwrite existing key')

    # Rotate key command
    rotate_parser = subparsers.add_parser('rotate-key', help='Rotate encryption key')
    rotate_parser.add_argument('--new-key-file', help='File containing new key')

    # Test command
    test_parser = subparsers.add_parser('test', help='Test encryption functionality')

    # Encrypt command
    encrypt_parser = subparsers.add_parser('encrypt', help='Encrypt a value')
    encrypt_parser.add_argument('--value', help='Value to encrypt (will prompt if not provided)')
    encrypt_parser.add_argument('--type', default='password', help='Type of value (password, api_key, etc.)')

    # Decrypt command
    decrypt_parser = subparsers.add_parser('decrypt', help='Decrypt a value')
    decrypt_parser.add_argument('value', help='Encrypted value to decrypt')

    # Check connections command
    checkconn_parser = subparsers.add_parser('check-connections', help='Check connection encryption status')
    checkconn_parser.add_argument('--details', '-d', action='store_true', help='Show detailed status')

    # Migrate command
    migrate_parser = subparsers.add_parser('migrate', help='Migrate unencrypted connections')
    migrate_parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')

    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show encryption statistics')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Initialize CLI
    cli = None
    try:
        cli = CryptoCLI(
            verbose=args.verbose,
            show_icons=not args.no_icons,
            table_format=args.table_format
        )
    except Exception as e:
        print(f"Error initializing CLI: {e}")
        return 1

    # Execute command
    try:
        if args.command == 'check':
            return cli.check_key()

        elif args.command == 'generate-key':
            return cli.generate_key(args.output, args.force)

        elif args.command == 'rotate-key':
            return cli.rotate_key(args.new_key_file)

        elif args.command == 'test':
            return cli.test_encryption()

        elif args.command == 'encrypt':
            return cli.encrypt_value(args.value, args.type)

        elif args.command == 'decrypt':
            return cli.decrypt_value(args.value)

        elif args.command == 'check-connections':
            return cli.check_connections(args.details)

        elif args.command == 'migrate':
            return cli.migrate_connections(args.dry_run)

        elif args.command == 'stats':
            return cli.stats()

    except KeyboardInterrupt:
        if cli:
            cli.log_info("Operation cancelled by user")
        print("\nOperation cancelled")
        return 1
    except Exception as e:
        if cli:
            cli.log_error(f"Unexpected error: {e}")
        print(f"Error: {e}")
        return 1
    finally:
        if cli:
            cli.close()

    return 0


if __name__ == '__main__':
    sys.exit(main())