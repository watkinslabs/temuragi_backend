import uuid
from datetime import datetime, timedelta
from functools import wraps
from flask import session, g, current_app, jsonify
from sqlalchemy.orm import Session

from app.register.classes import get_model

class AuthService:
    """Authentication service for handling user auth operations"""
    __depends_on__=[]
    
    def __init__(self, db_session: Session):
        
        self.db_session = db_session
        self.lockout_threshold = 5  # Failed attempts before lockout
        self.lockout_duration = 30  # Minutes
        self.User = get_model('User')
        self.UserToken = get_model('UserToken')

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
        session['user_id'] = str(user.id)
        session['username'] = user.username
        session['role_id'] = str(user.role_id) if user.role_id else None

        if remember:
            session.permanent = True
            current_app.permanent_session_lifetime = timedelta(days=30)

        self.db_session.commit()

        return {'success': True, 'message': 'Login successful', 'user': user}

    def login_api(self, identity: str, password: str, remember: bool = False, application: str = 'web') -> dict:
        """
        Authenticate user and create API tokens for SPA/API usage
        
        Args:
            identity: Username or email
            password: User password
            remember: Whether to extend token lifetime
            application: Application context (default 'web')
            
        Returns:
            dict: Result with tokens and user info
        """
        # First perform standard login validation
        login_result = self.login(identity, password, remember)
        
        if not login_result['success']:
            return login_result
        
        user = login_result['user']
        
        # Clean up expired tokens for this user before creating new ones
        self._cleanup_user_tokens(user.id)
        
        # Check for existing valid refresh token for this application
        existing_refresh = self._get_valid_refresh_token(user.id, application)
        
        if existing_refresh:
            # Reuse existing refresh token and create new access token
            try:
                access_token = existing_refresh.refresh_access_token(self.db_session)
                
                return {
                    'success': True,
                    'message': 'Login successful',
                    'api_token': access_token.token,
                    'refresh_token': existing_refresh.token,
                    'user_id': str(user.id),
                    'user_info': {
                        'username': user.username,
                        'email': user.email,
                        'full_name': getattr(user, 'full_name', None),
                        'role': str(user.role_id) if user.role_id else None
                    },
                    'expires_in': access_token.expires_in_seconds(),
                    'redirect_url': '/v2/'
                }
            except Exception as e:
                # If reuse fails, create new tokens below
                current_app.logger.warning(f"Failed to reuse tokens: {str(e)}")
        
        # Create new token pair
        try:
            # Revoke any remaining active tokens for this application
            self._revoke_application_tokens(user.id, application)
            
            tokens = self.UserToken.create_token_pair(
                session=self.db_session,
                user_id=user.id,
                name=f"{application} login",
                application=application,
                is_system_temporary=False
            )
            
            return {
                'success': True,
                'message': 'Login successful',
                'api_token': tokens['access_token'].token,
                'refresh_token': tokens['refresh_token'].token,
                'user_id': str(user.id),
                'user_info': {
                    'username': user.username,
                    'email': user.email,
                    'full_name': getattr(user, 'full_name', None),
                    'role': str(user.role_id) if user.role_id else None
                },
                'expires_in': tokens['access_token'].expires_in_seconds(),
                'redirect_url': '/v2/'
            }
            
        except Exception as e:
            # Log the error
            current_app.logger.error(f"Token creation failed: {str(e)}")
            return {
                'success': False,
                'message': 'Failed to create authentication tokens',
                'user': None
            }

    def refresh_token(self, refresh_token: str) -> dict:
        """
        Create new access token using refresh token
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            dict: New access token or error
        """
        # Validate refresh token
        token_obj = self.UserToken.validate_refresh_token(self.db_session, refresh_token)
        
        if not token_obj:
            return {
                'success': False,
                'message': 'Invalid or expired refresh token'
            }
        
        try:
            # Create new access token
            new_access_token = token_obj.refresh_access_token(self.db_session)
            
            return {
                'success': True,
                'api_token': new_access_token.token,
                'expires_in': new_access_token.expires_in_seconds(),
                'user_id': str(token_obj.user_id)
            }
            
        except Exception as e:
            current_app.logger.error(f"Token refresh failed: {str(e)}")
            return {
                'success': False,
                'message': 'Failed to refresh token'
            }

    def validate_api_token(self, token: str) -> dict:
        """
        Validate an API token and return user info
        
        Args:
            token: Access token to validate
            
        Returns:
            dict: Validation result with user info
        """
        token_obj = self.UserToken.validate_access_token(self.db_session, token)
        
        if not token_obj:
            return {
                'success': False,
                'message': 'Invalid or expired token'
            }
        
        user = token_obj.user
        
        return {
            'success': True,
            'user_id': str(user.id),
            'user_info': {
                'username': user.username,
                'email': user.email,
                'full_name': getattr(user, 'full_name', None),
                'role': str(user.role_id) if user.role_id else None
            },
            'token_info': {
                'expires_in': token_obj.expires_in_seconds(),
                'application': token_obj.application
            }
        }

    def logout_api(self, access_token: str = None, user_id: str = None) -> dict:
        """
        Logout API user by revoking tokens
        
        Args:
            access_token: Current access token to revoke
            user_id: User UUID to revoke all tokens for
            
        Returns:
            dict: {'success': bool, 'message': str}
        """
        if access_token:
            token_obj = self.UserToken.find_by_token(self.db_session, access_token)
            if token_obj:
                # Revoke the token and any linked tokens
                token_obj.revoke()
                self.db_session.commit()
        
        if user_id:
            # Revoke all active tokens for user
            user_tokens = self.db_session.query(self.UserToken).filter(
                self.UserToken.user_id == user_id,
                self.UserToken.is_active == True
            ).all()
            
            for token in user_tokens:
                token.revoke()
            
            self.db_session.commit()
        
        # Also clear session if exists
        session.clear()
        
        return {'success': True, 'message': 'Logged out successfully'}
   
    def register(self, username: str, email: str, password: str, role_id: str = None) -> dict:
        """
        Register new user
        
        Args:
            username: Unique username
            email: Unique email address
            password: User password
            role_id: Optional role UUID
            
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
            id=uuid.uuid4(),
            username=username,
            email=email,
            role_id=role_id,
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
    
    def _cleanup_user_tokens(self, user_id: uuid.UUID) -> None:
        """
        Clean up expired tokens for a user
        
        Args:
            user_id: User UUID to clean tokens for
        """
        try:
            # Delete expired tokens
            expired_tokens = self.db_session.query(self.UserToken).filter(
                self.UserToken.user_id == user_id,
                self.UserToken.expires_at < datetime.utcnow(),
                self.UserToken.ignore_expiration == False
            ).all()
            
            for token in expired_tokens:
                self.db_session.delete(token)
            
            self.db_session.commit()
        except Exception as e:
            current_app.logger.error(f"Token cleanup failed: {str(e)}")
            self.db_session.rollback()
    
    def _get_valid_refresh_token(self, user_id: uuid.UUID, application: str) -> 'UserToken':
        """
        Get existing valid refresh token for user and application
        
        Args:
            user_id: User UUID
            application: Application context
            
        Returns:
            UserToken or None
        """
        return self.db_session.query(self.UserToken).filter(
            self.UserToken.user_id == user_id,
            self.UserToken.application == application,
            self.UserToken.token_type == 'refresh',
            self.UserToken.is_active == True,
            (self.UserToken.expires_at > datetime.utcnow()) | (self.UserToken.ignore_expiration == True)
        ).first()
    
    def _revoke_application_tokens(self, user_id: uuid.UUID, application: str) -> None:
        """
        Revoke all tokens for a specific application
        
        Args:
            user_id: User UUID
            application: Application context
        """
        tokens = self.db_session.query(self.UserToken).filter(
            self.UserToken.user_id == user_id,
            self.UserToken.application == application,
            self.UserToken.is_active == True
        ).all()
        
        for token in tokens:
            token.revoke()
        
        self.db_session.commit()
    
    def cleanup_expired_tokens(self, days_old: int = 7) -> dict:
        """
        Clean up all expired tokens older than specified days
        This should be run as a scheduled task
        
        Args:
            days_old: Delete tokens expired more than this many days ago
            
        Returns:
            dict: Cleanup statistics
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            # Count tokens to be deleted
            count = self.db_session.query(self.UserToken).filter(
                self.UserToken.expires_at < cutoff_date,
                self.UserToken.ignore_expiration == False
            ).count()
            
            # Delete expired tokens
            self.db_session.query(self.UserToken).filter(
                self.UserToken.expires_at < cutoff_date,
                self.UserToken.ignore_expiration == False
            ).delete()
            
            # Also delete soft-deleted tokens older than cutoff
            self.db_session.query(self.UserToken).filter(
                self.UserToken.is_active == False,
                self.UserToken.updated_at < cutoff_date
            ).delete()
            
            self.db_session.commit()
            
            return {
                'success': True,
                'message': f'Cleaned up {count} expired tokens',
                'tokens_deleted': count
            }
            
        except Exception as e:
            self.db_session.rollback()
            current_app.logger.error(f"Token cleanup failed: {str(e)}")
            return {
                'success': False,
                'message': f'Cleanup failed: {str(e)}',
                'tokens_deleted': 0
            }


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


def api_login_required(f):
    """
    Decorator to require API token authentication
    
    Usage:
        @api_login_required
        def protected_api_endpoint():
            # Only authenticated API users can access
            pass
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask import request
        
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing or invalid authorization header'}), 401
        
        token = auth_header.split(' ')[1]
        
        # Validate token
        auth_service = get_auth_service()
        validation_result = auth_service.validate_api_token(token)
        
        if not validation_result['success']:
            return jsonify({'error': validation_result['message']}), 401
        
        # Store user info in g for access in the view
        g.current_user_id = validation_result['user_id']
        g.current_user_info = validation_result['user_info']
        g.token_info = validation_result['token_info']
        
        return f(*args, **kwargs)
    
    return decorated_function


def get_auth_service() -> AuthService:
    """
    Helper to get auth service with current db session
    
    Returns:
        AuthService instance
    """
    return AuthService(g.session)