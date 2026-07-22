# blueprints/meta.py
# ── Ops/SEO endpoints — health check, robots.txt, sitemap.xml.
#    Imports _BASE_URL and _SITEMAP_CACHE from app.py, which owns them as
#    the single source of truth (used elsewhere for absolute URL
#    generation and daily sitemap caching). Registered at the bottom of
#    app.py after those names exist. ──────────────────────────────────────
from datetime import datetime

from flask import Blueprint, jsonify, Response

from app import _BASE_URL, _SITEMAP_CACHE

bp = Blueprint('meta', __name__)


@bp.route("/healthz")
def healthz():
    # Don't expose module status in production
    return jsonify({"status": "ok"})


@bp.route("/robots.txt")
def robots_txt():
    content = (
        "User-agent: *\n"
        "Crawl-delay: 10\n"
        "Allow: /\n"
        "Disallow: /static/downloads/osd/\n"
        "Disallow: /analyze_cli\n"
        "Disallow: /compare_cli\n"
        "Disallow: /blackbox/analyze\n"
        "Disallow: /api/\n"
        "\n"
        "User-agent: GPTBot\nDisallow: /\n\n"
        "User-agent: CCBot\nDisallow: /\n\n"
        "User-agent: anthropic-ai\nDisallow: /\n\n"
        "User-agent: Claude-Web\nDisallow: /\n\n"
        "User-agent: Bytespider\nDisallow: /\n\n"
        "User-agent: PetalBot\nDisallow: /\n\n"
        "User-agent: SemrushBot\nDisallow: /\n\n"
        "User-agent: AhrefsBot\nDisallow: /\n\n"
        "User-agent: MJ12bot\nDisallow: /\n\n"
        "\n"
        f"Sitemap: {_BASE_URL}/sitemap.xml\n"
    )
    resp = Response(content, mimetype="text/plain")
    resp.headers["Cache-Control"] = "public, max-age=86400"
    return resp


@bp.route("/sitemap.xml")
def sitemap_xml():
    today = datetime.now().strftime("%Y-%m-%d")
    if (_SITEMAP_CACHE.get("date") == today
            and _SITEMAP_CACHE.get("base") == _BASE_URL
            and _SITEMAP_CACHE.get("xml")):
        xml = _SITEMAP_CACHE["xml"]
    else:
        pages = [
            ("/team",             "monthly", "0.7"),
            ("/flight-quiz",      "weekly",  "0.8"),
            ("/bf-wizard",        "weekly",  "0.9"),
            ("/build-card",       "weekly",  "0.8"),
            ("/tuning-log",       "weekly",  "0.7"),
            ("/leaderboard",      "weekly",  "0.8"),
            ("/landing",          "weekly",  "1.0"),
            ("/blackbox",         "weekly",  "1.0"),
            ("/app",              "weekly",  "0.9"),
            ("/cli_surgeon",      "weekly",  "0.9"),
            ("/pid-advisor",      "weekly",  "0.9"),
            ("/quick-tune",       "weekly",  "0.9"),
            ("/rpm-filter",       "weekly",  "0.8"),
            ("/motor-prop",       "weekly",  "0.8"),
            ("/rates-visualizer", "weekly",  "0.8"),
            ("/cli-comparator",   "weekly",  "0.8"),
            ("/esc-checker",      "weekly",  "0.8"),
            ("/fpv-trainer",      "weekly",  "0.9"),
            ("/battery-health",   "weekly",  "0.8"),
            ("/motor-thermal",    "weekly",  "0.8"),
            ("/loop-analyzer",    "weekly",  "0.8"),
            ("/osd",              "weekly",  "0.7"),
            ("/vtx",              "monthly", "0.6"),
            ("/vtx-range",        "monthly", "0.6"),
            ("/vtx-smartaudio",   "monthly", "0.6"),
            ("/downloads",        "weekly",  "0.7"),
            ("/fpv",              "monthly", "0.6"),
            ("/about",            "monthly", "0.5"),
            ("/changelog",        "weekly",  "0.5"),
            ("/military-uas",     "weekly",  "0.8"),
        ]
        base = _BASE_URL
        urls = "\n".join(
            f"""  <url>
    <loc>{base}{loc}</loc>
    <lastmod>{today}</lastmod>
    <changefreq>{freq}</changefreq>
    <priority>{pri}</priority>
  </url>"""
            for loc, freq, pri in pages
        )
        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{urls}
</urlset>"""
        _SITEMAP_CACHE["xml"] = xml
        _SITEMAP_CACHE["date"] = today
        _SITEMAP_CACHE["base"] = _BASE_URL
    resp = Response(xml, mimetype="application/xml")
    resp.headers["Cache-Control"] = "public, max-age=86400"
    return resp
