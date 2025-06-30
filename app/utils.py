import json
import uuid
import base64
from datetime import datetime, date, timedelta
from decimal import Decimal
from flask import Response
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy.orm.state import InstanceState
from sqlalchemy.sql.sqltypes import Enum

class SQLAlchemyEncoder(json.JSONEncoder):
    def default(self, obj):
        # SQLAlchemy model instances
        if isinstance(obj.__class__, DeclarativeMeta):
            return obj.to_dict()
        
        # Date and time types
        elif isinstance(obj, (datetime, date)):
            return obj.isoformat()
        
        # UUID type
        elif isinstance(obj, uuid.UUID):
            return str(obj)
        
        # Decimal and Numeric types
        elif isinstance(obj, Decimal):
            return str(obj)
        
        # Timedelta (Interval type)
        elif isinstance(obj, timedelta):
            # Convert to ISO 8601 duration format
            total_seconds = int(obj.total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            return f"PT{hours}H{minutes}M{seconds}S"
        
        # Binary data
        elif isinstance(obj, (bytes, bytearray)):
            return base64.b64encode(obj).decode('utf-8')
        
        # SQLAlchemy Enum type
        elif hasattr(obj, 'name') and hasattr(obj, 'value') and isinstance(obj.__class__.__name__, str) and 'Enum' in obj.__class__.__name__:
            return obj.value
        
        # SQLAlchemy InstanceState (internal state object)
        elif isinstance(obj, InstanceState):
            return None  # Skip internal SQLAlchemy state
        
        # Set type (common in many-to-many relationships)
        elif isinstance(obj, set):
            return list(obj)
        
        # For any other type, try string representation
        try:
            return str(obj)
        except Exception:
            # If all else fails, use the parent class default
            # which will raise TypeError for truly unserializable objects
            return super().default(obj)
        

        
def jsonify(*args, **kwargs):
    """Drop-in replacement for Flask's jsonify that handles SQLAlchemy objects"""
    if args:
        data = args[0]
    else:
        data = kwargs
    
    return Response(
        json.dumps(data, cls=SQLAlchemyEncoder, indent=2),
        mimetype='application/json'
    )