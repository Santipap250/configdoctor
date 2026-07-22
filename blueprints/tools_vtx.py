# blueprints/tools_vtx.py
# ── VTX-related tool pages — render-only, no server-side logic ────────────
from flask import Blueprint, render_template

bp = Blueprint('tools_vtx', __name__)


@bp.route("/vtx")
def vtx():
    return render_template("vtx.html")


@bp.route("/vtx-range")
def vtx_range():
    return render_template("vtx_range.html")


@bp.route("/vtx-smartaudio")
def vtx_smartaudio():
    return render_template("vtx_smartaudio.html")
