import uuid
from datetime import datetime, timedelta
from functools import wraps
from flask import session, g, current_app
from sqlalchemy.orm import Session

from app.register.database import get_model

class AuthService:
    """Authentication service for handling user auth operations"""
    
    def __init__(self, db_session: Session):
        
        self.db_session = db_session
        self.lockout_threshold = 5  # Failed attempts before lockout
        self.lockout_duration = 30  # Minutes
        self.User = get_model('User')

    def login(self, identity: str, password: str, remember: bool = False) -> dict:
        """
        Authenticate user and create session

        Args:
            identity: Username or email
            password: User password
            remember: Whether to remember user session
            
        Returns:
            dict: {'success': bool, 'message': str, 'user': User or None}
        """
        user = self.User.find_by_identity(self.db_session, identity)

        if not user:
            return {'success': False, 'message': 'Invalid username or password', 'user': None}

        # Check if account is locked
        if user.is_currently_locked:
            return {'success': False, 'message': 'Account is locked. Please try again later.', 'user': None}

        # Verify password
        if not user.check_password(password):
            # Increment failed login attempts
            user.failed_login_attempts += 1
            
            # Lock account if threshold reached
            if user.failed_login_attempts >= self.lockout_threshold:
                user.is_locked = True
                user.locked_until = datetime.utcnow() + timedelta(minutes=self.lockout_duration)
                self.db_session.commit()
                return {'success': False, 'message': 'Too many failed attempts. Account locked.', 'user': None}
            
            self.db_session.commit()
            return {'success': False, 'message': 'Invalid username or password', 'user': None}

        # Check if user is active
        if not user.is_active:
            return {'success': False, 'message': 'Account is disabled', 'user': None}

        # Reset failed login attempts on successful login
        user.failed_login_attempts = 0
        user.is_locked = False
        user.locked_until = None
        user.last_login_date = datetime.utcnow()

        # Create session
        session['user_id'] = str(user.uuid)
        session['username'] = user.username
        session['role_uuid'] = str(user.role_uuid) if user.role_uuid else None

        if remember:
            session.permanent = True
            current_app.permanent_session_lifetime = timedelta(days=30)

        self.db_session.commit()

        return {'success': True, 'message': 'Login successful', 'user': user}

    def logout(self) -> dict:
        """
        Logout current user and clear session
        
        Returns:
            dict: {'success': bool, 'message': str}
        """
        session.clear()
        return {'success': True, 'message': 'Logged out successfully'}
    
    def register(self, username: str, email: str, password: str, role_uuid: str = None) -> dict:
        """
        Register new user
        
        Args:
            username: Unique username
            email: Unique email address
            password: User password
            role_uuid: Optional role UUID
            
        Returns:
            dict: {'success': bool, 'message': str, 'user': User or None}
        """
        # Check if username exists
        if self.User.find_by_identity(self.db_session, username):
            return {'success': False, 'message': 'Username already exists', 'user': None}
        
        # Check if email exists
        if self.User.find_by_email(self.db_session, email):
            return {'success': False, 'message': 'Email already registered', 'user': None}
        
        # Create new user
        user = self.User(
            uuid=uuid.uuid4(),
            username=username,
            email=email,
            role_uuid=role_uuid,
            is_active=True
        )
        user.set_password(password)
        
        self.db_session.add(user)
        self.db_session.commit()
        
        return {'success': True, 'message': 'Registration successful', 'user': user}
    
    def get_current_user(self):
        """
        Get currently logged in user
        
        Returns:
            User or None
        """
        user_id = session.get('user_id')
        if not user_id:
            return None
        
        return self.User.find_by_id(self.db_session, user_id)
    
    def is_authenticated(self) -> bool:
        """
        Check if user is authenticated
        
        Returns:
            bool: True if authenticated
        """
        return 'user_id' in session
    
    def change_password(self, user_id: str, current_password: str, new_password: str) -> dict:
        """
        Change user password
        
        Args:
            user_id: User UUID
            current_password: Current password for verification
            new_password: New password to set
            
        Returns:
            dict: {'success': bool, 'message': str}
        """
        user = self.User.find_by_id(self.db_session, user_id)
        
        if not user:
            return {'success': False, 'message': 'User not found'}
        
        if not user.check_password(current_password):
            return {'success': False, 'message': 'Current password is incorrect'}
        
        user.set_password(new_password)
        self.db_session.commit()
        
        return {'success': True, 'message': 'Password changed successfully'}
    
    def reset_password(self, user_id: str, new_password: str) -> dict:
        """
        Reset user password (admin function or after email verification)
        
        Args:
            user_id: User UUID
            new_password: New password to set
            
        Returns:
            dict: {'success': bool, 'message': str}
        """
        user = self.User.find_by_id(self.db_session, user_id)
        
        if not user:
            return {'success': False, 'message': 'User not found'}
        
        user.set_password(new_password)
        user.failed_login_attempts = 0
        user.is_locked = False
        user.locked_until = None
        self.db_session.commit()
        
        return {'success': True, 'message': 'Password reset successfully'}
    
    def unlock_account(self, user_id: str) -> dict:
        """
        Manually unlock user account
        
        Args:
            user_id: User UUID
            
        Returns:
            dict: {'success': bool, 'message': str}
        """
        user = self.User.find_by_id(self.db_session, user_id)
        
        if not user:
            return {'success': False, 'message': 'User not found'}
        
        user.is_locked = False
        user.locked_until = None
        user.failed_login_attempts = 0
        self.db_session.commit()
        
        return {'success': True, 'message': 'Account unlocked successfully'}


def login_required(f):
    """
    Decorator to require authentication for views
    
    Usage:
        @login_required
        def protected_view():
            # Only authenticated users can access
            pass
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            from flask import redirect, url_for, flash
            flash('Please log in to access this page', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def get_auth_service() -> AuthService:
    """
    Helper to get auth service with current db session
    
    Returns:
        AuthService instance
    """
    return AuthService(g.session)