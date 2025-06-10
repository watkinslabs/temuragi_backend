# app/classes.py
"""
Clean class access using the register_classes discovery system
Usage: from app.classes import get_class, TemplateRenderer, BlockProcessor
"""

# Import the functions from the register system
from .register.classes import get_class, list_classes, get_all_classes, _class_registry

# Make functions available directly
__all__ = ['get_class', 'list_classes', 'get_all_classes']

# Populate globals for static imports
for name, cls in _class_registry.items():
    if not name.islower():  # skip aliases
        globals()[name] = cls
        __all__.append(name)


# Dynamic attribute access for clean imports
def __getattr__(name):
    """
    Allow direct imports like: from app.classes import TemplateRenderer
    Falls back to registry lookup if not found as regular attribute
    """
    # Check if it's in the global registry
    if name in _class_registry:
        return _class_registry[name]
    
    # If not found, give helpful error
    available = [k for k in _class_registry.keys() if not k.islower()]  # Skip aliases
    raise AttributeError(f"Class '{name}' not found in registry. Available classes: {available}")