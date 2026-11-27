import pytest

from app import create_app
from app.auth import reset_lockout
from app.extensions import db

PASSWORD = "test-password"


@pytest.fixture
def app(monkeypatch, tmp_path):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'test.db'}",
        "SQLALCHEMY_ENGINE_OPTIONS": {},
        "SECRET_KEY": "test",
        "APP_PASSWORD": PASSWORD,
        "MOXFIELD_USERNAME": "mirkwoodrunner",
    })
    with app.app_context():
        db.create_all()
    reset_lockout()
    yield app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def logged_in(client):
    client.post("/login", data={"password": PASSWORD})
    return client
