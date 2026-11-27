"""TEMPORARY Phase 1a probe. Runs Moxfield requests from Render, where
Cloudflare allows them, so we can find endpoints and save test fixtures.
Delete this file, its template and its tests once docs/DECISIONS.md records
the endpoints."""
from flask import Blueprint, Response, current_app, render_template, request

from ..importers import moxfield

bp = Blueprint("probe", __name__, url_prefix="/probe")

# Latest run only, in memory. Fine for one user and one worker.
_last_results = []


@bp.route("/", methods=["GET", "POST"])
def index():
    global _last_results
    error = None
    if request.method == "POST":
        action = request.form.get("action")
        urls = []
        if action == "list":
            urls = moxfield.candidate_list_urls(current_app.config["MOXFIELD_USERNAME"])
        elif action == "deck":
            deck_id = moxfield.parse_deck_id(request.form.get("deck", ""))
            if deck_id:
                urls = moxfield.candidate_deck_urls(deck_id)
            else:
                error = "That doesn't look like a Moxfield deck link or id."
        elif action == "custom":
            urls = [request.form.get("url", "").strip()]
        try:
            if urls:
                _last_results = moxfield.probe(urls)
        except ValueError as exc:
            error = str(exc)
    return render_template("probe.html", results=_last_results, error=error)


@bp.route("/raw/<int:n>")
def raw(n):
    if n >= len(_last_results):
        return "No such result. Run the probe again.", 404
    result = _last_results[n]
    return Response(
        result["body"],
        mimetype="application/json" if "json" in result["content_type"] else "text/plain",
        headers={"Content-Disposition": f"attachment; filename=moxfield-{n}.json"},
    )
