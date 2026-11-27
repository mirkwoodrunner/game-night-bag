"""Tests for the temporary probe. Moxfield is always mocked."""
import pytest

from app.importers import moxfield


class FakeResponse:
    def __init__(self, status=200, text='{"ok": true}', ctype="application/json"):
        self.status_code = status
        self.text = text
        self.headers = {"Content-Type": ctype}


class FakeSession:
    def __init__(self, response=None):
        self.calls = []
        self.response = response or FakeResponse()

    def get(self, url, headers, timeout):
        self.calls.append((url, headers))
        return self.response


@pytest.mark.parametrize("text,expected", [
    ("https://moxfield.com/decks/AbC123_x-9", "AbC123_x-9"),
    ("https://www.moxfield.com/decks/AbC123?tab=stats", "AbC123"),
    ("AbC123", "AbC123"),
    ("  AbC123  ", "AbC123"),
    ("not a deck link!", None),
    ("", None),
])
def test_parse_deck_id(text, expected):
    assert moxfield.parse_deck_id(text) == expected


def test_fetch_raw_rejects_other_hosts():
    with pytest.raises(ValueError):
        moxfield.fetch_raw("https://evil.example/x", session=FakeSession())
    with pytest.raises(ValueError):
        moxfield.fetch_raw("http://api.moxfield.com/x", session=FakeSession())


def test_fetch_raw_sends_headers_and_flags_cloudflare():
    session = FakeSession(FakeResponse(403, "<title>Attention Required! | Cloudflare</title>", "text/html"))
    result = moxfield.fetch_raw(moxfield.deck_url("abc"), session=session)
    assert session.calls[0][1]["User-Agent"] == "GameNightBag/0.1"
    assert result["status"] == 403
    assert result["error"] == "Cloudflare block page"


def test_probe_waits_between_requests():
    sleeps = []
    session = FakeSession()
    results = moxfield.probe(["https://api.moxfield.com/a", "https://api2.moxfield.com/b"],
                             session=session, sleep=sleeps.append)
    assert [r["status"] for r in results] == [200, 200]
    assert sleeps == [1.0]


def test_probe_page_runs_and_downloads(logged_in, monkeypatch):
    def fake_probe(urls):
        return [{"url": u, "status": 200, "content_type": "application/json",
                 "body": '{"name": "Deck"}', "error": "", "seconds": 0.1} for u in urls]
    monkeypatch.setattr(moxfield, "probe", fake_probe)
    resp = logged_in.post("/probe/", data={"action": "deck", "deck": "https://moxfield.com/decks/abc123"})
    assert resp.status_code == 200
    assert b"api.moxfield.com/v2/decks/all/abc123" in resp.data
    raw = logged_in.get("/probe/raw/0")
    assert raw.status_code == 200
    assert raw.data == b'{"name": "Deck"}'


def test_probe_page_bad_deck_and_bad_custom_url(logged_in):
    resp = logged_in.post("/probe/", data={"action": "deck", "deck": "nope nope"})
    assert b"doesn&#39;t look like" in resp.data
    resp = logged_in.post("/probe/", data={"action": "custom", "url": "https://evil.example/"})
    assert b"Not an allowed Moxfield API URL" in resp.data
