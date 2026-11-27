from tests.conftest import PASSWORD


def test_healthz_is_public(client):
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok"}


def test_pages_require_login(client):
    for path in ("/", "/probe/"):
        resp = client.get(path)
        assert resp.status_code == 302
        assert "/login" in resp.headers["Location"]


def test_wrong_password(client):
    resp = client.post("/login", data={"password": "nope"})
    assert resp.status_code == 401
    assert b"Wrong password" in resp.data
    assert client.get("/").status_code == 302


def test_right_password_and_home_hits_db(client):
    resp = client.post("/login", data={"password": PASSWORD})
    assert resp.status_code == 302
    home = client.get("/")
    assert home.status_code == 200
    assert b"Database connected" in home.data


def test_next_redirect_is_local_only(client):
    resp = client.post("/login?next=//evil.example", data={"password": PASSWORD})
    assert resp.headers["Location"] == "/"
    client.post("/logout")
    resp = client.post("/login?next=/probe/", data={"password": PASSWORD})
    assert resp.headers["Location"] == "/probe/"


def test_lockout_after_ten_failures(client):
    for _ in range(10):
        client.post("/login", data={"password": "nope"})
    resp = client.post("/login", data={"password": PASSWORD})
    assert b"Too many failed attempts" in resp.data
    assert client.get("/").status_code == 302


def test_missing_app_password(app, client):
    app.config["APP_PASSWORD"] = ""
    resp = client.post("/login", data={"password": ""})
    assert b"APP_PASSWORD is not set" in resp.data


def test_logout(logged_in):
    logged_in.post("/logout")
    assert logged_in.get("/").status_code == 302
