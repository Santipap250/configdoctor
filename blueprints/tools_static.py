# blueprints/tools_static.py
# ── Tool pages that are pure render_template with no server-side logic.
#    Anything that touches request.form/args, the analyzer modules, or
#    module-level state stays in app.py — see the audit report for the
#    phased plan to migrate the remaining logic-bearing routes. ──────────
from flask import Blueprint, render_template, redirect

bp = Blueprint('tools_static', __name__)


@bp.route("/landing")
def landing():
    return render_template("landing.html")


@bp.route("/")
def loading():
    # PATCH BW-3: redirect straight to /landing to cut a double page load
    return redirect("/landing", code=302)


@bp.route("/ping")
def ping():
    return "pong"


@bp.route('/fpv')
def fpv_hub():
    return render_template('fpv/index.html')


@bp.route('/cli_surgeon')
def cli_surgeon_page():
    return render_template('cli_surgeon.html')


@bp.route('/rates-visualizer')
def rates_visualizer():
    return render_template('rates_visualizer.html')


@bp.route('/cli-comparator')
def cli_comparator():
    return render_template('cli_comparator.html')


@bp.route('/blackbox')
def blackbox_page():
    return render_template('blackbox.html')


@bp.route('/esc-checker')
def esc_checker():
    return render_template('esc_checker.html')


@bp.route('/fpv-trainer')
def fpv_trainer():
    return render_template('fpv_trainer.html')


@bp.route('/flight-quiz')
def flight_quiz():
    """Flight Style Quiz — 5 questions, recommends rates + preset"""
    return render_template('flight_quiz.html')


@bp.route('/bf-wizard')
def bf_wizard():
    """Betaflight Config Wizard — 7 steps → CLI ready to paste"""
    return render_template('bf_wizard.html')


@bp.route('/build-card')
def build_card():
    """Build Card Generator — shareable drone spec card"""
    return render_template('build_card.html')


@bp.route('/tuning-log')
def tuning_log():
    """Tuning Log — records every tuning session"""
    return render_template('tuning_log.html')


@bp.route('/leaderboard')
def leaderboard():
    """Community Config Leaderboard — vote + rank configs"""
    return render_template('leaderboard.html')


@bp.route('/battery-health')
def battery_health():
    return render_template('battery_health.html')


@bp.route('/motor-thermal')
def motor_thermal():
    return render_template('motor_thermal.html')


@bp.route('/loop-analyzer')
def loop_analyzer():
    return render_template('loop_analyzer.html')
