import os
import fnmatch
from datetime import datetime
from flask import request, redirect, url_for, current_app, session, render_template

class IPFilter:
    def __init__(self,):
        pass
        
    def _ip_matches(self, ip, patterns):
        for pattern in patterns:
            if fnmatch.fnmatch(ip, pattern):
                return True
        return False

    def get_client_ip(self):
        # Get IP from X-Forwarded-For header (HAProxy adds this)
        forwarded_for = request.headers.get('X-Forwarded-For')
        
        if forwarded_for:
            # The leftmost IP in the list is the original client IP
            client_ip = forwarded_for.split(',')[0].strip()
        else:
            # Fallback to remote address if header not present
            client_ip = request.remote_addr
        
        return client_ip
        
    def load_patterns(self):
        db = current_app.db
        database=current_app.config['DEFAULT_DATABASE'] 
        schema=current_app.config['DEFAULT_SCHEMA'] 
        
        try:
            #print("Fetching IPS")
            rows=db.fetch_all("SELECT ip_pattern, ip_type FROM VirtualReports.dbo.ip_filter")
            whitelist = [row.ip_pattern for row in rows if row. ip_type== 'whitelist']
            blacklist = [row.ip_pattern for row in rows if row.ip_type == 'blacklist']
            #print("DONE Fetching IPS")
            return whitelist, blacklist
        except Exception as e:
            print(f"FAILED {e}")
            whitelist =[ '*.*.*.*' ]
            blacklist =[]
            return whitelist, blacklist

            
    def log_ip_request(self, ip_address, status, request_path=None):
        """
        Log an IP request with status (allowed/blocked) and request path
        
        Args:
            ip_address (str): The IP address making the request
            status (bool or int): True/1 for allowed, False/0 for blocked
            request_path (str, optional): The requested URL path. If None, gets current path.
        
        Returns:
            tuple: (success, message) or (None, None) if request shouldn't be logged
        """
        # Get current request path if not provided
        if request_path is None:
            try:
                request_path = request.path
            except RuntimeError:
                # Not in request context
                request_path = "Unknown"
        
        # Check if we should log this request
        should_log = False
        
        # Path ends with .php
        if request_path.lower().endswith('.php'):
            should_log = True
        # Path ends with /
        elif request_path.endswith('/'):
            should_log = True
        # Path has no extension in the last segment
        else:
            last_segment = os.path.basename(request_path)
            if '.' not in last_segment:
                should_log = True
        
        # Skip logging if it's not a path we want to track
        if not should_log:
            return None, None
        
        
        table = "VirtualReports.dbo.ip_request_log"
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Convert to boolean if it's not already
        status_bool = bool(status)
        status_str = 'allowed' if status_bool else 'blocked'
        
        user_id=session.get('user_id',None)
        insert_query = f"""
        INSERT INTO {table}
        (ip_address, timestamp, status, request_path, user_id)
        VALUES (:ip_address, :timestamp, :status, :request_path, :user_id)
        """

        # Get current request path if not provided
        if request_path is None:
            try:
                request_path = request.path
            except RuntimeError:
                # Not in request context
                request_path = "Unknown"        
        
        params = {
            "ip_address": ip_address,
            "timestamp": timestamp,
            "status": status_bool,  # Will be converted to bit in SQL
            "request_path": request_path,
            "user_id": user_id
        }
        
        try:
            current_app.db.execute(insert_query, params)
            return True, f'Logged {status_str} request from {ip_address}'
        except Exception as e:
            return False, f'Error logging request: {e}'                
