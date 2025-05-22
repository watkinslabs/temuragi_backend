

-- Trigger function to auto-update updated_at columns
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- templates: hold all your Jinja + assets
CREATE TABLE templates (
  uuid          UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
  name          TEXT         NOT NULL UNIQUE,
  display       TEXT         NOT NULL,
  title         TEXT         NULL,
  template_src  TEXT         NOT NULL,
  javascript    TEXT         NULL,
  css           TEXT         NULL,
  options       JSONB        NULL,
  created_at    TIMESTAMPTZ  NOT NULL DEFAULT now(),
  updated_at    TIMESTAMPTZ  NOT NULL DEFAULT now(),
  active        BOOLEAN      NOT NULL DEFAULT TRUE
);

CREATE TRIGGER trg_templates_updated_at
BEFORE UPDATE ON templates
FOR EACH ROW
EXECUTE PROCEDURE update_updated_at_column();

-- crud_defs: SQL queries + metadata
CREATE TABLE crud_defs (
  uuid          UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
  name          TEXT         NOT NULL UNIQUE,
  display       TEXT         NOT NULL,
  description   TEXT         NULL,
  query_select  TEXT         NOT NULL,
  query_insert  TEXT         NOT NULL,
  query_update  TEXT         NOT NULL,
  query_delete  TEXT         NOT NULL,
  columns       JSONB        NULL,
  variables     JSONB        NULL,
  options       JSONB        NULL,
  created_at    TIMESTAMPTZ  NOT NULL DEFAULT now(),
  updated_at    TIMESTAMPTZ  NOT NULL DEFAULT now(),
  active        BOOLEAN      NOT NULL DEFAULT TRUE
);

CREATE TRIGGER trg_crud_defs_updated_at
BEFORE UPDATE ON crud_defs
FOR EACH ROW
EXECUTE PROCEDURE update_updated_at_column();

-- connections: external DB endpoints
CREATE TABLE connections (
  uuid            UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
  name            TEXT         NOT NULL UNIQUE,
  db_type         TEXT         NOT NULL,       -- e.g. 'mssql','mysql','postgres'
  dsn             TEXT         NOT NULL,
  credentials     JSONB        NULL,            -- encrypted JSON { user, pass, … }
  options         JSONB        NULL,
  created_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),
  updated_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),
  active          BOOLEAN      NOT NULL DEFAULT TRUE
);

CREATE TRIGGER trg_connections_updated_at
BEFORE UPDATE ON connections
FOR EACH ROW
EXECUTE PROCEDURE update_updated_at_column();

-- pages: map a route to a template (+ optional CRUD + optional connection)
CREATE TABLE pages (
  uuid            UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
  name            TEXT         NOT NULL UNIQUE,
  display         TEXT         NOT NULL,
  title           TEXT         NULL,
  route           TEXT         NOT NULL UNIQUE,
  template_uuid   UUID         NOT NULL,
  crud_uuid       UUID         NULL,
  connection_uuid UUID         NULL,
  options         JSONB        NULL,
  created_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),
  updated_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),
  active          BOOLEAN      NOT NULL DEFAULT TRUE,
  CONSTRAINT fk_pages_template
    FOREIGN KEY(template_uuid) REFERENCES templates(uuid),
  CONSTRAINT fk_pages_crud
    FOREIGN KEY(crud_uuid) REFERENCES crud_defs(uuid),
  CONSTRAINT fk_pages_connection
    FOREIGN KEY(connection_uuid) REFERENCES connections(uuid)
);

CREATE TRIGGER trg_pages_updated_at
BEFORE UPDATE ON pages
FOR EACH ROW
EXECUTE PROCEDURE update_updated_at_column();

-- index to speed up route lookups of active pages
CREATE INDEX idx_pages_active_route ON pages(active, route);
