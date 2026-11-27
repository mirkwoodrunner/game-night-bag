"""All Moxfield access lives here. No other module talks to Moxfield.

Moxfield has no official API. These are the undocumented endpoints its own
site uses, so treat every response as untrusted. See docs/DECISIONS.md.
"""
import re
import time
from urllib.parse import quote, urlparse

import requests

USER_AGENT = "GameNightBag/0.1"
ALLOWED_HOSTS = {"api.moxfield.com", "api2.moxfield.com"}
REQUEST_GAP_SECONDS = 1.0
TIMEOUT_SECONDS = 20

DECK_ID_RE = re.compile(r"moxfield\.com/decks/([A-Za-z0-9_-]+)")


def parse_deck_id(text):
    """Accept a Moxfield deck link or a bare public id. Return the id or None."""
    text = (text or "").strip()
    match = DECK_ID_RE.search(text)
    if match:
        return match.group(1)
    if re.fullmatch(r"[A-Za-z0-9_-]{4,64}", text):
        return text
    return None


def deck_url(public_id):
    return f"https://api.moxfield.com/v2/decks/all/{quote(public_id)}"


# --- Phase 1a probe. Remove once the public deck list endpoint is known. ---

def candidate_list_urls(username):
    """Guesses at the endpoint behind the public profile page's deck list."""
    u = quote(username)
    return [
        f"https://api2.moxfield.com/v2/users/{u}/decks?pageNumber=1&pageSize=100",
        f"https://api2.moxfield.com/v3/decks/search?authorUserNames={u}&pageNumber=1&pageSize=100",
        f"https://api2.moxfield.com/v2/decks/search?authorUserNames={u}&pageNumber=1&pageSize=100",
        f"https://api.moxfield.com/v2/users/{u}/decks?pageNumber=1&pageSize=100",
        f"https://api2.moxfield.com/v1/users/{u}",
    ]


def candidate_deck_urls(public_id):
    p = quote(public_id)
    return [deck_url(public_id), f"https://api2.moxfield.com/v3/decks/all/{p}"]


def fetch_raw(url, session=None):
    """One anonymous GET to an allowed Moxfield host. Never raises for HTTP errors."""
    host = urlparse(url).hostname
    if urlparse(url).scheme != "https" or host not in ALLOWED_HOSTS:
        raise ValueError(f"Not an allowed Moxfield API URL: {url}")
    http = session or requests
    started = time.monotonic()
    try:
        resp = http.get(
            url,
            headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
            timeout=TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        return {"url": url, "status": None, "content_type": "", "body": "",
                "error": str(exc), "seconds": round(time.monotonic() - started, 2)}
    body = resp.text
    return {
        "url": url,
        "status": resp.status_code,
        "content_type": resp.headers.get("Content-Type", ""),
        "body": body,
        "error": "Cloudflare block page" if "cloudflare" in body[:3000].lower() else "",
        "seconds": round(time.monotonic() - started, 2),
    }


def probe(urls, session=None, sleep=time.sleep):
    """Fetch each URL one at a time, at least a second apart."""
    results = []
    for i, url in enumerate(urls):
        if i:
            sleep(REQUEST_GAP_SECONDS)
        results.append(fetch_raw(url, session=session))
    return results
