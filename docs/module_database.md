# New Module Database Setup Guide

## 1. Creating a New Module with Models

### 1.1 Choose Your Numbering Range

## Core System Architecture (0-99)
### 0-9: Foundation/Base
- 0_base_model.py - Base model class
- 1_core_config_model.py - Core configuration
- 2_system_log_model.py - System logging
### 10-19: Database/Cache
- 10_database_connection_model.py
- 11_cache_model.py
- 12_migration_model.py
### 20-29: Security/Encryption
- 20_encryption_key_model.py
- 21_security_token_model.py
- 22_audit_log_model.py
### 30-39: System Monitoring
- 30_system_health_model.py
- 31_performance_metric_model.py
- 32_error_tracking_model.py
---
## Core Application Models (100-299)
### 100-119: User Management
- 100_user_model.py - Core user entity
- 101_user_profile_model.py - Extended user info
- 102_user_preference_model.py - User settings
- 103_user_session_model.py - Session tracking
- 104_user_activity_model.py - Activity logs
### 120-139: Authentication & Security
- 120_authentication_model.py - Auth methods
- 121_password_reset_model.py - Password recovery
- 122_two_factor_auth_model.py - 2FA
- 123_login_attempt_model.py - Security tracking
- 124_firewall_rule_model.py - Security rules
### 140-159: Roles & Permissions
- 140_role_model.py - Role definitions
- 141_permission_model.py - Permission entities
- 142_role_permission_model.py - Role-permission mapping
- 143_user_role_model.py - User-role assignments
- 144_permission_group_model.py - Permission grouping
### 160-179: Menu & Navigation
- 160_menu_type_model.py - Menu type definitions
- 161_menu_tier_model.py - Menu hierarchy
- 162_menu_link_model.py - Menu items/links
- 163_menu_quick_link_model.py - User quick links
- 164_role_menu_permission_model.py - Menu access control
- 165_navigation_breadcrumb_model.py - Breadcrumb tracking
### 180-199: Content Management
- 180_page_model.py - CMS pages
- 181_page_version_model.py - Page versioning
- 182_content_block_model.py - Reusable content
- 183_media_file_model.py - File uploads
- 184_content_category_model.py - Content organization
### 200-219: Communication
- 200_notification_model.py - System notifications
- 201_email_template_model.py - Email templates
- 202_message_model.py - Internal messaging
- 203_announcement_model.py - System announcements
- 204_newsletter_model.py - Newsletter system
### 220-239: Settings & Configuration
- 220_application_setting_model.py - App settings
- 221_feature_flag_model.py - Feature toggles
- 222_theme_model.py - UI themes
- 223_localization_model.py - Multi-language
- 224_timezone_model.py - Timezone handling
### 240-259: API & Integration
- 240_api_key_model.py - API access keys
- 241_webhook_model.py - Webhook definitions
- 242_external_service_model.py - Service integrations
- 243_oauth_client_model.py - OAuth configurations
- 244_api_rate_limit_model.py - Rate limiting
### 260-279: Reporting & Analytics
- 260_report_model.py - Report definitions
- 261_dashboard_model.py - Dashboard configs
- 262_metric_model.py - Business metrics
- 263_analytics_event_model.py - Event tracking
- 264_kpi_model.py - Key performance indicators
### 280-299: System Administration
- 280_backup_model.py - Backup management
- 281_maintenance_mode_model.py - Maintenance scheduling
- 282_system_update_model.py - Update tracking
- 283_license_model.py - License management
- 284_deployment_model.py - Deployment history
---
## Business Logic Models (300-499)
### 300-319: Customer Management
- 300_customer_model.py - Customer entities
- 301_customer_contact_model.py - Contact info
- 302_customer_address_model.py - Address management
- 303_customer_note_model.py - Customer notes
- 304_customer_segment_model.py - Customer segmentation
### 320-339: Product/Inventory Management
- 320_product_model.py - Product catalog
- 321_product_category_model.py - Product categories
- 322_product_variant_model.py - Product variations
- 323_inventory_model.py - Stock management
- 324_supplier_model.py - Supplier information
### 340-359: Order Management
- 340_order_model.py - Order entities
- 341_order_item_model.py - Order line items
- 342_order_status_model.py - Order status tracking
- 343_shipping_model.py - Shipping information
- 344_return_model.py - Return/refund handling
### 360-379: Financial Management
- 360_invoice_model.py - Invoice generation
- 361_payment_model.py - Payment tracking
- 362_transaction_model.py - Financial transactions
- 363_tax_model.py - Tax calculations
- 364_discount_model.py - Discount/coupon system
### 380-399: Project Management
- 380_project_model.py - Project entities
- 381_task_model.py - Task management
- 382_milestone_model.py - Project milestones
- 383_time_tracking_model.py - Time logs
- 384_project_resource_model.py - Resource allocation
### 400-419: Document Management
- 400_document_model.py - Document storage
- 401_document_version_model.py - Version control
- 402_document_permission_model.py - Access control
- 403_document_template_model.py - Templates
- 404_document_workflow_model.py - Approval workflows
### 420-439: Event Management
- 420_event_model.py - Event entities
- 421_event_registration_model.py - Registration
- 422_event_schedule_model.py - Event scheduling
- 423_event_ticket_model.py - Ticketing
- 424_event_venue_model.py - Venue management
### 440-459: Marketing & Sales
- 440_campaign_model.py - Marketing campaigns
- 441_lead_model.py - Lead management
- 442_opportunity_model.py - Sales opportunities
- 443_contact_form_model.py - Contact submissions
- 444_survey_model.py - Survey system
### 460-479: Support & Helpdesk
- 460_ticket_model.py - Support tickets
- 461_ticket_category_model.py - Ticket categories
- 462_knowledge_base_model.py - KB articles
- 463_faq_model.py - FAQ system
- 464_support_agent_model.py - Agent management
### 480-499: Workflow & Automation
- 480_workflow_model.py - Workflow definitions
- 481_workflow_step_model.py - Workflow steps
- 482_automation_rule_model.py - Automation rules
- 483_trigger_model.py - Event triggers
- 484_action_model.py - Automated actions
---
## Extensions & Plugins (500-999)
### 500-549: Third-party Integrations
- 500_stripe_integration_model.py
- 501_paypal_integration_model.py
- 502_salesforce_integration_model.py
- 503_mailchimp_integration_model.py
- 504_slack_integration_model.py
### 550-599: Advanced Features
- 550_ai_model_config_model.py
- 551_machine_learning_model.py
- 552_recommendation_engine_model.py
- 553_search_index_model.py
- 554_chat_bot_model.py
### 600-649: Mobile & API Extensions
- 600_mobile_app_config_model.py
- 601_push_notification_model.py
- 602_mobile_session_model.py
- 603_app_version_model.py
- 604_device_registration_model.py
### 650-699: Enterprise Features
- 650_tenant_model.py - Multi-tenancy
- 651_organization_model.py - Enterprise orgs
- 652_department_model.py - Org structure
- 653_cost_center_model.py - Cost allocation
- 654_compliance_model.py - Compliance tracking
### 700-749: Performance & Scaling
- 700_cache_strategy_model.py
- 701_cdn_config_model.py
- 702_load_balancer_model.py
- 703_queue_job_model.py
- 704_background_task_model.py
### 750-799: Development & Testing
- 750_test_data_model.py
- 751_mock_service_model.py
- 752_performance_test_model.py
- 753_ab_test_model.py
- 754_feature_branch_model.py
### 800-849: Monitoring & Observability
- 800_log_aggregation_model.py
- 801_metric_collection_model.py
- 802_alert_rule_model.py
- 803_health_check_model.py
- 804_trace_model.py
### 850-899: Security Extensions
- 850_vulnerability_scan_model.py
- 851_security_policy_model.py
- 852_incident_response_model.py
- 853_threat_detection_model.py
- 854_compliance_report_model.py
### 900-999: Custom/Client-Specific
- 900_custom_field_model.py
- 901_client_specific_model.py
- 950_legacy_migration_model.py
- 999_experimental_model.py
---

### 1.2 Module Structure

```bash
# Create your module
MODULE=customers
CONTEXT=admin  # or _system / _user
BASE=app/$CONTEXT/$MODULE

mkdir -p $BASE/tpl/$MODULE $BASE/static $BASE/tests
touch $BASE/__init__.py $BASE/view.py $BASE/hook.py
```

### 1.3 Model Dependencies - Critical Order

**Your models MUST be numbered by dependencies:**

```python
# Example: Customer module using 300-319 range
300_customer_model.py           # Independent
301_customer_contact_model.py   # Depends on customer
302_customer_address_model.py   # Depends on customer
303_customer_note_model.py      # Depends on customer + user (for who wrote note)
304_customer_segment_model.py   # Depends on customer
```

## 2. Model Implementation

### 2.1 Independent Model (No Dependencies)

```python
# 300_customer_model.py
from sqlalchemy import Column, String, Text, Boolean, DateTime
from app._system._core.base import BaseModel

class Customer(BaseModel):
    __tablename__ = 'customers'

    name = Column(String(200), nullable=False)
    email = Column(String(100), nullable=True, unique=True)
    phone = Column(String(20), nullable=True)
    active = Column(Boolean, default=True, nullable=False)
```

### 2.2 Model Depending on Your Own Models

```python
# 301_customer_contact_model.py
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app._system._core.base import BaseModel

class CustomerContact(BaseModel):
    __tablename__ = 'customer_contacts'

    contact_type = Column(String(50), nullable=False)  # 'email', 'phone', 'address'
    contact_value = Column(String(200), nullable=False)
    
    # Foreign key to your own model (lower number)
    customer_uuid = Column(UUID(as_uuid=True),
                          ForeignKey('customers.uuid', ondelete='CASCADE'),
                          nullable=False)
    
    customer = relationship("Customer", backref="contacts")
```

### 2.3 Model Depending on System Models

```python
# 303_customer_note_model.py - References both customer AND user
from sqlalchemy import Column, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app._system._core.base import BaseModel

class CustomerNote(BaseModel):
    __tablename__ = 'customer_notes'

    note_text = Column(Text, nullable=False)
    note_type = Column(String(50), default='general', nullable=False)
    
    # Reference your own model
    customer_uuid = Column(UUID(as_uuid=True),
                          ForeignKey('customers.uuid', ondelete='CASCADE'),
                          nullable=False)
    
    # Reference system model (user who wrote the note)
    created_by_uuid = Column(UUID(as_uuid=True),
                            ForeignKey('users.uuid', ondelete='SET NULL'),
                            nullable=True)
    
    customer = relationship("Customer", backref="notes")
    created_by = relationship("User", backref="customer_notes")
```

## 3. Referencing System Models

### 3.1 Common System References

```python
# Reference users (from 100_user_model.py)
user_uuid = Column(UUID(as_uuid=True),
                  ForeignKey('users.uuid', ondelete='SET NULL'),
                  nullable=True)

# Reference roles (from 140_role_model.py) 
role_uuid = Column(UUID(as_uuid=True),
                  ForeignKey('roles.uuid', ondelete='RESTRICT'),
                  nullable=False)

# Reference authentication logs (from 120_authentication_model.py)
auth_uuid = Column(UUID(as_uuid=True),
                  ForeignKey('authentications.uuid', ondelete='SET NULL'),
                  nullable=True)
```

### 3.2 Cross-Module References

```python
# Example: Order module (340-359) referencing Customer module (300-319)
# 340_order_model.py
class Order(BaseModel):
    __tablename__ = 'orders'
    
    order_date = Column(DateTime, nullable=False)
    
    # Reference customer (lower number = loads first)
    customer_uuid = Column(UUID(as_uuid=True),
                          ForeignKey('customers.uuid', ondelete='RESTRICT'),
                          nullable=False)
    
    # Reference user who created order
    created_by_uuid = Column(UUID(as_uuid=True),
                            ForeignKey('users.uuid', ondelete='SET NULL'),
                            nullable=True)
    
    customer = relationship("Customer", backref="orders")
    created_by = relationship("User", backref="orders_created")
```

### 3.3 Accessing Models in Views

```python
# In view.py
from flask import Blueprint, render_template, request, jsonify

bp = Blueprint("customers", __name__, url_prefix="/customers")

@bp.route("/")
def list_customers():
    # Import your models
    from app.admin.customers.customer_300_model import Customer
    
    customers = Customer.query.all()
    return render_template("customers/list.html", customers=customers)

@bp.route("/notes", methods=["POST"]) 
def add_note_ajax():
    # Import multiple models including system ones
    from app.admin.customers.customer_note_303_model import CustomerNote
    from app._system.user.user_100_model import User
    
    data = request.get_json()
    
    note = CustomerNote(
        note_text=data['text'],
        customer_uuid=data['customer_uuid'],
        created_by_uuid=data['user_uuid']
    )
    
    app.db_session.add(note)
    app.db_session.commit()
    
    return jsonify({"status": "success", "note_id": str(note.uuid)})
```

## 4. Table Management

### 4.1 Check Loading Order

```bash
# Preview model loading order
python menu_cli.py preview-order

# Should show your models in correct dependency order:
# 100-119: User Management
#   100: _system/user/100_user_model.py
#
# 300-319: Customer Management  
#   300: admin/customers/300_customer_model.py
#   301: admin/customers/301_customer_contact_model.py
#   303: admin/customers/303_customer_note_model.py
```

### 4.2 Create Tables

```bash
# Create all tables in dependency order
python menu_cli.py create-tables

# Output shows models loading in order:
# ✓ 100_user_model.py
# ✓ 300_customer_model.py
# ✓ 301_customer_contact_model.py
# ✓ 303_customer_note_model.py
# Database tables created successfully
```

### 4.3 Development Table Cleanup

```bash
# During development, clean up your specific tables:

# Option 1: Drop your specific tables (manual)
psql -d your_db -c "DROP TABLE IF EXISTS customer_notes CASCADE;"
psql -d your_db -c "DROP TABLE IF EXISTS customer_contacts CASCADE;" 
psql -d your_db -c "DROP TABLE IF EXISTS customers CASCADE;"
python menu_cli.py create-tables

# Option 2: Full system cleanup (nuclear option)
python menu_cli.py cleanup full
python menu_cli.py create-tables
```

## 5. Common Integration Patterns

### 5.1 User Tracking Pattern

```python
# Track who created/modified records
class Customer(BaseModel):
    # ... other fields ...
    
    created_by_uuid = Column(UUID(as_uuid=True),
                            ForeignKey('users.uuid', ondelete='SET NULL'),
                            nullable=True)
    modified_by_uuid = Column(UUID(as_uuid=True),
                             ForeignKey('users.uuid', ondelete='SET NULL'),
                             nullable=True)
    
    created_by = relationship("User", foreign_keys=[created_by_uuid])
    modified_by = relationship("User", foreign_keys=[modified_by_uuid])
```

### 5.2 Status/Configuration Pattern

```python
# Reference system configuration
class Customer(BaseModel):
    # ... other fields ...
    
    status = Column(String(20), default='active', nullable=False)
    
    # Or reference application settings (220_application_setting_model.py)
    default_payment_terms_uuid = Column(UUID(as_uuid=True),
                                       ForeignKey('application_settings.uuid'),
                                       nullable=True)
```

### 5.3 Audit Trail Pattern

```python
# 304_customer_audit_model.py
class CustomerAudit(BaseModel):
    __tablename__ = 'customer_audits'
    
    table_name = Column(String(50), nullable=False)
    record_uuid = Column(UUID(as_uuid=True), nullable=False)
    action = Column(String(20), nullable=False)  # 'CREATE', 'UPDATE', 'DELETE'
    changes = Column(Text, nullable=True)  # JSON of what changed
    
    # Reference user who made the change
    user_uuid = Column(UUID(as_uuid=True),
                      ForeignKey('users.uuid', ondelete='SET NULL'),
                      nullable=True)
    
    user = relationship("User")
```

## 6. Testing Your Module

### 6.1 Basic Model Test

```python
# tests/test_customer_models.py
def test_customer_creation():
    from app.admin.customers.customer_300_model import Customer
    
    customer = Customer(
        name="Test Customer",
        email="test@example.com",
        phone="555-1234"
    )
    
    app.db_session.add(customer)
    app.db_session.commit()
    
    assert customer.uuid is not None
    assert customer.name == "Test Customer"
```

### 6.2 Cross-Model Relationship Test

```python
def test_customer_note_relationship():
    from app.admin.customers.customer_300_model import Customer
    from app.admin.customers.customer_note_303_model import CustomerNote
    from app._system.user.user_100_model import User
    
    # Create test data
    customer = Customer(name="Test Customer")
    user = User.query.first()  # Assuming users exist
    
    app.db_session.add(customer)
    app.db_session.flush()  # Get UUID
    
    note = CustomerNote(
        note_text="Test note",
        customer_uuid=customer.uuid,
        created_by_uuid=user.uuid
    )
    
    app.db_session.add(note)
    app.db_session.commit()
    
    # Test relationships work
    assert note.customer.name == "Test Customer"
    assert note.created_by.email == user.email
    assert len(customer.notes) == 1
```

## 7. Troubleshooting

### 7.1 Foreign Key Errors
```
relation "customers" does not exist
```
**Fix:** Check model numbering. `300_customer_model.py` must load before `301_customer_contact_model.py`

### 7.2 Import Errors  
```
cannot import name 'Customer'
```
**Fix:** Import models inside functions, not at module level:
```python
# WRONG - imports at module level
from app.admin.customers.customer_300_model import Customer

# RIGHT - imports inside functions
@bp.route("/")
def customers():
    from app.admin.customers.customer_300_model import Customer
    # ... use Customer here
```

### 7.3 Relationship Errors
```
Could not determine join condition
```
**Fix:** Use explicit foreign_keys when multiple relationships to same table:
```python
created_by = relationship("User", foreign_keys=[created_by_uuid])
modified_by = relationship("User", foreign_keys=[modified_by_uuid])
```

### 7.4 Wrong Number Range
```
Model loads in wrong order
```
**Fix:** Use `python menu_cli.py preview-order` to check loading sequence. Ensure dependencies have lower numbers.

## 8. Deployment Checklist

- [ ] Chosen appropriate number range from 0-999 system
- [ ] Models numbered in dependency order (dependencies have lower numbers)
- [ ] All foreign keys reference existing tables from lower-numbered models
- [ ] `python menu_cli.py preview-order` shows models in correct sequence
- [ ] `python menu_cli.py create-tables` succeeds without foreign key errors
- [ ] Tests pass for model creation and cross-model relationships
- [ ] view.py imports models inside route functions, not at module level
- [ ] No circular dependencies between models