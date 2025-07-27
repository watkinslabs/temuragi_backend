import os

def running_in_container():
    if os.path.exists('/.dockerenv'):
        return True
    try:
        with open('/proc/1/cgroup', 'rt') as f:
            return 'docker' in f.read() or 'kubepods' in f.read()
    except Exception:
        return False

DEFAULT_CONFIG = {
    "port": 5000,
    "scan_paths": ["_system", "admin", "user"],
    "base_dir": os.path.join(os.getcwd(), "app"),
    "base_url": "http://localhost",
    "db_user": "temuragi_user",
    "db_password": "fjk3490qnfmkldsavnmi934qgj03598340-jfklfdsgt34rt23rfdas",
    "db_host": "localhost",
    "db_port": "5432",
    "db_name": "temuragi_db",
    "csrf_secret": "fgmdklajfg89r0gfj3490thjkl;tjh43890tuhjiroeqtjoreiqt",
    "debug": True,
    "log_level": "DEBUG",
    "route_prefix": "",
    "log_file": "logs/app.log",
    "encryption_key":"u1tOOtBW2ECTWXSMS_pZ9wwdn4dEZzg_-ihYJfbYbd8="
}


config = {
    "in_container": running_in_container(),
    "port": int(os.environ.get("TEMURAGI_PORT", DEFAULT_CONFIG["port"])),
    "scan_paths": DEFAULT_CONFIG["scan_paths"],
    "base_url": os.environ.get("TEMURAGI_BASE_URL", DEFAULT_CONFIG["base_url"]),
    "base_dir": os.environ.get("TEMURAGI_BASE_DIR", DEFAULT_CONFIG["base_dir"]),
    "db_user": os.environ.get("TEMURAGI_DB_USER", DEFAULT_CONFIG["db_user"]),
    "db_password": os.environ.get("TEMURAGI_DB_PASSWORD", DEFAULT_CONFIG["db_password"]),
    "db_host": os.environ.get("TEMURAGI_DB_HOST", DEFAULT_CONFIG["db_host"]),
    "db_port": os.environ.get("TEMURAGI_DB_PORT", DEFAULT_CONFIG["db_port"]),
    "db_name": os.environ.get("TEMURAGI_DB_NAME", DEFAULT_CONFIG["db_name"]),
    "csrf_secret": os.environ.get("TEMURAGI_CRSF_KEY", DEFAULT_CONFIG["csrf_secret"]),
    "debug": os.environ.get("TEMURAGI_DEBUG", str(DEFAULT_CONFIG["debug"])).lower() == "true",
    "log_level": os.environ.get("TEMURAGI_LOG_LEVEL", DEFAULT_CONFIG["log_level"]),
    "route_prefix": os.environ.get("TEMURAGI_ROUTE_PREFIX",DEFAULT_CONFIG["route_prefix"]),
    "log_file": DEFAULT_CONFIG["log_file"],
    "encryption_key": os.environ.get("TEMURAGI_ENCRYPTION_KEY", DEFAULT_CONFIG["encryption_key"])
}


config["database_uri"] = (
    f"postgresql+psycopg2://{config['db_user']}:{config['db_password']}"
    f"@{config['db_host']}:{config['db_port']}/{config['db_name']}"
)
