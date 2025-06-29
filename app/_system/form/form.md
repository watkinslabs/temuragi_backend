# Custom Actions CLI Usage Examples

## Basic Usage

### No Actions
To create a list without any actions:
```bash
# Using --no-actions flag
python form_cli.py report-datatable my-report --no-actions

# Or using --actions=none
python form_cli.py report-datatable my-report --actions=none

# Or using --actions=no
python form_cli.py report-datatable my-report --actions=no
```

### Default Actions
To use default actions (view, export):
```bash
python form_cli.py report-datatable my-report
```

### Simple Custom Actions
To specify simple action names:
```bash
# Just edit and delete
python form_cli.py report-datatable my-report --actions="edit,delete"

# Create, edit, and delete
python form_cli.py report-datatable my-report --actions="create,edit,delete"

# View and export
python form_cli.py report-datatable my-report --actions="view,export"
```

## Advanced Usage

### Custom Actions with URLs
To override URLs for specific actions:
```bash
# Custom edit URL
python form_cli.py report-datatable my-report --actions="edit:url=/custom/edit/{id},delete"

# Multiple custom URLs
python form_cli.py report-datatable my-report --actions="edit:url=/admin/edit/{id},delete:url=/admin/delete/{id}"

# With create action and custom URL
python form_cli.py report-datatable my-report --actions="create:url=/custom/create,edit,delete"
```

### Custom Actions with Icons
To specify custom icons:
```bash
# Custom icon for edit
python form_cli.py report-datatable my-report --actions="edit:icon=fa-pencil,delete"

# Multiple custom icons
python form_cli.py report-datatable my-report --actions="edit:icon=fa-pencil,delete:icon=fa-trash-alt,view:icon=fa-search"
```

### Custom Actions with Multiple Properties
Combine multiple properties using colon notation:
```bash
# Edit with custom URL and icon
python form_cli.py report-datatable my-report --actions="edit:url=/custom/edit:icon=fa-pencil,delete"

# Complex example with multiple actions
python form_cli.py report-datatable my-report --actions="create:url=/admin/create:icon=fa-plus-circle,edit:url=/admin/edit:icon=fa-edit,delete:url=/admin/delete:icon=fa-trash:class=btn-danger"
```

### Override Data URL
To override the data URL along with custom actions:
```bash
# Custom data URL with custom actions
python form_cli.py report-datatable my-report --data-url="/api/custom/data" --actions="edit,delete"

# No actions with custom data URL
python form_cli.py report-datatable my-report --data-url="/api/custom/data" --no-actions
```

## Action Properties Reference

The following properties can be set for each action:

- `url`: Custom URL for the action (e.g., `url=/custom/edit/{id}`)
- `icon`: Font Awesome icon class (e.g., `icon=fa-pencil`)
- `class`: Bootstrap button class (e.g., `class=btn-danger`)
- `label`: Custom label text (e.g., `label=Modify`)
- `method`: HTTP method (e.g., `method=POST`)
- `confirm`: Confirmation message (e.g., `confirm=Are you sure?`)

## Default Icons and Classes

The system provides default icons and classes for common action names:

| Action | Default Icon | Default Class |
|--------|-------------|---------------|
| view | fa-eye | btn-info |
| edit | fa-edit | btn-primary |
| delete | fa-trash | btn-danger |
| create | fa-plus | btn-success |
| copy | fa-copy | btn-secondary |
| duplicate | fa-clone | btn-secondary |
| export | fa-download | btn-outline-primary |
| print | fa-print | btn-outline-secondary |
| archive | fa-archive | btn-warning |
| restore | fa-undo | btn-success |
| approve | fa-check | btn-success |
| reject | fa-times | btn-danger |
| email | fa-envelope | btn-secondary |
| share | fa-share | btn-secondary |

## Examples for Different Use Cases

### Read-Only List
```bash
python form_cli.py report-datatable user-activity --actions="view,export"
```

### Full CRUD Operations
```bash
python form_cli.py report-datatable products --actions="create,edit,delete,view"
```

### Custom Admin Panel
```bash
python form_cli.py report-datatable users --actions="edit:url=/admin/users/{id}/edit:icon=fa-user-edit,delete:url=/admin/users/{id}/delete:confirm=Delete this user?,view:url=/admin/users/{id}"
```

### Workflow Actions
```bash
python form_cli.py report-datatable orders --actions="view,approve:icon=fa-check-circle:class=btn-success,reject:icon=fa-times-circle:class=btn-danger,archive"
```

### No Actions (Data Display Only)
```bash
python form_cli.py report-datatable analytics-summary --no-actions
```