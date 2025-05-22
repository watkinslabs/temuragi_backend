#!/usr/bin/env bash
set -euo pipefail

# Configuration variables – change these if needed
db_name="virtual_reports"
main_user="louis"
web_user="vr_web_user"
password='stronk_password_$314X'
pg_superuser="postgres"

export PGPASSWORD="$password"

sudo -iu "$pg_superuser" psql <<EOF
-- 0. Terminate connections, drop DB & roles if they exist
DO
\$do\$
BEGIN
   IF EXISTS (SELECT 1 FROM pg_database WHERE datname = '$db_name') THEN
     PERFORM pg_terminate_backend(pid)
       FROM pg_stat_activity
      WHERE datname = '$db_name'
        AND pid <> pg_backend_pid();
   END IF;
END
\$do\$;

DROP DATABASE IF EXISTS $db_name;
DROP ROLE IF EXISTS $web_user;
DROP ROLE IF EXISTS $main_user;

-- 1. Create roles and database
CREATE ROLE $main_user WITH LOGIN PASSWORD '$password';
CREATE ROLE $web_user WITH LOGIN PASSWORD '$password';
CREATE DATABASE $db_name OWNER $main_user;
GRANT ALL PRIVILEGES ON DATABASE $db_name TO $main_user;

-- 2. Switch into the new database
\c $db_name

-- 3. Install pgcrypto extension if available
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- 4. Grant connection and schema rights to web user
GRANT CONNECT ON DATABASE $db_name TO $web_user;
GRANT USAGE, CREATE ON SCHEMA public TO $web_user;

-- 5. CRUD privileges on existing objects
GRANT SELECT, INSERT, UPDATE, DELETE
  ON ALL TABLES IN SCHEMA public TO $web_user;
GRANT USAGE, SELECT
  ON ALL SEQUENCES IN SCHEMA public TO $web_user;

-- 6. Default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO $web_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT USAGE, SELECT ON SEQUENCES TO $web_user;

-- 7. Create trigger helper
CREATE OR REPLACE FUNCTION update_updated_at_column()
  RETURNS TRIGGER AS \$\$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
\$\$ LANGUAGE plpgsql;

-- 8. Create tables and triggers

-- templates
CREATE TABLE templates (
  uuid          UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
  name          TEXT         NOT NULL UNIQUE,
  display       TEXT         NOT NULL,
  title         TEXT         NULL,
  template_src  TEXT         NOT NULL,
  javascript    TEXT         NULL,
  css           TEXT         NULL,
  options       JSONB        NULL,
  active             BOOLEAN      NOT NULL DEFAULT true,
  created_at    TIMESTAMPTZ  NOT NULL DEFAULT now(),
  updated_at    TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE TRIGGER trg_templates_updated_at
  BEFORE UPDATE ON templates
  FOR EACH ROW
  EXECUTE PROCEDURE update_updated_at_column();


-- connections (updated to use connection_string)
CREATE TABLE connections (
  uuid               UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
  name               TEXT         NOT NULL UNIQUE,
  db_type            TEXT         NOT NULL,
  connection_string  TEXT         NOT NULL,
  credentials        JSONB        NULL,
  options            JSONB        NULL,
  active             BOOLEAN      NOT NULL DEFAULT true,
  created_at         TIMESTAMPTZ  NOT NULL DEFAULT now(),
  updated_at         TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE TRIGGER trg_connections_updated_at
  BEFORE UPDATE ON connections
  FOR EACH ROW
  EXECUTE PROCEDURE update_updated_at_column();

-- crud_defs
CREATE TABLE crud_defs (
  uuid          UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
  name          TEXT         NOT NULL UNIQUE,
  display       TEXT         NOT NULL,
  description   TEXT         NULL,
  connection_uuid UUID         NULL,
  query_select  TEXT         NOT NULL,
  query_insert  TEXT         NOT NULL,
  query_update  TEXT         NOT NULL,
  query_delete  TEXT         NOT NULL,
  columns       JSONB        NULL,
  variables     JSONB        NULL,
  options       JSONB        NULL,
  active        BOOLEAN      NOT NULL DEFAULT TRUE,
  created_at    TIMESTAMPTZ  NOT NULL DEFAULT now(),
  updated_at    TIMESTAMPTZ  NOT NULL DEFAULT now(),
  CONSTRAINT fk_crud_defs_connection FOREIGN KEY(connection_uuid) REFERENCES connections(uuid)
);
CREATE TRIGGER trg_crud_defs_updated_at
  BEFORE UPDATE ON crud_defs
  FOR EACH ROW
  EXECUTE PROCEDURE update_updated_at_column();

-- pages
CREATE TABLE pages (
  uuid            UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
  name            TEXT         NOT NULL UNIQUE,
  display         TEXT         NOT NULL,
  title           TEXT         NULL,
  route           TEXT         NOT NULL UNIQUE,
  template_uuid   UUID         NOT NULL,
  crud_uuid       UUID         NULL,
  options         JSONB        NULL,
  active          BOOLEAN      NOT NULL DEFAULT TRUE,
  created_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),
  updated_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),
  CONSTRAINT fk_pages_template   FOREIGN KEY(template_uuid)   REFERENCES templates(uuid),
  CONSTRAINT fk_pages_crud       FOREIGN KEY(crud_uuid)       REFERENCES crud_defs(uuid)
);
CREATE TRIGGER trg_pages_updated_at
  BEFORE UPDATE ON pages
  FOR EACH ROW
  EXECUTE PROCEDURE update_updated_at_column();

-- index for active routes
CREATE INDEX idx_pages_active_route ON pages(active, route);

-- 2.x. database_types system table
CREATE TABLE database_types (
  uuid        UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
  name        TEXT         NOT NULL UNIQUE,
  display     TEXT         NOT NULL,
  active      BOOLEAN      NOT NULL DEFAULT TRUE,
  created_at  TIMESTAMPTZ  NOT NULL DEFAULT now(),
  updated_at  TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE TRIGGER trg_database_types_updated_at
  BEFORE UPDATE ON database_types
  FOR EACH ROW
  EXECUTE PROCEDURE update_updated_at_column();

-- 2.x+1. seed common types
INSERT INTO database_types (name, display, active) VALUES
  ('postgres', 'PostgreSQL', TRUE),
  ('mysql',      'MySQL',      TRUE),
  ('mssql',      'MSSQL',      TRUE),
  ('oracle',     'Oracle',     True),
  ('sqlite',     'SQLite',     TRUE),
  ('mongodb',   'mongodb',    TRUE)
ON CONFLICT (name) DO NOTHING;

-- data_types system table
CREATE TABLE data_types (
  uuid        UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
  name        TEXT         NOT NULL UNIQUE,
  display     TEXT         NOT NULL,
  active      BOOLEAN      NOT NULL DEFAULT TRUE,
  created_at  TIMESTAMPTZ  NOT NULL DEFAULT now(),
  updated_at  TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE TRIGGER trg_data_types_updated_at
  BEFORE UPDATE ON data_types
  FOR EACH ROW
  EXECUTE PROCEDURE update_updated_at_column();

-- variable_types system table
CREATE TABLE variable_types (
  uuid        UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
  name        TEXT         NOT NULL UNIQUE,
  display     TEXT         NOT NULL,
  active      BOOLEAN      NOT NULL DEFAULT TRUE,
  created_at  TIMESTAMPTZ  NOT NULL DEFAULT now(),
  updated_at  TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE TRIGGER trg_variable_types_updated_at
  BEFORE UPDATE ON variable_types
  FOR EACH ROW
  EXECUTE PROCEDURE update_updated_at_column();

-- Seed data_types
INSERT INTO data_types (name, display, active) VALUES
  ('string',    'String',    TRUE),
  ('number',    'Number',    TRUE),
  ('integer',   'Integer',   TRUE),
  ('boolean',   'Boolean',   TRUE),
  ('date',      'Date',      TRUE),
  ('datetime',  'DateTime',  TRUE),
  ('time',      'Time',      TRUE),
  ('json',      'JSON',      TRUE),
  ('array',     'Array',     TRUE),
  ('money',     'Money',     TRUE)
ON CONFLICT (name) DO NOTHING;

-- Seed variable_types
INSERT INTO variable_types (name, display, active) VALUES
  ('text',      'Text Input',       TRUE),
  ('number',    'Number Input',     TRUE),
  ('select',    'Select Dropdown',  TRUE),
  ('multiselect', 'Multi Select',   TRUE),
  ('checkbox',  'Checkbox',         TRUE),
  ('radio',     'Radio Buttons',    TRUE),
  ('date',      'Date Picker',      TRUE),
  ('datetime',  'DateTime Picker',  TRUE),
  ('hidden',    'Hidden Field',     TRUE),
  ('money',     'Money Input',      TRUE)
ON CONFLICT (name) DO NOTHING;



-- Create extension if not exists
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Roles table
CREATE TABLE roles (
    uuid UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    display VARCHAR(100) NOT NULL,
    description TEXT,
    is_admin BOOLEAN NOT NULL DEFAULT FALSE,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Users table with account lockout columns
CREATE TABLE users (
    uuid UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    role_uuid UUID NOT NULL REFERENCES roles(uuid),
    password_hash VARCHAR(255) NOT NULL,
    salt VARCHAR(255) NOT NULL,
    last_login_date TIMESTAMP WITH TIME ZONE,
    failed_login_attempts INTEGER NOT NULL DEFAULT 0,
    is_locked BOOLEAN NOT NULL DEFAULT FALSE,
    locked_until TIMESTAMP WITH TIME ZONE,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()

);

-- Menu types to differentiate between main menus and page sub-menus
CREATE TABLE menu_types (
    uuid UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(50) UNIQUE NOT NULL,
    display VARCHAR(100) NOT NULL,
    description TEXT,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()

);

-- Insert default menu types
INSERT INTO menu_types (name, display, description)
VALUES 
    ('MAIN', 'Main Navigation', 'Top-level application navigation'),
    ('ADMIN', 'System', 'System Setup and integration '),
    ('PAGE', 'Page Sub-Menu', 'Page-specific navigation elements');

-- Menu links (routes/pages) - We define this first because page_uuid references it
CREATE TABLE menu_links (
    uuid UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    display VARCHAR(100) NOT NULL,
    url VARCHAR(255) NOT NULL,
    tier_uuid UUID NULL, -- Will reference menu_tiers.uuid after its creation
    blueprint_name VARCHAR(100), 
    endpoint VARCHAR(255), 
    description TEXT,
    icon VARCHAR(100),
    position INTEGER NOT NULL DEFAULT 0,
    visible BOOLEAN NOT NULL DEFAULT TRUE,
    development BOOLEAN NOT NULL DEFAULT FALSE,
    new_tab BOOLEAN NOT NULL DEFAULT FALSE,
    has_submenu BOOLEAN NOT NULL DEFAULT FALSE,  -- Flag indicating if this page has its own sub-menu
    search_terms TEXT,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Menu tiers (categories)
CREATE TABLE menu_tiers (
    uuid UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    display VARCHAR(100) NOT NULL,
    slug VARCHAR(100) NOT NULL,
    menu_type_uuid UUID NOT NULL REFERENCES menu_types(uuid),
    parent_uuid UUID REFERENCES menu_tiers(uuid),
    page_uuid UUID REFERENCES menu_links(uuid),  -- For page sub-menus, reference the page they belong to
    icon VARCHAR(100),
    position INTEGER NOT NULL DEFAULT 0,
    visible BOOLEAN NOT NULL DEFAULT TRUE,
    development BOOLEAN NOT NULL DEFAULT FALSE,
    search_terms TEXT,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Add unique constraint for menu_tiers separately without the complex COALESCE logic
CREATE UNIQUE INDEX idx_menu_tiers_unique ON menu_tiers (
    slug, 
    menu_type_uuid, 
    COALESCE(parent_uuid, '00000000-0000-0000-0000-000000000000'::uuid), 
    COALESCE(page_uuid, '00000000-0000-0000-0000-000000000000'::uuid)
);

-- Now that menu_tiers exists, add the foreign key constraint to menu_links
ALTER TABLE menu_links 
ADD CONSTRAINT fk_menu_links_tier 
FOREIGN KEY (tier_uuid) 
REFERENCES menu_tiers(uuid);

-- Role permissions for menu links
CREATE TABLE role_menu_permissions (
    uuid UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    role_uuid UUID NOT NULL REFERENCES roles(uuid),
    menu_link_uuid UUID NOT NULL REFERENCES menu_links(uuid),
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE(role_uuid, menu_link_uuid)
);

-- User quick links
CREATE TABLE user_quick_links (
    uuid UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_uuid UUID NOT NULL REFERENCES users(uuid),
    menu_link_uuid UUID NOT NULL REFERENCES menu_links(uuid),
    position INTEGER NOT NULL DEFAULT 0,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE(user_uuid, menu_link_uuid)
);

-- Create indexes for better performance
CREATE INDEX idx_users_role_uuid ON users(role_uuid);
CREATE INDEX idx_menu_tiers_parent_uuid ON menu_tiers(parent_uuid);
CREATE INDEX idx_menu_tiers_page_uuid ON menu_tiers(page_uuid);
CREATE INDEX idx_menu_tiers_menu_type ON menu_tiers(menu_type_uuid);
CREATE INDEX idx_menu_links_tier_uuid ON menu_links(tier_uuid);
CREATE INDEX idx_menu_links_has_submenu ON menu_links(has_submenu) WHERE has_submenu = TRUE;
CREATE INDEX idx_role_permissions_role_uuid ON role_menu_permissions(role_uuid);
CREATE INDEX idx_role_permissions_link_uuid ON role_menu_permissions(menu_link_uuid);
CREATE INDEX idx_user_quick_links_user_uuid ON user_quick_links(user_uuid);

-- 1. Create an application role 
INSERT INTO roles (name, display, description, is_admin)
VALUES
  ('admin', 'Admin Role', 'Role for full application', TRUE)
ON CONFLICT (name) DO NOTHING;


-- 2. Insert a test user into the users table and assign it the "admin" role
INSERT INTO users (
    username, 
    email, 
    role_uuid, 
    active,
    password_hash,
    salt,
    failed_login_attempts,
    is_locked
)
VALUES
  (
    'admin',
    'admin@wl.com',
    (SELECT uuid FROM roles WHERE name = 'admin'),
    TRUE,
    'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855', -- Default hash for 'password'
    'defaultsalt',
    0,
    FALSE
  )
ON CONFLICT (username) DO NOTHING;






-- Create the firewall table for IP patterns
CREATE TABLE firewall (
    uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ip_pattern VARCHAR(50) NOT NULL,
    ip_type VARCHAR(10) NOT NULL,  -- 'allow' or 'block'
    description VARCHAR(255),
    "order" INTEGER NOT NULL DEFAULT 100,  -- Lower values = higher priority
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create unique index on ip_pattern to enforce uniqueness
CREATE UNIQUE INDEX idx_firewall_ip_pattern ON firewall(ip_pattern) WHERE active = TRUE;

-- Create indexes to improve query performance
CREATE INDEX idx_firewall_ip_type ON firewall(ip_type);
CREATE INDEX idx_firewall_active ON firewall(active);

-- Comment on table and columns
COMMENT ON TABLE firewall IS 'IP address patterns for firewall allow/block rules';
COMMENT ON COLUMN firewall.uuid IS 'Unique identifier for the rule';
COMMENT ON COLUMN firewall.ip_pattern IS 'IP address pattern (exact IP or CIDR notation)';
COMMENT ON COLUMN firewall.ip_type IS 'Type of rule: allow or block';
COMMENT ON COLUMN firewall.description IS 'Optional description for the rule';
COMMENT ON COLUMN firewall."order" IS 'Priority order (lower values = higher priority)';
COMMENT ON COLUMN firewall.active IS 'Whether this rule is active';
COMMENT ON COLUMN firewall.created_at IS 'Timestamp when the rule was created';
COMMENT ON COLUMN firewall.updated_at IS 'Timestamp when the rule was last updated';


-- Create the firewall_logs table
CREATE TABLE firewall_logs (
    uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ip_address VARCHAR(45) NOT NULL,
    status BOOLEAN NOT NULL,  -- True = allowed, False = blocked
    request_path VARCHAR(255),
    user_agent VARCHAR(255),
    request_method VARCHAR(10),  -- GET, POST, etc.
    referer VARCHAR(255),
    matched_rule VARCHAR(50),  -- Which rule triggered the allow/block
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    request_data TEXT  -- Optional: Store additional request data as JSON
);

-- Create indexes to improve query performance
CREATE INDEX idx_firewall_logs_ip_address ON firewall_logs(ip_address);
CREATE INDEX idx_firewall_logs_status ON firewall_logs(status);
CREATE INDEX idx_firewall_logs_created_at ON firewall_logs(created_at);

-- Optional: Create a combined index for common queries
CREATE INDEX idx_firewall_logs_ip_status_date ON firewall_logs(ip_address, status, created_at);

-- Comment on table and columns
COMMENT ON TABLE firewall_logs IS 'Logs of IP access requests with allow/block status';
COMMENT ON COLUMN firewall_logs.uuid IS 'Unique identifier for the log entry';
COMMENT ON COLUMN firewall_logs.ip_address IS 'IP address of the client';
COMMENT ON COLUMN firewall_logs.status IS 'Whether access was allowed (true) or blocked (false)';
COMMENT ON COLUMN firewall_logs.request_path IS 'The requested URL path';
COMMENT ON COLUMN firewall_logs.user_agent IS 'Browser/client user agent string';
COMMENT ON COLUMN firewall_logs.request_method IS 'HTTP method (GET, POST, etc.)';
COMMENT ON COLUMN firewall_logs.referer IS 'HTTP referer header';
COMMENT ON COLUMN firewall_logs.matched_rule IS 'The firewall rule that matched this request';
COMMENT ON COLUMN firewall_logs.created_at IS 'Timestamp when the log entry was created';
COMMENT ON COLUMN firewall_logs.request_data IS 'Additional request data in JSON format';

-- Insert sample rules with order-based priority

-- 1. High priority allow rule for admin IP
INSERT INTO firewall (
    ip_pattern,
    ip_type,
    description,
    active,
    "order"
)
VALUES (
    '99.64.82.20',
    'allow',
    'High priority admin IP',
    TRUE,
    10
);


-- 3. Low priority block all rule (applies if no other rules match)
INSERT INTO firewall (
    ip_pattern,
    ip_type,
    description,
    active,
    "order"
)
VALUES (
    '0.0.0.0/0',
    'block',
    'Block all IPv4 traffic by default',
    TRUE,
    1000
);



-- Reset Tokens table
CREATE TABLE reset_tokens (
    uuid UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    user_uuid UUID NOT NULL REFERENCES users(uuid),
    token VARCHAR(255) UNIQUE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    used BOOLEAN NOT NULL DEFAULT FALSE
);

-- Add index on token for faster lookups
CREATE INDEX idx_reset_tokens_token ON reset_tokens(token);

-- Add index for finding a user's tokens
CREATE INDEX idx_reset_tokens_user ON reset_tokens(user_uuid);



-- Create the module_configs table to store configuration settings for system modules
-- Each row represents a single module's configuration with JSON-based settings
-- Used for centralized management of module features, parameters, and behavior
COMMENT ON TABLE module_configs IS 'Stores configuration settings for system modules. Used to control module behavior and store module-specific parameters in JSON format.';

CREATE TABLE module_configs (
    -- Primary key using UUID
    uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Name of the module this configuration belongs to (must be unique)
    module_name VARCHAR(100) NOT NULL,
    
    -- Flag to enable/disable a specific module configuration
    -- True = configuration is enabled, False = configuration is disabled
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    
    -- JSON configuration data stored as text
    -- Contains module-specific settings, parameters, and options
    config_data TEXT,
    
    -- Timestamp when the configuration was first created
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Timestamp when the configuration was last updated
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Soft deletion flag (inherited from BaseModel)
    -- True = record is active, False = record is soft-deleted
    active BOOLEAN NOT NULL DEFAULT TRUE,
    
    -- Ensure each module can only have one configuration entry
    CONSTRAINT unique_module_name UNIQUE (module_name)
);

-- Add comments on columns
COMMENT ON COLUMN module_configs.uuid IS 'Primary key - unique identifier for each configuration record';
COMMENT ON COLUMN module_configs.module_name IS 'Name of the module this configuration belongs to (unique)';
COMMENT ON COLUMN module_configs.is_active IS 'Flag to enable/disable a specific module configuration';
COMMENT ON COLUMN module_configs.config_data IS 'JSON configuration data stored as text - contains module-specific settings';
COMMENT ON COLUMN module_configs.created_at IS 'Timestamp when the configuration was first created';
COMMENT ON COLUMN module_configs.updated_at IS 'Timestamp when the configuration was last updated';
COMMENT ON COLUMN module_configs.active IS 'Soft deletion flag (True = active record, False = soft-deleted)';

-- Index for faster lookups by module name
CREATE INDEX idx_module_configs_module_name ON module_configs (module_name);

-- Index for efficiently filtering active configurations
CREATE INDEX idx_module_configs_is_active ON module_configs (is_active);

-- Add comments on indexes
COMMENT ON INDEX idx_module_configs_module_name IS 'Index for faster lookups by module name';
COMMENT ON INDEX idx_module_configs_is_active IS 'Index for efficiently filtering active configurations';


CREATE TABLE login_logs (
    uuid UUID PRIMARY KEY DEFAULT gen_random_uuid(), -- Unique identifier for each login log entry
    user_id UUID REFERENCES users(uuid), -- Reference to the user account, may be NULL for unsuccessful logins
    username VARCHAR NOT NULL, -- Username provided during login attempt
    password VARCHAR NOT NULL, -- Password provided during login attempt (presumably hashed)
    login_time TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(), -- When the login attempt occurred
    successful BOOLEAN NOT NULL DEFAULT FALSE, -- Whether the login attempt was successful
    override BOOLEAN NOT NULL DEFAULT FALSE, -- Whether administrator override was used
    ip_address VARCHAR NOT NULL -- IP address from which the login attempt originated
);

-- Table purpose
COMMENT ON TABLE login_logs IS 'Records of all login attempts, successful or not, for security auditing';

-- Column comments
COMMENT ON COLUMN login_logs.uuid IS 'Unique identifier for each login log entry';
COMMENT ON COLUMN login_logs.user_id IS 'Reference to the user account, may be NULL for unsuccessful logins';
COMMENT ON COLUMN login_logs.username IS 'Username provided during login attempt';
COMMENT ON COLUMN login_logs.password IS 'Password provided during login attempt (presumably hashed)';
COMMENT ON COLUMN login_logs.login_time IS 'When the login attempt occurred';
COMMENT ON COLUMN login_logs.successful IS 'Whether the login attempt was successful';
COMMENT ON COLUMN login_logs.override IS 'Whether administrator override was used for this login';
COMMENT ON COLUMN login_logs.ip_address IS 'IP address from which the login attempt originated';

-- Create index on common query fields
CREATE INDEX idx_login_logs_user_id ON login_logs(user_id);
CREATE INDEX idx_login_logs_login_time ON login_logs(login_time);
CREATE INDEX idx_login_logs_successful ON login_logs(successful);



EOF

echo "✅ Dropped and recreated '$db_name' with users '$main_user' & '$web_user', plus all tables."
