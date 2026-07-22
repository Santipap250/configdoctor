# blueprints/api_community.py
# ── Community rating + like API. Imports the SQLite connection helper,
#    the lock guarding it, the IP-hashing helper, the rate-limit decorator,
#    and the shared logger from app.py — all module-level state owned by
#    app.py as the single source of truth. Registered at the bottom of
#    app.py, after those names exist. ──────────────────────────────────────
from flask import Blueprint, request, jsonify

from app import _get_db, _db_lock, _ip_hash, _rate, logger

bp = Blueprint('api_community', __name__)


# ── GET /api/rating — public stats ───────────────────────────────────────
@bp.route('/api/rating', methods=['GET'])
@_rate("60 per minute;600 per day")
def api_rating_get():
    # try/finally everywhere to avoid connection leaks
    try:
        with _db_lock:
            conn = _get_db()
            try:
                row = conn.execute(
                    "SELECT COUNT(*) AS cnt, COALESCE(AVG(stars),0) AS avg FROM ratings"
                ).fetchone()
                likes_row = conn.execute("SELECT COUNT(*) AS cnt FROM likes").fetchone()
            finally:
                conn.close()
        avg = round(row['avg'], 2) if row['cnt'] > 0 else None
        return jsonify({
            'count':  row['cnt'],
            'avg':    avg,
            'likes':  likes_row['cnt'],
        })
    except Exception:
        logger.exception("api_rating_get error")
        return jsonify({'error': 'เกิดข้อผิดพลาดกรุณาลองใหม่'}), 500


# ── POST /api/rating — submit star (1-5) ─────────────────────────────────
@bp.route('/api/rating', methods=['POST'])
@_rate("5 per minute;20 per day")
def api_rating_post():
    # try/finally on conn + never echo str(e) back to the client
    try:
        data  = request.get_json(force=True) or {}
        try:
            stars = int(data.get('stars', 0))
        except (TypeError, ValueError):
            return jsonify({'error': 'stars must be an integer 1–5'}), 400
        if stars < 1 or stars > 5:
            return jsonify({'error': 'stars must be 1–5'}), 400
        h = _ip_hash(request)
        with _db_lock:
            conn = _get_db()
            try:
                existing = conn.execute(
                    "SELECT id FROM ratings WHERE ip_hash = ?", (h,)
                ).fetchone()
                if existing:
                    return jsonify({'error': 'already_rated'}), 409
                conn.execute(
                    "INSERT INTO ratings (ip_hash, stars) VALUES (?, ?)", (h, stars)
                )
                conn.commit()
                row = conn.execute(
                    "SELECT COUNT(*) AS cnt, AVG(stars) AS avg FROM ratings"
                ).fetchone()
            finally:
                conn.close()
        return jsonify({
            'ok':    True,
            'count': row['cnt'],
            'avg':   round(row['avg'], 2),
        })
    except Exception:
        logger.exception("api_rating_post error")
        return jsonify({'error': 'เกิดข้อผิดพลาดกรุณาลองใหม่'}), 500


# ── POST /api/like — toggle like (once per IP) ───────────────────────────
@bp.route('/api/like', methods=['POST'])
@_rate("5 per minute;10 per day")
def api_like_post():
    # try/finally on conn
    try:
        h = _ip_hash(request)
        with _db_lock:
            conn = _get_db()
            try:
                existing = conn.execute(
                    "SELECT id FROM likes WHERE ip_hash = ?", (h,)
                ).fetchone()
                if existing:
                    return jsonify({'error': 'already_liked'}), 409
                conn.execute("INSERT INTO likes (ip_hash) VALUES (?)", (h,))
                conn.commit()
                cnt = conn.execute("SELECT COUNT(*) AS cnt FROM likes").fetchone()['cnt']
            finally:
                conn.close()
        return jsonify({'ok': True, 'likes': cnt})
    except Exception:
        logger.exception("api_like_post error")
        return jsonify({'error': 'เกิดข้อผิดพลาดกรุณาลองใหม่'}), 500
