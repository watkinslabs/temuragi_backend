# models/ip_filter_model.py
from datetime import datetime, timedelta

class IPFilterModel:
    def __init__(self, db, database="VirtualReports", schema="dbo"):
        self.db = db
        self.database = database
        self.schema = schema
    
    def _get_table(self, table_name):
        """Build fully qualified table name"""
        database = self.database or self.db.config.get('DEFAULT_DATABASE', 'VirtualReports')
        schema = self.schema or self.db.config.get('DEFAULT_SCHEMA', 'dbo')
        return f"{database}.{schema}.{table_name}"
    
    def get_all_patterns(self):
        """Get all IP patterns from the database"""
        table = self._get_table("ip_filter")
        query = f"SELECT ip_id, ip_pattern, ip_type, created_at FROM {table} ORDER BY ip_type, ip_pattern"
        return self.db.fetch_all(query)
    
    def add_pattern(self, ip_pattern, ip_type):
        """Add a new IP pattern to the database"""
        table = self._get_table("ip_filter")
        
        # Check if pattern already exists
        check_query = f"SELECT ip_id FROM {table} WHERE ip_pattern = :ip_pattern"
        exists = self.db.fetch(check_query, {"ip_pattern": ip_pattern})
        
        if exists:
            return False, f'IP pattern "{ip_pattern}" already exists'
        
        # Add new pattern
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        insert_query = f"""
        INSERT INTO {table} 
        (ip_pattern, ip_type, created_at) 
        VALUES (:ip_pattern, :ip_type, :created_at)
        """
        params = {
            "ip_pattern": ip_pattern,
            "ip_type": ip_type,
            "created_at": timestamp
        }
        
        try:
            self.db.execute(insert_query, params)
            return True, f'Added {ip_type} pattern: {ip_pattern}'
        except Exception as e:
            return False, f'Error adding pattern: {e}'
    
    def get_pattern_by_id(self, pattern_id):
        """Get pattern details by ip_id"""
        table = self._get_table("ip_filter")
        query = f"SELECT ip_id, ip_pattern, ip_type FROM {table} WHERE ip_id = :id"
        return self.db.fetch(query, {"id": pattern_id})
    
    def delete_pattern(self, pattern_id):
        """Delete an IP pattern by ip_id"""
        table = self._get_table("ip_filter")
        
        # Get pattern details first
        pattern = self.get_pattern_by_id(pattern_id)
        if not pattern:
            return False, 'Pattern not found'
        
        # Delete pattern
        delete_query = f"DELETE FROM {table} WHERE ip_id = :id"
        
        try:
            self.db.execute(delete_query, {"id": pattern_id})
            return True, f'Deleted {pattern.ip_type} pattern: {pattern.ip_pattern}'
        except Exception as e:
            return False, f'Error deleting pattern: {e}'
    
    def get_request_logs(self, ip_address=None, status=None, days=7):
        """Get IP request logs with optional filtering"""
        table = self._get_table("ip_request_log")
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Build query with filters
        query = f"""
        SELECT top 1000 log_id, ip_address, timestamp, status, request_path
        FROM {table}
        WHERE timestamp BETWEEN :start_date AND :end_date
        """
        
        params = {
            "start_date": start_date.strftime('%Y-%m-%d %H:%M:%S'),
            "end_date": end_date.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        if ip_address:
            query += " AND ip_address LIKE :ip_pattern"
            params["ip_pattern"] = f"%{ip_address}%"
        
        if status in [0,1]:
            query += " AND status = :status"
            params["status"] = status
        
        query += " ORDER BY timestamp DESC"
        
        return self.db.fetch_all(query, params)
    
    def get_top_blocked_ips(self, days=7):
        """Get top blocked IPs"""
        table = self._get_table("ip_request_log")
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        query = f"""
        SELECT top 20  ip_address, COUNT(*) as count
        FROM {table}
        WHERE timestamp BETWEEN :start_date AND :end_date
        AND status = 0
        GROUP BY ip_address
        ORDER BY count DESC
        """
        
        params = {
            "start_date": start_date.strftime('%Y-%m-%d %H:%M:%S'),
            "end_date": end_date.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return self.db.fetch_all(query, params)
    
    def get_top_allowed_ips(self, days=7):
        """Get top allowed IPs"""
        table = self._get_table("ip_request_log")
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        query = f"""
        SELECT top 20 ip_address, COUNT(*) as count
        FROM {table}
        WHERE timestamp BETWEEN :start_date AND :end_date
        AND status = 1
        GROUP BY ip_address
        ORDER BY count DESC
        """
        
        params = {
            "start_date": start_date.strftime('%Y-%m-%d %H:%M:%S'),
            "end_date": end_date.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return self.db.fetch_all(query, params)
    
    def get_daily_stats(self, days=7):
        """Get daily statistics"""
        table = self._get_table("ip_request_log")
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        query = f"""
        SELECT 
            CONVERT(date, timestamp) as day,
            status,
            COUNT(*) as count
        FROM {table}
        WHERE timestamp BETWEEN :start_date AND :end_date
        GROUP BY CONVERT(date, timestamp), status
        ORDER BY day
        """
        
        params = {
            "start_date": start_date.strftime('%Y-%m-%d %H:%M:%S'),
            "end_date": end_date.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return self.db.fetch_all(query, params)

    def log_ip_request(self, ip_address, status, request_path):
        """
        Log an IP request with status (allowed/blocked) and request path
        
        Args:
            ip_address (str): The IP address making the request
            status (str): 1 or 0
            request_path (str): The requested URL path
        
        Returns:
            tuple: (success, message)
        """
        table = self._get_table("ip_request_log")
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        insert_query = f"""
        INSERT INTO {table}
        (ip_address, timestamp, status, request_path)
        VALUES (:ip_address, :timestamp, :status, :request_path)
        """
        
        params = {
            "ip_address": ip_address,
            "timestamp": timestamp,
            "status": status,
            "request_path": request_path
        }
        
        try:
            self.db.execute(insert_query, params)
            return True, f'Logged {status} request from {ip_address}'
        except Exception as e:
            return False, f'Error logging request: {e}'        