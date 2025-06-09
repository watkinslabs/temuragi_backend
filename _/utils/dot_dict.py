import json    
    
class DotDict(dict):
    """
    Dictionary subclass with attribute access and JSON serialization.
    Supports both dot notation and dictionary access styles.
    Supports equality testing and 'in' operator.
    Directly serializable by json.dumps()
    """

    def parse_json(self, key):
        """Parse a JSON string at the given key and replace it."""
        if key not in self:
            self[key] = []
            return
            
        json_string = self[key]
        if not json_string:
            self[key] = []
            return
            
        try:
            parsed = json.loads(json_string)
            
            # Convert to appropriate type
            if isinstance(parsed, list):
                self[key] = [DotDict(item) if isinstance(item, dict) else item for item in parsed]
            elif isinstance(parsed, dict):
                self[key] = DotDict(parsed)
            else:
                self[key] = parsed
        except:
            self[key] = []

    def __init__(self, *args, **kwargs):
        super(DotDict, self).__init__(*args, **kwargs)
        # Enable attribute access
        for key, value in self.items():
            if isinstance(value, dict) and not isinstance(value, DotDict):
                self[key] = DotDict(value)  # Recursively convert nested dicts
    
    def __getattr__(self, key):
        """Enable dot notation access"""
        try:
            return self[key]
        except KeyError:
            keys = ', '.join(self.keys())
            raise AttributeError(f"Attribute '{key}' not found. Available attributes: {keys}")
    
    def __setattr__(self, key, value):
        """Enable dot notation assignment"""
        self[key] = value
    
    def __delattr__(self, key):
        """Enable dot notation deletion"""
        try:
            del self[key]
        except KeyError:
            raise AttributeError(f"Attribute '{key}' not found")
    
    def get(self, key, default=None):
        """Get with default value"""
        return super(DotDict, self).get(key, default)
    
    def __eq__(self, other):
        """
        Enable equality testing with other DotDict objects
        and regular dictionaries
        """
        if isinstance(other, DotDict):
            return dict(self) == dict(other)
        elif isinstance(other, dict):
            return dict(self) == other
        return NotImplemented
    
    def __contains__(self, key):
        """Support 'in' operator"""
        return super(DotDict, self).__contains__(key)
    
    def copy(self):
        """Return a new DotDict with the same items"""
        return DotDict(dict.copy(self))
    
    def __repr__(self):
        """String representation that can be used for debugging"""
        return f"DotDict({dict.__repr__(self)})"