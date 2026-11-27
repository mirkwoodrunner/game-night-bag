from flask import Blueprint, render_template
from sqlalchemy import text

from ..extensions import db

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    # A real database round trip, so the home page doubles as a smoke test.
    db_ok = db.session.execute(text("SELECT 1")).scalar() == 1
    return render_template("index.html", db_ok=db_ok)
