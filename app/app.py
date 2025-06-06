import os
import importlib
import inspect
from flask import Flask, g , session 
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session, relationship

from .config import config 
from .utils.route_collector import collect_blueprint_routes
from .utils.logger import register_logger

from .register_blueprints import register_blueprints
from .register_hooks import register_hooks
from .register_db import register_db



def create_app():
    app = Flask(__name__)

    app.config.update(config)
    register_logger(app)
    register_db(app)

    # http error pages, theme
    register_blueprints(app.config.get('ROUTE_PREFIX', ''),"_system",app)
    # management side of system
    register_blueprints(app.config.get('ADMIN_ROUTE_PREFIX', ''),"admin",app)
    # ops side
    register_blueprints(app.config.get('ROUTE_PREFIX', '')      , "_user",app)

    # THEMES
    register_blueprints(app.config.get('ROUTE_PREFIX', '')      , "themes",app)

    register_hooks("_system",app)
    register_hooks("admin",app)
    register_hooks("_user",app)

    collect_blueprint_routes(app)

    return app

app = create_app()
    
if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5050)