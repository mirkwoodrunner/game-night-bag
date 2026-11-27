import os

from dotenv import load_dotenv
from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

from .config import load_config
from .extensions import db, migrate


def create_app(test_config=None):
    load_dotenv()
    app = Flask(__name__, instance_relative_config=True)
    os.makedirs(app.instance_path, exist_ok=True)

    app.config.update(load_config(app.instance_path))
    if test_config:
        app.config.update(test_config)

    # Render sits behind one proxy. Trust it for client IP and HTTPS scheme.
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)

    db.init_app(app)
    migrate.init_app(app, db)
    from . import models  # noqa: F401  register models with SQLAlchemy

    from .auth import bp as auth_bp, require_login
    from .routes.health import bp as health_bp
    from .routes.main import bp as main_bp
    from .routes.probe import bp as probe_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(probe_bp)
    app.before_request(require_login)

    return app
