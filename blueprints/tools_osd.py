# blueprints/tools_osd.py
# ── OSD Designer export endpoint. Imports the export helpers, logger, and
#    rate-limit decorator from app.py, which owns them (the cleanup/
#    filename helpers are also reused by app-level maintenance elsewhere).
#    Registered at the bottom of app.py, after those names exist. ─────────
import io
import json

from flask import Blueprint, request, jsonify, send_file, url_for
from werkzeug.utils import secure_filename

from app import (
    app,
    logger,
    _rate,
    _cleanup_osd_files,
    _timestamped_filename,
    _generate_osd_text_from_model,
    _generate_cli_from_model,
)

bp = Blueprint('tools_osd', __name__)


@bp.route('/osd/export', methods=['POST'])
@_rate("5 per minute;30 per day")
def osd_export():
    import os

    fmt       = (request.args.get('format') or 'txt').lower()
    save_flag = str(request.args.get('save', '0')).lower() in ('1', 'true', 'yes')
    data      = request.get_json(silent=True)
    if not isinstance(data, dict):
        return ("Invalid JSON payload", 400)
    if fmt == 'cli':
        content, ext = _generate_cli_from_model(data), 'cli.txt'
    elif fmt == 'json':
        content, ext = json.dumps(data, ensure_ascii=False, indent=2), 'json'
    else:
        content, ext = _generate_osd_text_from_model(data), 'txt'
    if save_flag:
        # SECURITY: limit OSD save to 100KB to prevent disk fill attacks
        if len(content.encode('utf-8')) > 100_000:
            return ("Content too large (max 100KB)", 413)
        out_dir = os.path.join(app.root_path, 'static', 'downloads', 'osd')
        os.makedirs(out_dir, exist_ok=True)
        # CLEANUP: remove files older than 24h before saving
        _cleanup_osd_files(max_age_hours=24)
        fname = secure_filename(_timestamped_filename(prefix="obix_osd", ext=ext))
        try:
            with open(os.path.join(out_dir, fname), 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception:
            # Do not leak exception detail to client
            logger.exception("osd_export save failed")
            return ("Failed to save file. Please try again.", 500)
        return jsonify({"ok": True, "download_url": url_for('static', filename=f'downloads/osd/{fname}'), "filename": fname})
    buf = io.BytesIO()
    buf.write(content.encode('utf-8'))
    buf.seek(0)
    return send_file(buf, mimetype='text/plain', as_attachment=True, download_name=f"obix_osd.{ext}")
