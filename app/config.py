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
    "port": 5050,
    "scan_paths": ["_system", "admin", "user"],
    "base_dir": os.path.join(os.getcwd(), "app"),
    "db_user": "temuragi_user",
    "db_password": "fjk3490qnfmkldsavnmi934qgj03598340-jfklfdsgt34rt23rfdas",
    "db_host": "localhost",
    "db_port": "5432",
    "db_name": "temuragi_db",
    "secret_key": "",
    "debug": True,
    "log_level": "DEBUG",
    "route_prefix": "/v2",
    "log_file": "logs/app.log",
}

CONFIG = {
    "in_container": running_in_container(),
    "port": int(os.environ.get("TEMURAGI_PORT", DEFAULT_CONFIG["port"])),
    "scan_paths": DEFAULT_CONFIG["scan_paths"],
    "base_dir": os.environ.get("TEMURAGI_BASE_DIR", DEFAULT_CONFIG["base_dir"]),
    "db_user": os.environ.get("TEMURAGI_DB_USER", DEFAULT_CONFIG["db_user"]),
    "db_password": os.environ.get("TEMURAGI_DB_PASSWORD", DEFAULT_CONFIG["db_password"]),
    "db_host": os.environ.get("TEMURAGI_DB_HOST", DEFAULT_CONFIG["db_host"]),
    "db_port": os.environ.get("TEMURAGI_DB_PORT", DEFAULT_CONFIG["db_port"]),
    "db_name": os.environ.get("TEMURAGI_DB_NAME", DEFAULT_CONFIG["db_name"]),
    "secret_key": os.environ.get("TEMURAGI_SECRET_KEY", DEFAULT_CONFIG["secret_key"]),
    "debug": os.environ.get("TEMURAGI_DEBUG", str(DEFAULT_CONFIG["debug"])).lower() == "true",
    "log_level": os.environ.get("TEMURAGI_LOG_LEVEL", DEFAULT_CONFIG["log_level"]),
    "route_prefix": DEFAULT_CONFIG["route_prefix"],
    "log_file": DEFAULT_CONFIG["log_file"],
}

CONFIG["db_uri"] = (
    f"postgresql+psycopg2://{CONFIG['db_user']}:{CONFIG['db_password']}"
    f"@{CONFIG['db_host']}:{CONFIG['db_port']}/{CONFIG['db_name']}"
)
