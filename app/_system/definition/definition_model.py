import uuid
import datetime
from sqlalchemy import Column, String, Text, Boolean, JSON, DateTime, event, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import object_session, relationship
from sqlalchemy.ext.declarative import declared_attr

from app._system._core.base import BaseModel

class CrudDef(BaseModel):
    __tablename__ = 'crud_defs'

    name = Column(String, unique=True, nullable=False)
    display = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    query_select = Column(Text, nullable=False)
    query_insert = Column(Text, nullable=False)
    query_update = Column(Text, nullable=False)
    query_delete = Column(Text, nullable=False)
    columns = Column(JSONB, nullable=True)
    variables = Column(JSONB, nullable=True)
    options = Column(JSONB, nullable=True)
    connection_uuid = Column(
        PG_UUID(as_uuid=True),
        ForeignKey('connections.uuid'),
        nullable=True
    )    
    

    
    def __init__(self, **kwargs):
        # Apply default values for JSON columns
        if 'columns' not in kwargs or kwargs['columns'] is None:
            kwargs['columns'] = {}
            
        if 'variables' not in kwargs or kwargs['variables'] is None:
            kwargs['variables'] = {}
            
        if 'options' not in kwargs or kwargs['options'] is None:
            kwargs['options'] = self.get_default_options()
        else:
            # Make sure options has the right structure
            self._ensure_options_structure(kwargs['options'])
            
        super(CrudDef, self).__init__(**kwargs)
    
    def get_default_options(self):
        """Return default options structure"""
        return {
            "results_limit": 0,
            "is_datatable": True,
            "datatable": {
                "is_live": False,
                "is_searchable": False, 
                "is_filterable": True,
                "is_exportable": False,
                "export_formats": "csv,xlsx"
            }
        }
    
    def _ensure_options_structure(self, options):
        """Ensure options has all required fields with default values"""
        if 'results_limit' not in options:
            options['results_limit'] = 0
            
        if 'is_datatable' not in options:
            options['is_datatable'] = True
            
        if 'datatable' not in options:
            options['datatable'] = {}
            
        dt_defaults = {
            'is_live': False,
            'is_searchable': False,
            'is_filterable': True,
            'is_exportable': False,
            'export_formats': 'csv,xlsx'
        }
        
        for key, value in dt_defaults.items():
            if key not in options['datatable']:
                options['datatable'][key] = value
        
        return options
    
    def get_default_column(self):
        """Return default column structure"""
        return {
            "display": "",
            "width": "",
            "order": 0,
            "type": "text",
            "description": ""
        }
    
    def get_default_variable(self):
        """Return default variable structure"""
        return {
            "display": "",
            "type": "text",
            "default": "",
            "limits": {},
            "order": 0  # Add order field with default value
        }
                
    def ensure_valid_structure(self):
        """Ensure the CRUD definition has valid structures for all fields"""
        # Apply defaults for JSON columns if they're None
        if self.columns is None:
            self.columns = {}
            
        if self.variables is None:
            self.variables = {}
            
        if self.options is None:
            self.options = self.get_default_options()
        else:
            self.options = self._ensure_options_structure(self.options)

# Setup SQLAlchemy event listeners to ensure defaults are set when loading from DB
@event.listens_for(CrudDef, 'load')
def receive_load(target, context):
    """Ensure all objects have proper defaults when loaded from database"""
    target.ensure_valid_structure()