# app/register/classes.py
"""
Class registry with auto-loading based on dependency resolution
This would replace or extend your existing register/classes.py
"""

import os
import logging
from typing import Dict, Any, Optional, List
from ..config import config

# The global class registry
_class_registry: Dict[str, Any] = {}
_model_registry: Dict[str, Any] = {}

# Configure logger for this module
logger = logging.getLogger(__name__)

# Import the auto-loader
from ..autoloader import auto_load_classes


def register_classes():
    """Initialize the registry with auto-loaded classes"""
    if not _class_registry:  # Only load once
        logger.info("Starting class registry initialization", extra={
            "event": "registry_init_start",
            "base_dir": config.base_dir,
            "scan_paths": config.scan_paths
        })
        
        try:
            # Auto-load all classes from multiple directories
            patterns = ["*_class.py", "*_service.py", "*_model.py"]
            
            logger.info("Auto-loading classes", extra={
                "event": "auto_load_start",
                "patterns": patterns,
                "base_directories": config.scan_paths
            })
            
            auto_load_classes(
                _class_registry,
                base_directories=config.scan_paths,
                patterns=patterns,
                base_dir=config.base_dir
            )
            
            # Log successful class loading
            logger.info("Classes loaded successfully", extra={
                "event": "classes_loaded",
                "total_classes": len(_class_registry),
                "class_names": list(_class_registry.keys())
            })
            
            # Everything is in the class registry, now add the models to their own registry
            model_count = 0
            for name, class_obj in _class_registry.items():
                if hasattr(class_obj, '__tablename__'):
                    _model_registry[name] = class_obj
                    model_count += 1
                    logger.debug("Model registered", extra={
                        "event": "model_registered",
                        "model_name": name,
                        "table_name": getattr(class_obj, '__tablename__', None)
                    })
            
            logger.info("Model registry populated", extra={
                "event": "models_registered",
                "total_models": model_count,
                "model_names": list(_model_registry.keys())
            })
                        
        except Exception as e:
            logger.error("Failed to auto-load classes", extra={
                "event": "auto_load_failed",
                "error_type": type(e).__name__,
                "error_message": str(e),
                "scan_paths": config.scan_paths,
                "base_dir": config.base_dir
            }, exc_info=True)
            raise


def get_model(name: str) -> Optional[Any]:
    """
    Get a class from the registry by name

    Args:
        name: The class name to retrieve

    Returns:
        The class object or None if not found
    """
    model = _model_registry.get(name)
    if model is None:
        logger.warning("Model not found", extra={
            "event": "model_not_found",
            "model_name": name,
            "available_models": list(_model_registry.keys())
        })
    else:
        logger.debug("Model retrieved", extra={
            "event": "model_retrieved",
            "model_name": name
        })
    return model


def get_class(name: str) -> Optional[Any]:
    """
    Get a class from the registry by name

    Args:
        name: The class name to retrieve

    Returns:
        The class object or None if not found
    """
    class_obj = _class_registry.get(name)
    if class_obj is None:
        logger.warning("Class not found", extra={
            "event": "class_not_found",
            "class_name": name
        })
    else:
        logger.debug("Class retrieved", extra={
            "event": "class_retrieved",
            "class_name": name
        })
    return class_obj


def list_classes() -> List[str]:
    """
    List all registered class names

    Returns:
        List of class names in the registry
    """
    class_list = list(_class_registry.keys())
    logger.debug("Class list retrieved", extra={
        "event": "class_list_retrieved",
        "count": len(class_list)
    })
    return class_list


def get_all_classes() -> Dict[str, Any]:
    """
    Get all registered classes

    Returns:
        Dictionary of all registered classes
    """
    logger.debug("All classes retrieved", extra={
        "event": "all_classes_retrieved",
        "count": len(_class_registry)
    })
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
        logger.error("Class registration failed - already exists", extra={
            "event": "class_registration_failed",
            "class_name": name,
            "override": override
        })
        raise ValueError(f"Class '{name}' already registered")
    
    # models get added to both
    if hasattr(class_obj, '__tablename__'):
        _model_registry[name] = class_obj
        logger.info("Model registered manually", extra={
            "event": "model_registered_manual",
            "model_name": name,
            "table_name": getattr(class_obj, '__tablename__', None),
            "override": override
        })
    
    _class_registry[name] = class_obj
    logger.info("Class registered manually", extra={
        "event": "class_registered_manual",
        "class_name": name,
        "override": override
    })


# Export the registry for direct access if needed
__all__ = ['get_class', 'list_classes', 'get_all_classes', 'register_class', '_class_registry']