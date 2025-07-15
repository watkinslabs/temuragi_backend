# app/register/classes.py
"""
Class registry with auto-loading based on dependency resolution
This would replace or extend your existing register/classes.py
"""

import os
from typing import Dict, Any, Optional, List
from ..config import config

# The global class registry
_class_registry: Dict[str, Any] = {}
_model_registry: Dict[str, Any] = {}


# Import the auto-loader
from ..autoloader import auto_load_classes


def register_classes():
    """Initialize the registry with auto-loaded classes"""
    if not _class_registry:  # Only load once
        try:
            # Auto-load all classes from multiple directories
            auto_load_classes(
                _class_registry,
                base_directories=config.scan_paths,
                patterns=[
                    "*_class.py",
                    "*_service.py",
                    "*_model.py",
                ],
                base_dir=config.base_dir
                )
            #everything is in the class registy, now add the models to their own registry
            for name, class_obj in _class_registry.items():
                if hasattr(class_obj, '__tablename__'):
                    _model_registry[name] = class_obj
        except Exception as e:
            print(f"Warning: Failed to auto-load classes: {e}")



def get_model(name: str) -> Optional[Any]:
    """
    Get a class from the registry by name

    Args:
        name: The class name to retrieve

    Returns:
        The class object or None if not found
    """
    model= _model_registry.get(name)
    if model==None:
        print(f"Model: {name} not found")
    return model


def get_class(name: str) -> Optional[Any]:
    """
    Get a class from the registry by name

    Args:
        name: The class name to retrieve

    Returns:
        The class object or None if not found
    """
    return _class_registry.get(name)


def list_classes() -> List[str]:
    """
    List all registered class names

    Returns:
        List of class names in the registry
    """
    return list(_class_registry.keys())


def get_all_classes() -> Dict[str, Any]:
    """
    Get all registered classes

    Returns:
        Dictionary of all registered classes
    """
    return _class_registry.copy()


def register_class(name: str, class_obj: Any, override: bool = False) -> None:
    """
    Manually register a class (useful for testing or dynamic registration)

    Args:
        name: The name to register the class under
        class_obj: The class object to register
        override: Whether to override existing registration

    Raises:
        ValueError: If class already registered and override is False
    """
    if name in _class_registry and not override:
        raise ValueError(f"Class '{name}' already registered")
    # models get added to both
    if hasattr(class_obj,'__tablename__') :
        _model_registry[name] = class_obj
    _class_registry[name] = class_obj


# Export the registry for direct access if needed
__all__ = ['get_class', 'list_classes', 'get_all_classes', 'register_class', '_class_registry']