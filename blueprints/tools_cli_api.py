# blueprints/tools_cli_api.py
# ── JSON APIs behind the CLI Surgeon, CLI Comparator, and Blackbox
#    Analyzer pages. Imports the shared logger, rate-limit decorator, and
#    the wrapped cli_analyze_dump/analyze_blackbox_csv helpers from app.py,
#    which owns the try/except guards around those optional analyzer
#    modules. Registered at the bottom of app.py, after those names exist. ──
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename

from app import logger, _rate, cli_analyze_dump, analyze_blackbox_csv

bp = Blueprint('tools_cli_api', __name__)


@bp.route('/blackbox/analyze', methods=['POST'])
@_rate("10 per minute;100 per day")
def blackbox_analyze():
    try:
        content_type = request.content_type or ""
        if not request.is_json and not content_type.startswith("application/json"):
            return jsonify({"error": "Content-Type must be application/json"}), 415
        data     = request.get_json(force=True) or {}
        csv_text = data.get('csv', '')
        filename = data.get('filename', 'upload.csv')
        # Sanitize filename (logged only, never used in file ops)
        filename = secure_filename(str(filename)[:64]) or 'upload.csv'
        if not csv_text:
            return jsonify({"error": "ไม่พบข้อมูล CSV"}), 400
        # 10MB limit
        if len(csv_text.encode('utf-8')) > 10_000_000:
            return jsonify({"error": "ไฟล์ใหญ่เกิน 10MB"}), 413
        result = analyze_blackbox_csv(csv_text)
        logger.info("blackbox_analyze: %s rows=%s",
                    filename, result.get('meta', {}).get('rows_analyzed', '?'))
        return jsonify(result)
    except Exception:
        logger.exception("blackbox_analyze error")
        return jsonify({"error": "เกิดข้อผิดพลาดในการวิเคราะห์ กรุณาลองใหม่"}), 500


@bp.route('/analyze_cli', methods=['POST'])
@_rate("20 per minute;200 per day")
def analyze_cli():
    try:
        content_type = request.content_type or ""
        if not request.is_json and not content_type.startswith("application/json"):
            return jsonify({"error": "Content-Type must be application/json"}), 415
        data = request.get_json(force=True) or {}
        dump = data.get('dump', '')
        if not isinstance(dump, str):
            return jsonify({"error": "dump must be a string"}), 400
        if not dump:
            return jsonify({"error": "no dump provided"}), 400
        # Size limit
        if len(dump.encode('utf-8')) > 512_000:
            return jsonify({"error": "ไฟล์ใหญ่เกิน 512KB"}), 413
        result = cli_analyze_dump(dump)
        # FIX-04b: extract PID dict from params for easier template/JS consumption
        try:
            params = result.get("params", {})
            result["pid"] = {
                "roll":  {"p": params.get("p_roll"),  "i": params.get("i_roll"),  "d": params.get("d_roll")},
                "pitch": {"p": params.get("p_pitch"), "i": params.get("i_pitch"), "d": params.get("d_pitch")},
                "yaw":   {"p": params.get("p_yaw"),   "i": params.get("i_yaw"),   "d": params.get("d_yaw", 0)},
            }
            result["motor_protocol"] = params.get("motor_pwm_protocol")
            result["dshot_bidir"]    = params.get("dshot_bidir")
        except Exception:
            logger.debug("suppressed exception", exc_info=True)
        # Enrich with firmware version detection
        try:
            from analyzer.cli_surgeon import detect_firmware_version
            result['firmware'] = detect_firmware_version(dump)
        except Exception:
            logger.debug("suppressed exception", exc_info=True)
        return jsonify(result)
    except Exception:
        logger.exception("analyze_cli error")
        return jsonify({"error": "เกิดข้อผิดพลาดในการวิเคราะห์ กรุณาลองใหม่"}), 500


@bp.route('/compare_cli', methods=['POST'])
@_rate("20 per minute;200 per day")
def compare_cli():
    """Compare two CLI dumps and return diff."""
    try:
        content_type = request.content_type or ""
        if not request.is_json and not content_type.startswith("application/json"):
            return jsonify({"error": "Content-Type must be application/json"}), 415
        data  = request.get_json(force=True) or {}
        dump_a = data.get('dump_a', '')
        dump_b = data.get('dump_b', '')
        if not isinstance(dump_a, str) or not isinstance(dump_b, str):
            return jsonify({"error": "dump_a และ dump_b ต้องเป็น string"}), 400
        if not dump_a or not dump_b:
            return jsonify({"error": "ต้องการ dump_a และ dump_b"}), 400
        # Size limit: each dump max 512KB
        if len(dump_a.encode('utf-8')) > 512_000 or len(dump_b.encode('utf-8')) > 512_000:
            return jsonify({"error": "ไฟล์ใหญ่เกิน 512KB ต่อ dump"}), 413
        from analyzer.cli_surgeon import compare_dumps
        result = compare_dumps(dump_a, dump_b)
        return jsonify(result)
    except Exception:
        logger.exception("compare_cli error")
        return jsonify({"error": "เกิดข้อผิดพลาดในการเปรียบเทียบ กรุณาลองใหม่"}), 500
