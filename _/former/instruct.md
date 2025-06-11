Enhanced Design Instructions with CRUD & Permissions
4. Add CRUD Service Layer Design
Create CRUD Service Architecture:

Build a service layer that handles CRUD operations with permission validation
Implement AWS-style permissions (e.g., page:create, page:read, page:update, page:delete)
Create metadata extraction for automatic AJAX endpoint generation
Design permission checking before any database operations

5. Permission System Design
AWS-Style Permission Format:

{resource}:{action} format (e.g., page:create, template:update)
Wildcard support (*:* for admin, page:* for all page operations)
Permission inheritance (view access = {resource}:read permission)
Resource-level permissions (per model/table permissions)

Form Permission Integration:

Hide Create button if user lacks {model}:create permission
Hide Edit button if user lacks {model}:update permission
Hide Delete button if user lacks {model}:delete permission
Show read-only forms if user only has {model}:read permission
Gray out/disable fields based on field-level permissions

6. AJAX Integration Design
Automatic Endpoint Generation:

Generate REST endpoints based on model metadata
Standard CRUD endpoints: GET /api/{model}, POST /api/{model}, PUT /api/{model}/{id}, DELETE /api/{model}/{id}
Relationship endpoints: GET /api/{model}/{id}/relationships
Bulk operations: POST /api/{model}/bulk, DELETE /api/{model}/bulk

Client-Side AJAX Architecture:

Auto-generate JavaScript for CRUD operations
Form submission via AJAX with validation feedback
Real-time field validation against server
Optimistic UI updates with rollback on failure
Loading states and progress indicators

7. Enhanced Form Generator Design
Permission-Aware Form Generation:

Accept user permission list as parameter
Conditionally render form elements based permissions
Add data-permission attributes to elements for JavaScript handling
Generate different form modes: create, edit, view-only

Metadata-Driven AJAX:

Extract API endpoints from model relationships
Generate JavaScript for dropdown population
Auto-wire foreign key selects with AJAX calls
Implement search/filter for large datasets

8. Security Integration Points
Server-Side Permission Validation:

Validate permissions on every API endpoint
Check permissions before database queries
Log permission violations for audit
Return appropriate HTTP status codes (403 Forbidden)

Client-Side Permission Handling:

Hide/show UI elements based on permissions
Disable form submission for insufficient permissions
Provide clear permission error messages
Graceful degradation for permission changes

9. Implementation Architecture
Service Layer Pattern:
FormGenerator → CRUDService → PermissionService → Database
                     ↓
               AJAX Endpoints ← JavaScript Client
Permission Flow:
User Login → Load Permissions → Generate Form → Check Permissions → Execute Action
AJAX Pattern:
Form Submit → Validate Client → AJAX Call → Server Validation → Database → Response → UI Update
10. Configuration Design
Model Configuration:

Define permission mappings per model
Configure field-level permissions
Set up relationship permission inheritance
Define custom validation rules per model

Endpoint Configuration:

Auto-register CRUD endpoints from models
Configure rate limiting per endpoint
Set up caching strategies
Define bulk operation limits