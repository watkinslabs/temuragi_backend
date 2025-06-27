import uuid
import datetime
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.declarative import declared_attr

from app.base.model import BaseModel

class VariableType(BaseModel):
    __tablename__ = 'variable_types'
    __depends_on__ = []  

    name = Column(String, unique=True, nullable=False)
    display = Column(String, nullable=False)



    @classmethod
    def create_initial_data(cls, session):
        """Create initial variable types"""
        initial_types = [
            ('text', 'Text Input', True),
            ('number', 'Number Input', True),
            ('select', 'Select Dropdown', True),
            ('multiselect', 'Multi Select', True),
            ('checkbox', 'Checkbox', True),
            ('radio', 'Radio Buttons', True),
            ('date', 'Date Picker', True),
            ('datetime', 'DateTime Picker', True),
            ('hidden', 'Hidden Field', True),
            ('money', 'Money Input', True),
            # New types specifically useful for reports
            ('textarea', 'Text Area', True),
            ('daterange', 'Date Range Picker', True),
            ('timerange', 'Time Range Picker', True),
            ('slider', 'Slider', True),
            ('toggle', 'Toggle Switch', True),
            ('color', 'Color Picker', True),
            ('file', 'File Upload', True),
            ('tags', 'Tag Input', True),
            ('autocomplete', 'Autocomplete', True),
            ('cascading_select', 'Cascading Dropdown', True),
            ('user_select', 'User Selector', True),
            ('sql_editor', 'SQL Editor', True),
            ('json_editor', 'JSON Editor', True)
        ]
        
        for name, display, active in initial_types:
            existing = session.query(cls).filter_by(name=name).first()
            if not existing:
                var_type = cls(name=name, display=display, is_active=active)
                session.add(var_type)