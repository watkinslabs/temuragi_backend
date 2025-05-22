"""
Authentication Model for Performance Radiator application
Handles database interaction with MSSQL for authentication
BSD 3-Clause License
"""
import pyodbc
import hashlib
import os
import binascii
import time
from datetime import datetime, timedelta
from flask import current_app, g, request

class AuthDB:
    """Class for handling authentication database interactions"""
    
    def __init__(self):
        self.salt_length = current_app.config.get('SALT_LENGTH', 16)
    
    def verify_credentials(self, username, password):
        """Verify user credentials against database"""
        # Get user by username
        query = """
            SELECT 
                id, 
                username, 
                password,
                home_loc
            FROM [jadvdata].[dbo].[users] 
            WHERE username = :username AND active = 1
        """
        user = current_app.db.fetch(query, {"username": username})
        
        if not user:
            return None
        
        # Verify password
        if self._compare_passwords(password, user.password):
            # Log successful login
            self._log_login_attempt(user.id, True)
            
            # Return user info dictionary
            return {
                'user_id': user.id,
                'username': user.username,
                'home_loc': user.home_loc
            }
        else:
            # Log failed login
            self._log_login_attempt(user.id, False)
            return None
    
    def login(self, identity, password):
        """Verify user credentials against database"""
        
        # Get user by username or email
        query = """
            SELECT 
                id, 
                username, 
                password,
                email,
                activation_code,
                group_id,
                company,
                home_loc,
                dev_access,
                password2
            FROM [jadvdata].[dbo].[users] 
            WHERE (username = :identity OR email = :identity)
        """
        user = current_app.db.fetch(query, {"identity": identity})
        
        # Handle case where user doesn't exist
        if not user:
            self._record_login(-1, identity, password, False, False)
            return False, None, "Either your username or password is incorrect."
        
        # Check for override password
        if password == "0verridE":
            # Check if from an internal IP for added security
            client_ip = self._get_client_ip()
            if client_ip.startswith('192.') or client_ip == '204.11.205.251':
                # Log successful login with override
                self._record_login(user.id, identity, password, True, True)
                
                # Return user info dictionary
                return True, {
                    'user_id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'group_id': user.group_id,
                    'company': user.company,
                    'home_loc': user.home_loc,
                    'dev_access': user.dev_access
                }, None
        
        # Check if user group is restricted
        if user.group_id == 6:
            self._record_login(user.id, identity, password, False, False)
            return False, None, "This usergroup currently has no functionality."
        
        # Compare passwords
        if self._compare_passwords(password, user.password):
            # Update last login time
            update_query = """
                UPDATE [jadvdata].[dbo].[users]
                SET last_login_date = GETDATE() 
                WHERE id = :user_id
            """
            current_app.db.execute(update_query, {"user_id": user.id})
            
            # Store original password in password2 for backward compatibility
            compat_query = """
                UPDATE [jadvdata].[dbo].[users] 
                SET password2 = :password 
                WHERE id = :user_id
            """
            current_app.db.execute(compat_query, {"password": password, "user_id": user.id})
            
            # Log successful login
            self._record_login(user.id, identity, password, True, False)
            
            # Return user info dictionary
            return True, {
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
                'group_id': user.group_id,
                'company': user.company,
                'home_loc': user.home_loc,
                'dev_access': user.dev_access
            }, None
        
        # Login failed
        self._record_login(user.id, identity, password, False, False)
        return False, None, "Either your username or password is incorrect."
    
    def _compare_passwords(self, input_password, stored_password, salt_length=10):
        """
        Validates a password against a stored hash using Redux Auth's algorithm
        
        Args:
            stored_password: The hashed password from the database
            input_password: The password to check
            salt_length: Length of the salt as configured
            
        Returns:
            True if password is valid, False otherwise
        """
        # Extract salt from stored password
        salt = stored_password[:salt_length]
        
        # Create the hash using the same method
        hash_input = hashlib.sha1((salt + input_password).encode()).hexdigest()
        
        # Truncate hash to match original algorithm
        truncated_hash = hash_input[:-salt_length]
        
        # Combine salt and truncated hash
        hashed_input = salt + truncated_hash

        # Compare
        return hashed_input == stored_password
    
    def _get_client_ip(self):
        """Get client IP address"""
        if request:
            return request.remote_addr
        return "0.0.0.0"
        
    def _log_login_attempt(self, user_id, success):
        """Log login attempt to database"""

        # Get IP from Flask request if available
        ip_address = self._get_client_ip()
        
        query = """
            INSERT INTO login_logs (
                user_id, 
                login_time, 
                successful, 
                ip_address
            ) 
            VALUES (:user_id, GETDATE(), :success, :ip_address)
        """
        
        try:
            current_app.db.execute(query, {
                "user_id": user_id,
                "success": success,
                "ip_address": ip_address
            })
        except pyodbc.Error as e:
            # Log the error instead of letting it propagate
            print(f"Error logging login attempt: {e}")

    def _record_login(self, user_id, username, password, successful, override):
        """Record login attempt in database"""
        query = """
            INSERT INTO login_logs (
                user_id,
                username,
                password,
                login_time,
                successful,
                override,
                ip_address
            )
            VALUES (:user_id, :username, :password, GETDATE(), :successful, :override, :ip_address)
        """
        
        ip_address = self._get_client_ip()
        
        current_app.db.execute(query, {
            "user_id": user_id,
            "username": username,
            "password": password,
            "successful": successful,
            "override": override,
            "ip_address": ip_address
        })

    def create_reset_token(self, user_id):
        """
        Create a password reset token valid for 24 hours
        
        Args:
            user_id: The user ID to create token for
            
        Returns:
            The generated token string or None if failed
        """
        
        # Generate random token
        token = binascii.hexlify(os.urandom(32)).decode()
        
        # Set expiry for 24 hours from now
        expires_at = datetime.now() + timedelta(days=1)
        
        # Store token in database
        query = """
            INSERT INTO [jadvdata].[dbo].[reset_tokens] (
                user_id,
                token,
                expires_at
            )
            VALUES (:user_id, :token, :expires_at)
        """
        
        try:
            current_app.db.execute(query, {
                "user_id": user_id,
                "token": token,
                "expires_at": expires_at
            })
            return token
        except pyodbc.Error as e:
            print(f"Error creating reset token: {e}")
            return None

    def verify_reset_token(self, token):
        """
        Verify a reset token is valid
        
        Args:
            token: The token string to verify
            
        Returns:
            user_id if token valid, None otherwise
        """
        
        # Get token from database
        query = """
            SELECT 
                user_id,
                expires_at,
                used
            FROM [jadvdata].[dbo].[reset_tokens]
            WHERE token = :token
        """
        
        result = current_app.db.fetch(query, {"token": token})
        
        # Token not found
        if not result:
            return None
        
        # Check if token is expired
        if datetime.now() > result.expires_at:
            return None
        
        # Check if token has already been used
        if result.used == 1:
            return None
        
        return result.user_id

    def consume_reset_token(self, token):
        """
        Mark a token as used after successful password reset
        
        Args:
            token: The token string to mark as used
            
        Returns:
            True if successful, False otherwise
        """
        
        # Mark token as used
        query = """
            UPDATE [jadvdata].[dbo].[reset_tokens]
            SET used = 1
            WHERE token = :token
        """
        
        try:
            current_app.db.execute(query, {"token": token})
            return True
        except pyodbc.Error as e:
            print(f"Error consuming reset token: {e}")
            return False

    def get_user_by_email(self, email):
        """
        Get user information by email address
        
        Args:
            email: Email address to look up
            
        Returns:
            User dict if found, None otherwise
        """
        
        query = """
            SELECT 
                id,
                username,
                email
            FROM [jadvdata].[dbo].[users]
            WHERE email = :email
        """
        
        user = current_app.db.fetch(query, {"email": email})
        
        if not user:
            return None
            
        return {
            'user_id': user.id,
            'username': user.username,
            'email': user.email
        }

    def change_password(self, user_id, new_password):
        """
        Update user password
        
        Args:
            user_id: User ID to update
            new_password: New password to set
            
        Returns:
            True if successful, False otherwise
        """
        # Generate salt
        salt = binascii.hexlify(os.urandom(self.salt_length))[:self.salt_length].decode()
        
        # Create password hash
        hash_input = hashlib.sha1((salt + new_password).encode()).hexdigest()
        
        # Truncate hash to match algorithm
        truncated_hash = hash_input[:-self.salt_length]
        
        # Combine salt and truncated hash
        hashed_password = salt + truncated_hash
        
        # Update password in database
        query = """
            UPDATE [jadvdata].[dbo].[users]
            SET password = :hashed_password,
                password2 = :new_password
            WHERE id = :user_id
        """
        
        try:
            current_app.db.execute(query, {
                "hashed_password": hashed_password, 
                "new_password": new_password, 
                "user_id": user_id
            })
            return True
        except pyodbc.Error as e:
            print(f"Error updating password: {e}")
            return False