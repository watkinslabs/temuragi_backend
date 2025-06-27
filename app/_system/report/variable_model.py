import re
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, func, ForeignKey, Index, UniqueConstraint, event
from sqlalchemy.orm import relationship, validates
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB

from app.base.model import BaseModel


class ReportVariable(BaseModel):
    """Model for report variable/parameter definitions"""
    __tablename__ = 'report_variables'
    __depends_on__ = ['Report', 'VariableType', 'DataType']
    
    report_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey('reports.id', ondelete='CASCADE'),
        nullable=False
    )
    name = Column(String(255), nullable=False)  # Variable name in query {var_name}
    display_name = Column(String(255))
    
    # Link to data type
    variable_type_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey('variable_types.id', ondelete='RESTRICT'),
        nullable=False
    )
    
    # Input configuration
    default_value = Column(Text)
    placeholder = Column(String(255))
    help_text = Column(Text)
    is_required = Column(Boolean, default=False)
    is_hidden = Column(Boolean, default=False)  # For system variables
    
    # Validation stored in JSON (similar to CrudDef variables)
    limits = Column(JSONB, nullable=True)  # min, max, regex, options, etc.
    
    # Dependencies
    depends_on = Column(String(255))  # Another variable name this depends on
    dependency_condition = Column(JSONB)  # Condition for showing/hiding
    
    # Order
    order_index = Column(Integer, default=0)
    
    # Relationships
    report = relationship("Report", back_populates="variables")
    variable_type = relationship("VariableType", foreign_keys=[variable_type_id])
    
    # Indexes and constraints
    __table_args__ = (
        Index('idx_report_variables', 'report_id', 'order_index'),
        UniqueConstraint('report_id', 'name', name='uq_report_variable_name'),
    )
    
    def __init__(self, **kwargs):
        if 'limits' not in kwargs or kwargs['limits'] is None:
            kwargs['limits'] = {}
        super(ReportVariable, self).__init__(**kwargs)
    
    def __repr__(self):
        return f"<ReportVariable {self.name} for report {self.report_id}>"


