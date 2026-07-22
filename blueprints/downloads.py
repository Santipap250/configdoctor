# blueprints/downloads.py
# ── Diff-file downloads listing + hardened path-traversal-safe file serve.
#    Imports app (for app.root_path) and _file_sha256 (cached hashing
#    helper) from app.py, which owns the SHA-256 cache as a module-level
#    dict shared across requests. ──────────────────────────────────────────
import os

from flask import Blueprint, abort, send_from_directory, render_template
from werkzeug.utils import secure_filename

from app import app, _file_sha256

bp = Blueprint('downloads', __name__)


@bp.route('/downloads/<fc>/<filename>')
def download_diff(fc, filename):
    safe_fc = secure_filename(fc)
    safe_fn = secure_filename(filename)
    base_root = os.path.realpath(os.path.join(app.root_path, 'static', 'downloads', 'diff_all'))
    if not safe_fc:
        abort(404)
    candidate_fc_dir = os.path.realpath(os.path.join(base_root, safe_fc))
    if not (candidate_fc_dir.startswith(base_root + os.sep) and os.path.isdir(candidate_fc_dir)):
        abort(404)
    file_path = os.path.realpath(os.path.join(candidate_fc_dir, safe_fn))
    if not file_path.startswith(candidate_fc_dir + os.sep):
        abort(404)
    if not os.path.isfile(file_path):
        abort(404)
    return send_from_directory(candidate_fc_dir, safe_fn, as_attachment=True)


@bp.route('/downloads')
def downloads_index():
    base = os.path.realpath(os.path.join(app.root_path, 'static', 'downloads', 'diff_all'))
    items = []
    if os.path.isdir(base):
        for fc in sorted(os.listdir(base)):
            fcdir = os.path.realpath(os.path.join(base, fc))
            if not os.path.isdir(fcdir):
                continue
            for fn in sorted(os.listdir(fcdir)):
                path = os.path.join(fcdir, fn)
                if not os.path.isfile(path):
                    continue
                items.append({'fc': fc, 'filename': fn,
                              'size': os.path.getsize(path),
                              'mtime': int(os.path.getmtime(path)),
                              'sha': _file_sha256(path)})
    return render_template('downloads.html', items=items)
