# blueprints/tools_gear.py
# ── FPV Affiliate Gear Guide — extension/UI layer only. Reads optional
#    ?class=&style=&size= query params and maps them onto the affiliate
#    catalog via affiliate/gear_recommender. Does NOT read analyzer/PID/
#    motor-prop/blackbox internals — only plain strings already computed
#    elsewhere are passed in. No context → falls back to generic starter
#    kits. Imports the gear-module wrappers and availability flag from
#    app.py, which owns the try/except import guarding this optional
#    module. Registered at the bottom of app.py, after those names exist. ──
from flask import Blueprint, request, render_template

from app import (
    logger,
    GEAR_MODULE_AVAILABLE,
    _gear_recommend,
    _gear_starter_kits,
    _gear_categories,
    _gear_disclaimer,
    _gear_all_by_category,
    _GEAR_CATEGORY_ORDER,
)

bp = Blueprint('tools_gear', __name__)


@bp.route('/fpv-gear')
def fpv_gear():
    drone_class = (request.args.get('class') or '').strip() or None
    style       = (request.args.get('style') or '').strip() or None
    size_inch   = (request.args.get('size') or '').strip() or None

    matched_ids = set()
    starter_kits = []
    all_by_category = {}

    if GEAR_MODULE_AVAILABLE:
        try:
            all_by_category = _gear_all_by_category()
        except Exception:
            logger.exception("gear_recommender.get_all_by_category failed")
        try:
            matched = _gear_recommend(drone_class=drone_class, style=style, size_inch=size_inch)
            if matched:
                for items in matched.values():
                    for p in items:
                        matched_ids.add(p['id'])
        except Exception:
            logger.exception("gear_recommender.recommend failed")
        try:
            starter_kits = _gear_starter_kits()
        except Exception:
            logger.exception("gear_recommender.get_starter_kits failed")

    return render_template(
        'fpv_gear.html',
        all_by_category=all_by_category,
        matched_ids=matched_ids,
        starter_kits=starter_kits,
        drone_class=drone_class, style=style, size_inch=size_inch,
        categories=(_gear_categories() if GEAR_MODULE_AVAILABLE else {}),
        category_order=_GEAR_CATEGORY_ORDER,
        gear_disclaimer=(_gear_disclaimer() if GEAR_MODULE_AVAILABLE else {"th": "", "en": ""}),
    )
