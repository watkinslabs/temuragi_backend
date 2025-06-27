import json
from sqlalchemy import Column, String, Boolean, Text, func, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.base.model import BaseModel

class Module(BaseModel):
    """Model for storing module configurations"""
    __tablename__ = 'modules'

    module_name = Column(String(100), nullable=False, unique=True, index=True)
    config_data = Column(Text, nullable=True)  # JSON blob for configuration

    # Relationships for templates and pages owned by this module
    templates = relationship("Template", back_populates="module", cascade="all, delete-orphan")
    pages = relationship("Page", back_populates="module", cascade="all, delete-orphan")

    def __repr__(self):
        """String representation of the module config"""
        return f"<ModuleConfig {self.module_name} (Active: {self.is_active})>"

    def get_config_dict(self):
        """Convert config_data JSON string to Python dictionary"""
        if not self.config_data:
            return {}
        try:
            return json.loads(self.config_data)
        except json.JSONDecodeError:
            return {}

    def set_config_dict(self, config_dict):
        """Convert Python dictionary to JSON string and store in config_data"""
        self.config_data = json.dumps(config_dict)

    @classmethod
    def get_all_configs(cls, db_session):
        """Get all module configurations"""
        return db_session.query(cls).order_by(cls.module_name).all()

    @classmethod
    def get_active_configs(cls, db_session):
        """Get all active module configurations"""
        return db_session.query(cls).filter(cls.is_active == True).order_by(cls.module_name).all()

    @classmethod
    def get_config_by_name(cls, db_session, module_name):
        """Get a module configuration by name"""
        return db_session.query(cls).filter(cls.module_name == module_name).first()

    @classmethod
    def get_config_by_id(cls, db_session, config_id):
        """Get a module configuration by ID"""
        return db_session.query(cls).filter(cls.id == config_id).first()

    @classmethod
    def add_or_update_config(cls, db_session, module_name, config_dict=None, is_active=True):
        """Add a new module configuration or update existing one"""
        existing = cls.get_config_by_name(db_session, module_name)

        if existing:
            # Update existing config
            existing.is_active = is_active
            if config_dict is not None:
                existing.set_config_dict(config_dict)
        else:
            # Create new config
            new_config = cls(
                module_name=module_name,
                is_active=is_active
            )
            if config_dict is not None:
                new_config.set_config_dict(config_dict)
            db_session.add(new_config)

        try:
            db_session.commit()
            return True, f"Configuration for {module_name} saved successfully"
        except Exception as e:
            db_session.rollback()
            return False, f"Error saving configuration: {str(e)}"

    @classmethod
    def activate_config(cls, db_session, config_id):
        """Activate a module configuration"""
        config = cls.get_config_by_id(db_session, config_id)
        if not config:
            return False, "Configuration not found"

        try:
            config.is_active = True
            db_session.commit()
            return True, f"{config.module_name} configuration activated"
        except Exception as e:
            db_session.rollback()
            return False, f"Error activating configuration: {str(e)}"

    @classmethod
    def deactivate_config(cls, db_session, config_id):
        """Deactivate a module configuration"""
        config = cls.get_config_by_id(db_session, config_id)
        if not config:
            return False, "Configuration not found"

        try:
            config.is_active = False
            db_session.commit()
            return True, f"{config.module_name} configuration deactivated"
        except Exception as e:
            db_session.rollback()
            return False, f"Error deactivating configuration: {str(e)}"

    @classmethod
    def delete_config(cls, db_session, config_id):
        """Delete a module configuration"""
        config = cls.get_config_by_id(db_session, config_id)
        if not config:
            return False, "Configuration not found"

        try:
            db_session.delete(config)
            db_session.commit()
            return True, f"{config.module_name} configuration deleted"
        except Exception as e:
            db_session.rollback()
            return False, f"Error deleting configuration: {str(e)}"
