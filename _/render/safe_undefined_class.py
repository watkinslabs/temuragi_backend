from jinja2 import Undefined
from markupsafe import Markup


class SafeUndefined(Undefined):
    """Custom undefined handler that returns safe fallback content"""
    
    def __str__(self):
        name = getattr(self, '_undefined_name', 'UNKNOWN')
        return Markup(f'<span class="undefined-var">[{name}]</span>')

    def __call__(self, *args, **kwargs):
        # Special handling for common functions to return useful content
        name = getattr(self, '_undefined_name', 'UNKNOWN')
        
        if 'get_flashed_messages' in str(name):
            # Return empty list to prevent unpacking errors
            with_categories = kwargs.get('with_categories', False) or (args and args[0])
            return [] if not with_categories else []
        
        if 'render_breadcrumbs' in str(name):
            return Markup('<nav><span class="undefined-function">[breadcrumbs not configured]</span></nav>')
        
        if 'render_' in str(name):
            return Markup(f'<div class="undefined-function">[{name} not available]</div>')
        
        # Generic function call
        return Markup(f'<span class="undefined-function">[{name}(...)]</span>')

    def __getattr__(self, name):
        current_name = getattr(self, '_undefined_name', 'UNKNOWN')
        return SafeUndefined(name=f"{current_name}.{name}")
    
    def __iter__(self):
        # Make undefined iterable to prevent template errors
        return iter([])
    
    def __len__(self):
        return 0
    
    def __getitem__(self, key):
        # Handle subscript access
        name = getattr(self, '_undefined_name', 'UNKNOWN')
        return SafeUndefined(name=f"{name}[{key}]")
    
    def __bool__(self):
        # Make undefined falsy
        return False