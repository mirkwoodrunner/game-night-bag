import pytest

from app.config import DEFAULT_SCRYFALL_CONTACT, load_config, normalize_database_url


@pytest.mark.parametrize("given,expected", [
    ("postgres://u:p@h/db", "postgresql+psycopg://u:p@h/db"),
    ("postgresql://u:p@h/db?sslmode=require", "postgresql+psycopg://u:p@h/db?sslmode=require"),
    ("postgresql+psycopg://u:p@h/db", "postgresql+psycopg://u:p@h/db"),
    ("sqlite:///x.db", "sqlite:///x.db"),
    (None, None),
])
def test_normalize_database_url(given, expected):
    assert normalize_database_url(given) == expected


def test_sqlite_fallback(monkeypatch, tmp_path):
    for name in ("DATABASE_URL", "SECRET_KEY", "SCRYFALL_CONTACT"):
        monkeypatch.delenv(name, raising=False)
    cfg = load_config(str(tmp_path))
    assert cfg["SQLALCHEMY_DATABASE_URI"] == f"sqlite:///{tmp_path}/local.db"
    assert cfg["SESSION_COOKIE_SECURE"] is False
    assert cfg["SECRET_KEY"]
    assert cfg["SCRYFALL_CONTACT"] == DEFAULT_SCRYFALL_CONTACT


def test_production_needs_secret_key(monkeypatch, tmp_path):
    monkeypatch.setenv("DATABASE_URL", "postgres://u:p@h/db")
    monkeypatch.delenv("SECRET_KEY", raising=False)
    with pytest.raises(RuntimeError):
        load_config(str(tmp_path))


def test_production_settings(monkeypatch, tmp_path):
    monkeypatch.setenv("DATABASE_URL", "postgres://u:p@h/db")
    monkeypatch.setenv("SECRET_KEY", "s")
    cfg = load_config(str(tmp_path))
    assert cfg["SESSION_COOKIE_SECURE"] is True
    assert cfg["SQLALCHEMY_ENGINE_OPTIONS"]["connect_args"] == {"prepare_threshold": None}
