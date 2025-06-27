# app/models.py
"""
Clean model access using the register_db discovery system
Usage: from app.models import get_model, Theme, PageTemplate
"""

from .register.classes import get_model


__all__ = ['get_model']

# If you want to keep __getattr__ as a fallback for dynamic access:
def __getattr__(name):
    """
    Fallback for any classes that might not have been injected yet
    """
    # First try to get it from globals (in case it was injected after this module loaded)
    if name in globals():
        return globals()[name]
    
    # Try getting from register if available
    try:
        from .register.classes import _model_registry
        if name in _model_registry:
            # Also inject it for next time
            globals()[name] = _model_registry[name]
            return _model_registry[name]
    except:
        pass
    
    # Give a helpful error
    available = [k for k in dir() if not k.startswith('_') and k[0].isupper()]
    raise AttributeError(f"Model '{name}' not found. Available models: {available}")