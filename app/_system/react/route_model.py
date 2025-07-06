import hashlib
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, func, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship, validates
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
import json

from app.base.model import BaseModel


class RouteMapping(BaseModel):
    """Map routes to components"""
    __tablename__ = 'route_mappings'
    __depends_on__ = ['ComponentBundle']
    
    # Route information
    path = Column(String(500), nullable=False, unique=True)  # /v2/reports/:id
    name = Column(String(255), nullable=False)
    
    # Component mapping
    component_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey('component_bundles.id', ondelete='CASCADE'),
        nullable=False
    )
    
    # Route-specific configuration
    props = Column(JSONB, default=dict)  # Props passed to component
    config = Column(JSONB, default=dict)  # Additional config
    
    # Access control
    requires_auth = Column(Boolean, default=True)
    required_permissions = Column(JSONB, default=list)
    required_roles = Column(JSONB, default=list)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # SEO
    title = Column(String(255))
    description = Column(Text)
    meta_tags = Column(JSONB, default=dict)
    
    # Relationships
    component = relationship("ComponentBundle", back_populates="route_mappings")
    
    # Indexes
    __table_args__ = (
        Index('idx_route_path', 'path'),
        Index('idx_route_active', 'is_active'),
    )
    
    def __repr__(self):
        return f"<RouteMapping {self.path} -> {self.component.name}>"
    
    def matches(self, request_path):
        """Check if this route matches a request path"""
        import re
        
        # Convert route pattern to regex
        # /reports/:id -> /reports/([^/]+)
        pattern = re.sub(r':([^/]+)', r'(?P<\1>[^/]+)', self.path)
        pattern = '^' + pattern + '$'
        
        match = re.match(pattern, request_path)
        if match:
            return True, match.groupdict()
        return False, {}
    
    def to_response(self):
        """Convert to response format for frontend"""
        return {
            'path': self.path,
            'component_name': self.component.name,
            'component_version': self.component.version,
            'bundle_url': self.component.get_bundle_url(),
            'props': {**self.component.default_props, **self.props},
            'config': self.config,
            'title': self.title,
            'description': self.description,
            'meta_tags': self.meta_tags
        }