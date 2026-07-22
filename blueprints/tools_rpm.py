# blueprints/tools_rpm.py
# ── RPM Filter Calculator. Imports calculate_rpm_filter and logger from
#    app.py, which owns the try/except guarding the optional
#    analyzer.rpm_filter_calc module. Registered at the bottom of app.py,
#    after those names exist. ───────────────────────────────────────────
from flask import Blueprint, request, render_template

from app import calculate_rpm_filter, logger

bp = Blueprint('tools_rpm', __name__)


@bp.route('/rpm-filter', methods=['GET', 'POST'])
def rpm_filter():
    result = None
    form   = {}
    if request.method == 'POST':
        try:
            kv        = int(request.form.get('kv', 2400))
            battery   = request.form.get('battery', '4S')
            prop_size = float(request.form.get('prop_size', 5.0))
            form = {'kv': kv, 'battery': battery, 'prop_size': prop_size}
            result = calculate_rpm_filter(kv, battery, prop_size)
        except Exception:
            logger.exception("rpm_filter error")
            result = {"error": "เกิดข้อผิดพลาดในการคำนวณ RPM Filter"}
    return render_template('rpm_filter.html', result=result, form=form)
