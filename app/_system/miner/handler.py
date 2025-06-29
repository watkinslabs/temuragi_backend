
class MinerError(Exception):
    """Custom exception for Miner operations"""
    __depends_on__ =[]

    def __init__(self, message, error_type="MinerError", status_code=400, details=None):
        self.message = message
        self.error_type = error_type
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class MinerPermissionError(MinerError):
    """Permission denied error"""
    __depends_on__ =[]

    def __init__(self, message, permission_required=None):
        super().__init__(message, "PermissionError", 403, {'permission_required': permission_required})

class DataBrokerError(MinerError):
    """Data broker specific errors"""
    __depends_on__ = []

    def __init__(self, message, handler_class=None, operation=None):
        details = {}
        if handler_class:
            details['handler_class'] = handler_class
        if operation:
            details['operation'] = operation
        super().__init__(message, "DataBrokerError", 400, details)

class BaseDataHandler:
    """Base class for specialized data handlers"""
    
    def __init__(self, session, auth_context, logger=None):
        self.session = session
        self.auth_context = auth_context
        self.logger = logger
        self.user_id = auth_context.get('user_id') if auth_context else None
    
    def handle_create(self, data):
        """Override in subclass"""
        raise NotImplementedError("Subclass must implement handle_create")
    
    def handle_update(self, data):
        """Override in subclass"""
        raise NotImplementedError("Subclass must implement handle_update")
    
    def handle_metadata(self, data):
        """Override in subclass"""
        raise NotImplementedError("Subclass must implement handle_metadata")
    
    def handle_process(self, data):
        """Override in subclass for custom processing"""
        raise NotImplementedError("Subclass must implement handle_process")
    
    def handle_batch_create(self, data_list):
        """Handle batch creation"""
        results = []
        for data in data_list:
            results.append(self.handle_create(data))
        return results
    
    def handle_validate(self, data):
        """Validate data without saving"""
        raise NotImplementedError("Subclass must implement handle_validate")
