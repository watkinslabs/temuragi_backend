from flask import request, current_app
from datetime import datetime, timedelta
from app._system.auth.auth_log_model import LoginLog
from app._system.auth.reset_token_model import ResetToken
from app._system.user.user_model import User

class AuthService:
    """Service for handling authentication operations"""
    
    @staticmethod
    def get_client_ip():
        """Get client IP address from request"""
        if request:
            return request.remote_addr
        return "0.0.0.0"
        
    @classmethod
    def login(cls, db_session, identity, password):
        """Authenticate a user with username/email and password"""
        # Find user by username or email
        user = User.find_by_identity(db_session, identity)
        
        # Handle case where user is not found
        if not user:
            # Log login attempt with anonymous user_id
            LoginLog.record_login(
                db_session,
                None,
                identity, 
                password,
                False, 
                False, 
                cls.get_client_ip()
            )
            return False, None, "Either your username or password is incorrect."
        
        # Check if account is locked
        now = datetime.utcnow()
        if user.is_locked:
            # Check if temporary lockout has expired
            if user.locked_until and user.locked_until < now:
                user.is_locked = False
                user.failed_login_attempts = 0
                user.locked_until = None
                db_session.commit()
            else:
                # Account is still locked
                LoginLog.record_login(
                    db_session,
                    user.uuid,
                    identity, 
                    password,
                    False, 
                    True, 
                    cls.get_client_ip()
                )
                return False, None, "Account is locked. Please try again later or reset your password."
        
        # Verify password
        if user.check_password(password):
            # Reset failed attempts
            user.failed_login_attempts = 0
            user.locked_until = None
            
            # Update last login time
            user.last_login_date = now
            
            # Commit changes
            db_session.commit()
            
            # Log successful login
            LoginLog.record_login(
                db_session,
                user.uuid,
                identity, 
                password,
                True, 
                False, 
                cls.get_client_ip()
            )
            
            # Return user info
            return True, user.to_dict(), None
        
        # Handle failed login attempt
        user.failed_login_attempts += 1
        
        # Check if account should be locked
        max_attempts = current_app.config.get('MAX_LOGIN_ATTEMPTS', 5)
        if user.failed_login_attempts >= max_attempts:
            user.is_locked = True
            # Lock for 30 minutes by default
            lockout_minutes = current_app.config.get('ACCOUNT_LOCKOUT_MINUTES', 30)
            user.locked_until = now + timedelta(minutes=lockout_minutes)
        
        db_session.commit()
        
        # Log failed login
        LoginLog.record_login(
            db_session,
            user.uuid,
            identity, 
            password,
            False, 
            user.is_locked, 
            cls.get_client_ip()
        )
        
        return False, None, "Either your username or password is incorrect."
    
    @classmethod
    def reset_password(cls, db_session, token, new_password):
        """Reset a user's password using a token"""
        # Verify token
        reset_token = ResetToken.verify(db_session, token)
        
        if not reset_token:
            return False, "Invalid or expired reset token."
        
        # Find user
        user = User.find_by_id(db_session, reset_token.user_uuid)
        
        if not user:
            return False, "User not found."
        
        # Update password
        user.set_password(new_password)
        
        # Unlock account if it was locked
        user.is_locked = False
        user.failed_login_attempts = 0
        user.locked_until = None
        
        # Mark token as used
        reset_token.consume(db_session)
        db_session.commit()
        
        return True, "Password has been reset successfully."
        
    @classmethod
    def unlock_account(cls, db_session, user_uuid):
        """Unlock a user account"""
        user = User.find_by_id(db_session, user_uuid)
        
        if not user:
            return False, "User not found."
            
        if not user.is_locked:
            return False, "Account is not locked."
            
        user.is_locked = False
        user.failed_login_attempts = 0
        user.locked_until = None
        db_session.commit()
        
        return True, "Account has been unlocked."