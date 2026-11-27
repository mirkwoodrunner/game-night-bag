import os
import secrets

DEFAULT_SCRYFALL_CONTACT = "https://github.com/mirkwoodrunner/game-night-bag"


def normalize_database_url(url):
    """Point postgres URLs at the psycopg v3 driver. Leave others alone."""
    if not url:
        return url
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            return "postgresql+psycopg://" + url[len(prefix):]
    return url


def load_config(instance_path):
    """Build the Flask config dict from environment variables."""
    database_url = normalize_database_url(os.environ.get("DATABASE_URL"))
    is_production = bool(database_url)
    if not database_url:
        database_url = "sqlite:///" + os.path.join(instance_path, "local.db")

    secret_key = os.environ.get("SECRET_KEY")
    if not secret_key:
        if is_production:
            raise RuntimeError("SECRET_KEY must be set when DATABASE_URL is set.")
        secret_key = secrets.token_hex(32)  # dev only, sessions reset on restart

    engine_options = {"pool_pre_ping": True}  # Neon closes idle connections
    if database_url.startswith("postgresql+psycopg://"):
        # Neon's pooler runs PgBouncer. Turn off psycopg's automatic
        # server-side prepared statements so they can't clash with it.
        engine_options["connect_args"] = {"prepare_threshold": None}

    return {
        "SQLALCHEMY_DATABASE_URI": database_url,
        "SQLALCHEMY_ENGINE_OPTIONS": engine_options,
        "SECRET_KEY": secret_key,
        "APP_PASSWORD": os.environ.get("APP_PASSWORD", ""),
        "MOXFIELD_USERNAME": os.environ.get("MOXFIELD_USERNAME", "mirkwoodrunner"),
        "SCRYFALL_CONTACT": os.environ.get("SCRYFALL_CONTACT") or DEFAULT_SCRYFALL_CONTACT,
        "SESSION_COOKIE_HTTPONLY": True,
        "SESSION_COOKIE_SAMESITE": "Lax",
        "SESSION_COOKIE_SECURE": is_production,
        "PERMANENT_SESSION_LIFETIME": 60 * 60 * 24 * 30,  # stay logged in on the phone
    }
