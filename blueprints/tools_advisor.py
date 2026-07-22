# blueprints/tools_advisor.py
# ── PID Symptom Advisor — Advisor page, Quick Tune Pad, and its JSON API.
#    Imports get_all_symptoms/_get_symptom_advice from app.py, which owns
#    the try/except around analyzer.symptom_advisor (single source of
#    truth for whether that optional module is available). This module is
#    registered at the bottom of app.py, after those names exist, so the
#    import below resolves without a circular-import error. ───────────────
import json
import re

from flask import Blueprint, render_template, jsonify

from app import get_all_symptoms, _get_symptom_advice

bp = Blueprint('tools_advisor', __name__)


def _build_advice_json():
    symptoms_list = get_all_symptoms()
    advice_dict = {s['id']: _get_symptom_advice(s['id']) for s in symptoms_list}
    return symptoms_list, json.dumps(advice_dict, ensure_ascii=False)


@bp.route('/pid-advisor')
def pid_advisor():
    symptoms_list, advice_json = _build_advice_json()
    return render_template('pid_advisor.html', symptoms=symptoms_list, advice_json=advice_json)


@bp.route('/quick-tune')
def quick_tune():
    symptoms_list, advice_json = _build_advice_json()
    return render_template('quick_tune.html', symptoms=symptoms_list, advice_json=advice_json)


@bp.route('/api/symptom/<symptom_id>')
def api_symptom(symptom_id):
    # SECURITY: allow only alphanumeric + underscore IDs
    if not re.match(r'^[a-zA-Z0-9_]{1,80}$', str(symptom_id)):
        return jsonify({"error": "invalid symptom ID"}), 400
    advice = _get_symptom_advice(symptom_id)
    # FIX v2.2: return 404 for unknown symptom ID
    if "error" in advice:
        return jsonify(advice), 404
    return jsonify(advice)
