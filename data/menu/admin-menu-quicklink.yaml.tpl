# UserQuickLink Template (Template)
# Template file - edit values before importing
# 
# INSTRUCTIONS:
# 1. AUTO-GENERATED fields are optional - uncomment to set specific values
# 2. Update foreign key UUIDs to reference existing records
# 3. Edit all other values as needed
# 4. Foreign key constraints must be satisfied before import
# Template file - edit values before importing
# Exported from template CLI

UserQuickLink:
  meta:
    tablename: user_quick_links
    schema: public
  data:
    user_uuid: null
    # NOTE: user_uuid must reference existing record UUID
    menu_link_uuid: null
    # NOTE: menu_link_uuid must reference existing record UUID
    position: 1
    # uuid: 12345678-1234-1234-1234-123456789abc  # AUTO-GENERATED: Optional, system will create if not provided
    is_active: true
    # created_at: '2024-01-01T00:00:00'  # AUTO-GENERATED: Optional, system will create if not provided
    # updated_at: '2024-01-01T00:00:00'  # AUTO-GENERATED: Optional, system will create if not provided
