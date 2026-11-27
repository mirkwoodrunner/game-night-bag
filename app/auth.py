"""Single-password login with a simple per-IP lockout."""
import hmac
import time
from collections import defaultdict, deque

from flask import Blueprint, current_app, redirect, render_template, request, session, url_for

bp = Blueprint("auth", __name__)

MAX_FAILURES = 10
WINDOW_SECONDS = 15 * 60
PUBLIC_ENDPOINTS = {"auth.login", "health.healthz", "static"}

# In memory, so it resets on restart and assumes one gunicorn worker.
_failures = defaultdict(deque)


def _recent_failures(ip, now):
    attempts = _failures[ip]
    while attempts and now - attempts[0] > WINDOW_SECONDS:
        attempts.popleft()
    return attempts


def reset_lockout():
    _failures.clear()


def require_login():
    if request.endpoint in PUBLIC_ENDPOINTS or request.endpoint is None:
        return None
    if session.get("logged_in"):
        return None
    return redirect(url_for("auth.login", next=request.full_path))


def _safe_next(target):
    # Only allow local paths, so the login page can't redirect off-site.
    if target and target.startswith("/") and not target.startswith("//"):
        return target
    return url_for("main.index")


@bp.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        ip = request.remote_addr or "unknown"
        now = time.monotonic()
        attempts = _recent_failures(ip, now)
        expected = current_app.config["APP_PASSWORD"]
        given = request.form.get("password", "")
        if len(attempts) >= MAX_FAILURES:
            error = "Too many failed attempts. Try again in 15 minutes."
        elif not expected:
            error = "APP_PASSWORD is not set on the server."
        elif hmac.compare_digest(given.encode(), expected.encode()):
            attempts.clear()
            session.clear()
            session.permanent = True
            session["logged_in"] = True
            return redirect(_safe_next(request.args.get("next")))
        else:
            attempts.append(now)
            error = "Wrong password."
        return render_template("login.html", error=error), 401
    return render_template("login.html", error=error)


@bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
