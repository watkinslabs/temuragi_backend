# Miner API Documentation

The Miner class is a unified data API handler that provides a single endpoint (`/api/data`) for all CRUD operations across all models in the application. It includes RBAC (Role-Based Access Control), audit logging, and support for specialized data handlers.

## Overview

- **Single Endpoint**: All operations go through `POST /api/data`
- **Token Authentication**: Requires Bearer token in Authorization header
- **Unified Response Format**: Consistent JSON responses across all operations
- **Automatic RBAC**: Permission checking based on operation and model
- **Audit Trail**: All operations are logged automatically

## Authentication

All requests require authentication:

```http
POST /api/data
Content-Type: application/json
Authorization: Bearer YOUR_TOKEN_HERE
```

## Core Operations

### 1. READ - Get Single Record

Fetch a single record by any column value.

```json
{
  "model": "User",
  "operation": "read",
  "filter_column": "email",
  "filter_value": "user@example.com"
}
```

**Backward compatible format (by ID):**
```json
{
  "model": "User",
  "operation": "read",
  "id": "123e4567-e89b-12d3-a456-426614174000"
}
```

**Options:**
- `slim`: (boolean) Return data as array instead of object

### 2. LIST - Get Multiple Records

Retrieve multiple records with filtering, sorting, pagination, and search.

```json
{
  "model": "User",
  "operation": "list",
  "start": 0,
  "length": 10,
  "filters": {
    "department": "Engineering",
    "is_verified": true
  },
  "order": [{"column": 0, "dir": "desc"}],
  "columns": [{"name": "name"}, {"name": "email"}, {"name": "created_at"}]
}
```

**With search across multiple fields:**
```json
{
  "model": "User",
  "operation": "list",
  "search": "john",
  "searchable_columns": ["name", "email", "username"],
  "start": 0,
  "length": 20
}
```

**Parameters:**
- `start`: Starting record (for pagination)
- `length`: Number of records to return (0 = all remaining)
- `search`: Search term to find across searchable columns
- `searchable_columns`: Array of column names to search in
- `filters`: Object with field-level filters (see Filter Operators below)
- `order`: Array of sort orders (DataTables format)
- `columns`: Array of column definitions (DataTables format)
- `include_inactive`: Include soft-deleted records (default: false)
- `return_columns`: Array of column names to return (limits response data)
- `slim`: Return data as arrays instead of objects

### 3. CREATE - Add New Record

Create a new record with the provided data.

```json
{
  "model": "User",
  "operation": "create",
  "data": {
    "name": "John Doe",
    "email": "john.doe@example.com",
    "department": "Engineering"
  }
}
```

**Note:** 
- The `is_active` field is automatically set by the model's default
- Primary keys (usually `id`) are auto-generated
- Created/updated timestamps are set automatically

### 4. UPDATE - Modify Existing Record

Update an existing record's fields.

```json
{
  "model": "User",
  "operation": "update",
  "filter_column": "email",
  "filter_value": "john.doe@example.com",
  "data": {
    "department": "Management",
    "title": "Engineering Manager"
  }
}
```

**Backward compatible format (by ID):**
```json
{
  "model": "User",
  "operation": "update",
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "data": {
    "department": "Management"
  }
}
```

**Notes:**
- Readonly fields are silently ignored with a warning in response
- `is_active` cannot be updated through the API
- Timestamps like `created_at` are readonly

### 5. DELETE - Remove Record

Delete (soft or hard) a record.

```json
{
  "model": "User",
  "operation": "delete",
  "filter_column": "email",
  "filter_value": "john.doe@example.com",
  "hard_delete": false
}
```

**Parameters:**
- `hard_delete`: If true, permanently deletes. If false, soft deletes (sets is_active=false)

### 6. COUNT - Count Records

Get count of records matching filters.

```json
{
  "model": "User",
  "operation": "count",
  "filters": {
    "department": "Engineering",
    "is_verified": true
  },
  "include_inactive": false
}
```

### 7. METADATA - Get Model Structure

Get detailed information about a model's columns and relationships.

```json
{
  "model": "User",
  "operation": "metadata"
}
```

Returns column types, relationships, indexes, and more.

### 8. FORM_METADATA - Get Form Generation Info

Get rich metadata optimized for form generation, including validation rules and display configuration.

```json
{
  "model": "User",
  "operation": "form_metadata"
}
```

## Filter Operators

When using the `filters` parameter in LIST or COUNT operations:

### Simple Filter (Exact Match)
```json
"filters": {
  "department": "Engineering"
}
```

### Complex Filters with Operators
```json
"filters": {
  "salary": {
    "operator": "gte",
    "value": 50000
  },
  "name": {
    "operator": "ilike",
    "value": "john"
  },
  "department": {
    "operator": "in",
    "value": ["Engineering", "IT", "DevOps"]
  }
}
```

**Available Operators:**
- `eq`: Equal (default)
- `ne`: Not equal
- `gt`: Greater than
- `gte`: Greater than or equal
- `lt`: Less than
- `lte`: Less than or equal
- `like`: Pattern match (case-sensitive)
- `ilike`: Pattern match (case-insensitive) - wildcards added automatically
- `in`: Value in list
- `not_in`: Value not in list
- `is_null`: Is null (value should be true/false)

## Search Behavior

When using the `search` parameter:

1. **Automatic Field Detection**: If `searchable_columns` not provided, Miner auto-detects searchable fields:
   - Text fields (VARCHAR, TEXT) are searched
   - Numeric fields searched only if search term is numeric
   - Date fields searched only if search term looks like a date
   - Boolean fields are never searched
   - UUID fields searched only if search term is valid UUID

2. **Search is case-insensitive** using ILIKE

3. **Partial matching** is automatic (no need to add wildcards)

## Response Formats

### Success Response
```json
{
  "success": true,
  "data": { ... },  // For single record operations
  "data": [ ... ],  // For list operations
  "message": "User updated successfully"
}
```

### List Response (DataTables Compatible)
```json
{
  "success": true,
  "draw": 1,
  "recordsTotal": 1000,
  "recordsFiltered": 23,
  "data": [
    {"id": "...", "name": "...", "email": "..."},
    ...
  ]
}
```

### Error Response
```json
{
  "success": false,
  "error": "Record not found",
  "error_type": "NotFoundError",
  "details": {}
}
```

## Batch Operations

Process multiple operations in a single request:

```json
{
  "batch": true,
  "operations": [
    {
      "model_name": "User",
      "operation": "create",
      "data": {"name": "User 1", "email": "user1@example.com"}
    },
    {
      "model_name": "User",
      "operation": "update",
      "data": {"id": "123", "name": "Updated Name"}
    }
  ]
}
```

## Special Features

### 1. Slim Mode
Returns data as arrays instead of objects (smaller payload):

```json
{
  "model": "User",
  "operation": "list",
  "slim": true
}
```

Response includes metadata about column order.

### 2. Data Brokers
If a model has a registered data handler, operations can be delegated to specialized handlers:

```python
# In your app initialization
miner.register_data_handler('PurchaseOrder', PurchaseOrderHandler)
```

### 3. Relationship Filters
Filter by related model fields:

```json
{
  "model": "User",
  "operation": "list",
  "filters": {
    "department": "Engineering"  // If department is a relationship, filters by department.name
  }
}
```

## Permission Model

Permissions follow the pattern: `api:modelname:action`

Examples:
- `api:user:read`
- `api:user:create`
- `api:user:update`
- `api:user:delete`

## Common Usage Examples

### Search for users with "max" in name
```json
{
  "model": "User",
  "operation": "list",
  "search": "max",
  "searchable_columns": ["name", "email"],
  "start": 0,
  "length": 10
}
```

### Get active users in Engineering, sorted by name
```json
{
  "model": "User",
  "operation": "list",
  "filters": {
    "department": "Engineering"
  },
  "order": [{"column": 0, "dir": "asc"}],
  "columns": [{"name": "name"}],
  "include_inactive": false
}
```

### Update user by email
```json
{
  "model": "User",
  "operation": "update",
  "filter_column": "email",
  "filter_value": "user@example.com",
  "data": {
    "phone": "555-1234"
  }
}
```