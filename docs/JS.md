# JavaScript Application Build Documentation

## Overview

This JavaScript application follows a modular, class-based architecture with a centralized registry system. All components self-register to a global `window.app` namespace for easy access and coordination.

## Core Architecture

### 1. Global Namespace (`app_core.js`)

The foundation of the application is the `window.app` object which serves as:
- A central registry for all managers/components
- A configuration store
- An access point for cross-component communication

```javascript
window.app = {
    managers: {},
    config: {},
    register: function(name, instance) {
        // Components self-register here
    }
}
```

### 2. Component Structure

All components follow a consistent pattern:

```javascript
class ComponentName {
    constructor(options = {}) {
        // Initialize properties
        this.property = options.property || default_value;
        
        // Self-register to window.app
        window.app.register('component_name', this);
        
        // Initialize
        this.init();
    }
    
    async init() {
        // Setup logic
    }
}
```

## Key Components

### 1. **AppInitializer** (`app.js`)
- Entry point for the application
- Initializes all core managers in correct order
- Sets up cross-component references
- Handles authentication flow
- Configures HTMX integration

### 2. **ApiManager** (`api_manager.js`)
- Centralized HTTP request handling
- Automatic authentication header injection
- Request/response/error interceptors
- CSRF token management

### 3. **AuthManager** (`auth_manager.js`)
- Token validation and refresh
- 401 response handling
- Login/logout flow
- HTMX request authentication

### 4. **ConnectionMonitor** (`connection_manager.js`)
- Network connectivity monitoring
- Automatic reconnection attempts
- Visual offline indicator
- Health endpoint checking

### 5. **DataForm** (`data_form.js`)
- Generic form handling for CRUD operations
- Foreign key select population
- Field validation
- Loading state management
- Success/error handling

### 6. **ReportBuilder** (`report.js`)
- Complex multi-tab form interface
- SQL query editor integration (CodeMirror)
- Dynamic column/variable management
- Preview functionality
- Metadata extraction

## Coding Patterns

### 1. **Snake Case Naming**
All variables, functions, and properties use snake_case:
```javascript
this.health_endpoint = options.health_endpoint;
this.check_interval = options.check_interval;
```

### 2. **Self-Registration Pattern**
Components register themselves during construction:
```javascript
constructor() {
    window.app.register('api', this);
}
```

### 3. **Async/Await Usage**
All async operations use async/await pattern:
```javascript
async load_connections() {
    try {
        const result = await window.app.api.post(url, data);
        // Handle result
    } catch (error) {
        // Handle error
    }
}
```

### 4. **Event Delegation**
For dynamically created elements:
```javascript
$(document).on('click', '.button-class', function() {
    // Handle click
});
```

### 5. **Configuration Pattern**
Options passed through constructor with defaults:
```javascript
constructor(options = {}) {
    this.options = {
        show_success_toast: true,
        show_error_toast: true,
        ...options
    };
}
```

## Data Flow

### 1. **API Communication**
```
Component → ApiManager → Server
    ↓           ↓           ↓
Component ← ApiManager ← Response
```

### 2. **Authentication Flow**
```
AppInitializer → AuthManager → Check Tokens
                      ↓
                 Validate/Refresh
                      ↓
              Continue or Redirect
```

### 3. **Form Submission**
```
Form Event → DataForm → Validate → ApiManager → Server
                            ↓
                     Handle Response
                            ↓
                    Show Notification
```

## UI Integration

### 1. **Bootstrap 5**
- Modal dialogs
- Toast notifications
- Form styling
- Grid system

### 2. **jQuery**
- DOM manipulation
- Event handling
- AJAX (through ApiManager)
- UI components (sortable)

### 3. **HTMX**
- Partial page updates
- Server-driven UI
- Automatic loading indicators

### 4. **CodeMirror**
- SQL query editing
- Syntax highlighting
- Auto-formatting

## State Management

### 1. **Component State**
Each component maintains its own state:
```javascript
this.loading_states = {
    form: false,
    fk_selects: new Set(),
    initial_data: false
};
```

### 2. **Shared State**
Through window.app registry:
```javascript
window.app.token_manager.get_tokens();
window.app.config.api_url;
```

### 3. **Data Persistence**
- No localStorage/sessionStorage usage
- All state in memory
- Server as source of truth

## Error Handling

### 1. **Try-Catch Blocks**
```javascript
try {
    const result = await window.app.api.post(url, data);
    if (result.success) {
        // Handle success
    } else {
        throw new Error(result.error);
    }
} catch (error) {
    this.show_error(error.message);
}
```

### 2. **Toast Notifications**
```javascript
window.showToast(message, type); // type: 'success', 'error', 'info', 'warning'
```

### 3. **Loading States**
```javascript
this.show_loading(true);
try {
    // Operation
} finally {
    this.show_loading(false);
}
```

## Build Process

### 1. **File Loading Order**
1. `app_core.js` - Creates window.app namespace
2. `api_manager.js` - API communication
3. `auth_manager.js` - Authentication
4. `connection_manager.js` - Network monitoring
5. `data_form.js` - Form handling
6. `app.js` - Initialization
7. Component-specific files (e.g., `report.js`)

### 2. **Initialization Sequence**
```javascript
// In app.js
async init() {
    // Create core managers
    new TokenManager();
    new ApiManager();
    new AuthManager();
    new ConnectionMonitor();
    
    // Set cross-references
    window.app.connection_monitor.set_auth_manager(window.app.auth_manager);
    
    // Check auth and start
    await window.app.auth_manager.init();
}
```

### 3. **Development Guidelines**

**DO:**
- Use snake_case for all identifiers
- Self-register components to window.app
- Handle loading states properly
- Use async/await for async operations
- Validate before API calls
- Show user feedback (toasts/loading)

**DON'T:**
- Use localStorage/sessionStorage
- Spread objects unnecessarily
- Rename classes without updating tests
- Remove code without approval
- Assume defaults

## Testing Considerations

### 1. **Component Access**
All components accessible via:
```javascript
window.app.component_name
window.reportBuilder // For specific instances
```

### 2. **State Inspection**
```javascript
window.app.auth_manager.validation_interval
window.app.connection_monitor.is_online
```

### 3. **Manual Testing**
- Check network offline behavior
- Test form validation
- Verify token refresh
- Test loading states

## Extending the Application

### 1. **Adding New Components**
```javascript
class NewComponent {
    constructor(options = {}) {
        // Properties
        this.option = options.option;
        
        // Register
        window.app.register('new_component', this);
        
        // Initialize
        this.init();
    }
    
    async init() {
        // Setup code
    }
}
```

### 2. **Adding API Interceptors**
```javascript
window.app.api.on_request(async (url, options) => {
    // Modify request
    return options;
});

window.app.api.on_error(async (error) => {
    // Handle error
    if (handled) return response;
});
```

### 3. **Custom Form Actions**
```javascript
class CustomForm extends DataForm {
    setup_field_watchers() {
        // Add custom field interactions
    }
    
    handle_success(result, operation) {
        super.handle_success(result, operation);
        // Custom success handling
    }
}
```

## Performance Considerations

1. **Lazy Loading**: Components only load when needed
2. **Debouncing**: For frequent operations (search, validation)
3. **Caching**: Through server-side cache headers
4. **Minimal DOM Updates**: Using HTMX for partial updates
5. **Efficient Selectors**: Cache jQuery selections when possible

## Security Notes

1. **CSRF Protection**: Automatic token inclusion
2. **XSS Prevention**: Proper escaping in templates
3. **Authentication**: JWT-based with refresh tokens
4. **Input Validation**: Client and server-side
5. **Secure Headers**: Set by server