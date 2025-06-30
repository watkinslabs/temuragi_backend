from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, g

from .firewall_model import Firewall
from .firewall_log_model import FirewallLog  

bp = Blueprint('firewall', __name__, url_prefix="/firewall", template_folder="tpl")


@bp.teardown_request
def close_session(exc):
    """Close session after request is done"""
    sess = g.pop('session', None)
    if sess:
        sess.close()

@bp.route('/', methods=['GET'])
def home():
    """Main IP filter management page"""
    ip_patterns = Firewall.get_all_patterns()
    return render_template('firewall/home.html', ip_patterns=ip_patterns)

@bp.route('/add', methods=['POST'])
def add_pattern():
    """Add a new IP pattern with validation"""
    ip_pattern = request.form.get('ip_pattern', '').strip()
    ip_type = request.form.get('ip_type')
    
    if not ip_pattern:
        flash('IP pattern cannot be empty', 'error')
        return redirect(url_for('firewall.home'))
    
    # Validate IP pattern format before proceeding
    is_valid, validation_message = Firewall.validate_ip_pattern(ip_pattern)
    if not is_valid:
        # Sanitize error message - extract the main error without technical details
        error_msg = f"Invalid IP pattern: {ip_pattern}"
        if "does not appear to be an IPv4 or IPv6 network" in validation_message:
            error_msg = f"'{ip_pattern}' is not a valid IP address or network"
        elif "has host bits set" in validation_message:
            error_msg = f"CIDR format error in '{ip_pattern}' - please check the network mask"
        
        flash(error_msg, 'error')
        return redirect(url_for('firewall.home'))
    
    # Convert whitelist/blacklist to allow/block
    if ip_type == 'whitelist':
        ip_type = 'allow'
    elif ip_type == 'blacklist':
        ip_type = 'block'
    else:
        flash('Invalid IP type', 'error')
        return redirect(url_for('firewall.home'))
    
    success, message = Firewall.add_pattern( ip_pattern, ip_type)
    
    # Clean the message to remove any potential JavaScript issues
    clean_message = message.replace("'", "").replace('"', "")
    
    flash(clean_message, 'success' if success else 'error')
    return redirect(url_for('firewall.home'))

@bp.route('/delete/<uuid:pattern_id>', methods=['POST'])
def delete_pattern(pattern_id):
    """Delete an IP pattern"""
    success, message = Firewall.delete_pattern( pattern_id)
    
    # Clean the message to remove any potential JavaScript issues
    clean_message = message.replace("'", "").replace('"', "")
    
    flash(clean_message, 'success' if success else 'error')
    return redirect(url_for('firewall.home'))

@bp.route('/logs', methods=['GET'])
def view_logs():
    """View IP request logs"""
    ip_address = request.args.get('ip_address', '')
    status_param = request.args.get('status', '')
    days = request.args.get('days', '7')
    
    try:
        days = int(days)
    except ValueError:
        days = 7
    
    # Convert status string to boolean
    status = None
    if status_param == 'allowed':
        status = True
    elif status_param == 'blocked':
        status = False
    
    logs_data, total_count = FirewallLog.get_request_logs(ip_address, status, days)
    
    # Format logs to match template expectations
    logs = []
    for log in logs_data:
        logs.append({
            'timestamp': log.created_at,
            'ip_address': log.ip_address,
            'status': 'allowed' if log.status else 'blocked',
            'request_path': log.request_path or ''
        })
    
    return render_template('firewall/logs.html', 
                          logs=logs, 
                          ip_address=ip_address,
                          status=status_param,
                          days=days)

@bp.route('/stats', methods=['GET'])
def view_stats():
    """View IP filter statistics"""
    days = request.args.get('days', '7')
    
    try:
        days = int(days)
    except ValueError:
        days = 7
    
    top_blocked_raw = FirewallLog.get_top_blocked_ips(days)
    top_allowed_raw = FirewallLog.get_top_allowed_ips(days)
    daily_stats = FirewallLog.get_daily_stats( days)
    
    # Format data to match template expectations
    top_blocked = [{'ip_address': ip, 'count': count} for ip, count in top_blocked_raw]
    top_allowed = [{'ip_address': ip, 'count': count} for ip, count in top_allowed_raw]
    
    return render_template('firewall/stats.html',
                          top_blocked=top_blocked,
                          top_allowed=top_allowed,
                          daily_stats=daily_stats,
                          days=days)