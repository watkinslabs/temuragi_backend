from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

class Engines:
    """Holds your engines.  One for config DB, and lazily-created ones for each target DSN."""
    def __init__(self, config_uri):
        # single engine to your Postgres “config server”
        self.config_engine = create_engine(config_uri, pool_size=5, max_overflow=10)
        # session factory for config DB
        self.ConfigSession = sessionmaker(bind=self.config_engine)
        # cache for per-page engines
        self._target_engines = {}

    def get_config_session(self):
        return self.ConfigSession()

    def get_target_engine(self, dsn, **opts):
        # reuse an engine per-DSN (keyed by the full DSN string)
        if dsn not in self._target_engines:
            self._target_engines[dsn] = create_engine(dsn, **opts)
        return self._target_engines[dsn]