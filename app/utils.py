import json
import uuid
from datetime import datetime, date
from flask import Response
from sqlalchemy.ext.declarative import DeclarativeMeta

class SQLAlchemyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj.__class__, DeclarativeMeta):
            return obj.to_dict()
        elif isinstance(obj, (datetime, date)):
            return obj.isoformat()
        elif isinstance(obj, uuid.UUID):
            return str(obj)
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