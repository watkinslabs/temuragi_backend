# app/models.py
"""
Clean model access using the register_db discovery system
Usage: from app.models import get_model, Theme, PageTemplate
"""

# Import the functions from the register system
from .register_db import get_model, list_models, get_all_models, _model_registry

# Make functions available directly
__all__ = ['get_model', 'list_models', 'get_all_models']

# Dynamic attribute access for clean imports
def __getattr__(name):
    """
    Allow direct imports like: from app.models import Theme
    Falls back to registry lookup if not found as regular attribute
    """
    # Check if it's in the global registry
    if name in _model_registry:
        return _model_registry[name]
    
    # If not found, give helpful error
    available = [k for k in _model_registry.keys() if not k.islower()]  # Skip table aliases
    raise AttributeError(f"Model '{name}' not found in registry. Available models: {available}")