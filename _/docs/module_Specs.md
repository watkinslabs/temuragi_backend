# Temuragi Modular Format – Technical Definition

## 1.  Scope

Defines the mandatory directory layout, naming conventions, and registration hooks required for any module that plugs into the Temuragi Flask platform.

## 2.  Core Principles

* **Self-containment**… each module owns all code, templates, static assets, and data models it needs.
* **Discoverability**… the platform locates modules automatically through filesystem scanning.  No manual import lists.
* **Convention over configuration**… follow the conventions below and zero configuration is required.

## 3.  Directory Layout

```
<package_root>/
│── <context>/        # _system  |  admin  |  _user
│   │── <module_name>/
│   │   │── __init__.py        # optional, may be empty
│   │   │── view.py            # Blueprint & routes  (mandatory)
│   │   │── hook.py            # register_* functions (optional)
│   │   │── *_model.py         # SQLAlchemy models (0…n files)
│   │   │── tpl/               # Jinja templates (optional)
│   │   │── static/            # Static assets (optional)
│   │   └── tests/             # pytest tests (optional)
```

* **context** chooses the URL prefix…

  * `_system`  → `ROUTE_PREFIX`
  * `admin`    → `ADMIN_ROUTE_PREFIX`
  * `_user`    → `ROUTE_PREFIX`
* Nested categorisation dirs are allowed to group modules… they **must contain nothing but sub-dirs and `__init__.py`**.

## 4.  Module Contents

### 4.1  view\.py (required)

```python
from flask import Blueprint, render_template, request, jsonify

bp = Blueprint(
    "<module_name>",
    __name__,
    url_prefix="/<module_name>",
    template_folder="tpl",
    static_folder="static",
)

@bp.route("/")
def home():
    return render_template("<module_name>/home.html")
```

* Variable **bp** must be a `flask.Blueprint` object.
* `url_prefix` **must** start with `/` and be relative (core registration injects global prefix later).
* Do not import the app instance… use application context only.

### 4.2  hook.py (optional)

Provide one or many functions named `register_*`.  Each will be invoked with the `Flask` app instance after blueprints have been registered.

```python
from flask import current_app

def register_firewall_handlers(app):
    """Example hook adding before_request handler."""
    @app.before_request
    def my_guard():
        current_app.logger.debug("guard")
```

### 4.3  \*\_model.py (0…n)

* File name ends with `_model.py`.
* Define `SQLAlchemy` models inheriting from `app._system._core.base.BaseModel`.
* No manual engine binding… the global session handles this.

### 4.4  Templates & static

* **Main pages**… Place full-page Jinja templates under `tpl/<module_name>/` and start every file with:

  ```jinja
  {% extends active_page_path %}
  ```

  This inherits the global layout that bundles Bootstrap 5 and Font Awesome, ensuring consistent styling.
* **Fragments**… Store reusable/loop-heavy partials in `tpl/<module_name>/fragments/`.  Keep the parent template clean by including them via `{% include '<module_name>/fragments/<file>.html' %}`.
* **Static assets**… Put CSS/JS/images under `static/`; Blueprint already exposes that path.

## 5.  Registration Flow

1. **Models**… `register_models()` walks each context path and imports any file ending `_model.py`.
2. **Blueprints**… `register_blueprints()` imports `view.py`, fetches **bp**, and attaches it with computed prefix:
   `full_prefix = <context_prefix> + bp.url_prefix`.
3. **Hooks**… `register_hooks()` imports `hook.py` and calls any `register_*` functions.

No extra work is required by module authors.

## 6.  Reserved Names

* `view.py`, `hook.py`, `tpl`, `static`… do not rename.
* Within models avoid table names that collide with existing core tables.

## 7.  Coding Guidelines

* Use snake\_case for all identifiers.
* Use `uuid.UUID` primary keys via `BaseModel`.
* Do not access global `db_session` directly inside import time… wrap inside request or app context.
* Keep module side-effects inside `register_*` hook bodies.
* **AJAX function naming**… Any server function handling an AJAX request **must** have a name ending in `_ajax`.

## 8.  Module Skeleton Generator

```bash
MODULE=my_module
CONTEXT=_system     # or admin / _user
BASE=app/$CONTEXT/$MODULE
mkdir -p $BASE/tpl/$MODULE $BASE/static $BASE/tests
cat > $BASE/__init__.py <<EOF
"""$MODULE module"""
EOF
cat > $BASE/view.py <<EOF
from flask import Blueprint, render_template

bp = Blueprint(
    "$MODULE",
    __name__,
    url_prefix="/$MODULE",
    template_folder="tpl",
    static_folder="static",
)

@bp.route("/")
def home():
    return render_template("$MODULE/home.html")
EOF
```

## 9.  Interaction Model and Tech Stack

* **Rendering**… Destination pages are rendered server-side by Flask/Jinja templates that extend the site-level theme.
* **AJAX first**… All dynamic interaction on these pages is expected to occur via jQuery `$.ajax` calls that exchange JSON payloads.
* **AJAX function naming**… Functions serving these AJAX endpoints **must** have `_ajax` appended to their function names.
* **AJAX method**… All AJAX endpoints **must** be registered with `methods=['POST']`; clients must invoke them using HTTP POST.
* **Default context**… Each template automatically receives common variables injected by `_system/templates/hook.register_template_processor` (e.g. `logged_in`, `user_id`, `theme`, `client_ip`). Authors can rely on them without extra code.
* **Stack**… Backend: Python, Flask, SQLAlchemy.  Front-end: Bootstrap 5, Font Awesome, and jQuery.

## 10.  Quality Checklist

* [ ] `view.py` exists and defines **bp**
* [ ] No hard coded URLs... use `url_for()` where possible
* [ ] Hook functions are idempotent
* [ ] Unit tests under `tests/` pass
* [ ] All AJAX endpoints use function names ending `_ajax` and accept POST only

## 11.  Runtime and Deployment Environment

* **OS**... CentOS Stream 10 with SELinux enforcing and systemd.
* **Python**... latest CPython 3 release available from EPEL or the `python-3xx` Software Collection.
* **WSGI layer**... Gunicorn (`gunicorn app:app --workers 4 --worker-class gevent --preload`).
* **Web front**... Nginx handles TLS termination, compression, and serves `/static/*` directly.
* **Virtualenv**... project lives under `/opt/temuragi`, venv in `/opt/temuragi/venv`.
* **Process supervision**... `temuragi.service` systemd unit keeps Gunicorn alive and restarts on failure.
* **Logging**... JSON file logs rotated in `/var/log/temuragi/` plus journald.

## 12.  Git Workflow and Release Cycle

* **Single repo**... All source lives in a git repository.
* **Branch per module**... create `feature/<module_name>` or `bugfix/<ticket>` branches; do not commit directly to `staging` or `main`.
* **Pull request**... open PR to `staging`; CI runs `pytest`, `flake8`, `black --check`, and integration tests.
* **Staging deploy**... merge into `staging` triggers auto-deployment to the staging server.
* **Promotion**... after QA sign-off merge `staging` into `main`; tag `vX.Y.Z`; production deploy.
* **Hotfix**... emergency patches come from `hotfix/*` branches, merged back to `staging` and `main`.

## 13.  Database Layer

* **Primary store**… PostgreSQL ≥ 14.
* **Driver stack**… SQLAlchemy 2.x → `psycopg2-binary` is the default driver; `pyodbc` is also available for DSN-style connection strings when required.
* **Config DB vs target DBs**… The `DATABASE_URI` in *config.py* points to the central *configuration* database holding connection definitions, auth, menu, etc.  Individual modules may define extra **Connection** rows that point to external target databases.
* **Automatic schema creation**… Each module’s `*_model.py` files are imported during `register_models()`.  At first run (or whenever a new module ships) `Base.metadata.create_all()` is executed against the config DB, creating any new tables automatically… no manual migration needed for module tables.
* **Alembic**… Core tables are managed with Alembic migrations; module tables rely on the auto-create mechanism and should be backward compatible.

---

© 2025 Temuragi  …  Licensed under BSD-3-Clause
