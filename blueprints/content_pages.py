# blueprints/content_pages.py
# ── Static/informational pages with no request-time business logic ────────
from flask import Blueprint, render_template

bp = Blueprint('content_pages', __name__)


@bp.route("/about")
def about():
    return render_template("about.html")


@bp.route("/team")
def team():
    return render_template("team.html")


@bp.route("/changelog")
def changelog():
    return render_template("changelog.html")


@bp.route('/military-uas')
def military_uas():
    return render_template('military_uas.html')
