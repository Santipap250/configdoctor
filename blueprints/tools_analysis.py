# blueprints/tools_analysis.py
# ── The core CLI-dump analysis flow: the /app form page, its JSON-API
#    twin used by AJAX form submission, and the Motor×Prop recommender.
#    Imports the shared form-handling helpers and preset data from app.py,
#    which owns them as the single source of truth (also used directly by
#    tests via `import app as A; A._handle_analysis_post()`). Registered
#    at the bottom of app.py, after those names exist. ─────────────────────
from flask import Blueprint, request, render_template, jsonify

from app import (
    logger,
    _rate,
    _handle_analysis_post,
    _handle_analysis_get_params,
    _recommend_motor_prop,
    PRESET_GROUPS,
    PRESETS,
)

bp = Blueprint('tools_analysis', __name__)


@bp.route("/app", methods=["GET", "POST"])
def index():
    # HTML page — NEVER rate-limit. Only /api/* endpoints are limited.
    analysis = None

    if request.method == "POST":
        try:
            analysis = _handle_analysis_post()
        except Exception:
            logger.exception("index POST error")
            analysis = {"warnings": [{"level": "error", "msg": "เกิดข้อผิดพลาดในการวิเคราะห์"}]}
        return render_template("index.html", analysis=analysis,
                               preset_groups=PRESET_GROUPS,
                               all_presets=PRESETS)

    # GET — if share params present, auto-run analysis so shared links work
    _SHARE_PARAMS = ("size", "battery", "style", "weight", "prop_size",
                     "blades", "pitch", "motor_kv", "motor_count", "battery_mAh")
    if any(request.args.get(p) for p in _SHARE_PARAMS):
        try:
            analysis = _handle_analysis_get_params()
        except Exception:
            logger.exception("index GET share-param error")
            analysis = None

    return render_template("index.html", analysis=analysis,
                           preset_groups=PRESET_GROUPS,
                           all_presets=PRESETS)


# ── /api/analyze — rate-limited JSON API (used by JS fetch, not the HTML form) ──
@bp.route("/api/analyze", methods=["POST"])
@_rate("20 per minute")
def api_analyze():
    """JSON endpoint for AJAX form submission.
    Returns the full analysis dict as JSON.
    The HTML form at /app still works via traditional POST (not rate-limited).
    """
    try:
        analysis = _handle_analysis_post()
        return jsonify(analysis)
    except Exception:
        logger.exception("api_analyze error")
        return jsonify({"error": "เกิดข้อผิดพลาดในการวิเคราะห์ กรุณาลองใหม่"}), 500


@bp.route('/motor-prop', methods=['GET', 'POST'])
def motor_prop():
    if request.method == 'POST':
        result = _recommend_motor_prop(request.form)
        return render_template('motor_prop.html', result=result)
    return render_template('motor_prop.html')
