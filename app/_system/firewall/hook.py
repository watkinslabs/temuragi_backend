from flask import  render_template, request, current_app, g

from app.models import Firewall, FirewallLog


def get_client_ip():
    """Get client IP address from request headers or remote_addr"""
    # Get IP from X-Forwarded-For header (HAProxy adds this)
    forwarded_for = request.headers.get('X-Forwarded-For')
    
    if forwarded_for:
        # The leftmost IP in the list is the original client IP
        client_ip = forwarded_for.split(',')[0].strip()
    else:
        # Fallback to remote address if header not present
        client_ip = request.remote_addr
    
    return client_ip
    
def register_firewall_handlers(app):
    """Register firewall IP access control handlers."""
    @app.before_request
    def check_ip_access():
        # Get the client IP
        ip = get_client_ip()
        
        # Get database session
        db_session = g.session if hasattr(g, 'session') else current_app.db_session
        
        # Check if access is allowed
        allowed, reason = Firewall.check_ip_access(db_session, ip)
        
        # Log the request (if you have a logging mechanism)
        try:
            # This assumes you have a separate logging mechanism
            # If not, you can remove this part or implement it separately
            log_ip_request(db_session, ip, allowed, reason)
            app.logger.info(f"Firewall:  {ip}, Allowed: {allowed}, Msg: {reason}")
        except Exception as e:
            # Don't block requests due to logging errors
            app.logger.error(f"Error logging IP request: {str(e)}")
        
        if not allowed:
            # Block access with a 403 Forbidden response
            app.logger.warning(f"Blocked IP access: {ip}, reason: {reason}")
            return render_template('firewall/blocked.html', 
                                  reason=reason,
                                  contact_email=current_app.config.get('ADMIN_EMAIL')), 403


def log_ip_request(db_session, ip, allowed, reason):
    """Log IP request for audit purposes"""
    try:
        # Get request details
        request_path = request.path
        user_agent = request.headers.get('User-Agent')
        request_method = request.method
        referer = request.headers.get('Referer')
        
        # Extract matched rule from reason if available
        matched_rule = None
        if reason and "pattern:" in reason:
            parts = reason.split("pattern:", 1)
            if len(parts) > 1:
                matched_rule = parts[1].split("(", 1)[0].strip()
        
        # Log the request
        FirewallLog.log_request(
            db_session,
            ip_address=ip,
            status=allowed,
            request_path=request_path,
            user_agent=user_agent,
            request_method=request_method,
            referer=referer,
            matched_rule=matched_rule
        )
    except Exception as e:
        current_app.logger.error(f"Error in log_ip_request: {str(e)}")