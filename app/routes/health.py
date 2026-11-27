from flask import Blueprint

bp = Blueprint("health", __name__)


@bp.route("/healthz")
def healthz():
    # Never touches the database, so it stays fast during cold starts.
    return {"status": "ok"}
