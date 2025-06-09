from flask import Flask
from .config import config 
from .register.logging import register_logger
from .register.blueprints import register_blueprints
from .register.template_hooks import register_hooks
from .register.database import register_db


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

    return app

app = create_app()
    
if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5050)