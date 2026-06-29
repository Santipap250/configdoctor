# affiliate/gear_recommender.py — OBIXConfig Doctor extension layer
# ============================================================
# FPV Affiliate Gear Recommendation — UI/catalog layer only.
#
# Scope: this module reads data/fpv_affiliate_products.json and maps a
# drone's *already-computed* class/style/size (plain strings/numbers — the
# output of analyzer/logic, never their internals) onto a small catalog of
# representative FPV parts. It does NOT perform PID math, motor/prop
# physics, or blackbox analysis, and it never imports analyzer/* or
# logic/*. It is safe to delete this entire package without touching any
# analysis logic elsewhere in the app — only app.py's /fpv-gear route and
# the two small UI hooks (templates/fpv/index.html, templates/index.html)
# would need their links removed.
# ============================================================
import json
import os
from functools import lru_cache

_DATA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "fpv_affiliate_products.json",
)

# Stable display order for category sections on the /fpv-gear page.
CATEGORY_ORDER = [
    "motors", "frames", "props", "escs",
    "batteries", "chargers", "goggles", "antennas",
]

# Maps analyzer drone_class (logic/presets.DRONE_CLASSES keys) -> catalog
# compatibility tags. This is a presentation-layer lookup table only — it
# does not affect, and is not affected by, the PID/filter baselines that
# share the same class keys in logic/presets.py.
CLASS_TAG_MAP = {
    "nano":       ["micro", "whoop", "indoor", "2inch"],
    "micro":      ["micro", "whoop", "indoor", "2inch"],
    "whoop":      ["whoop", "micro", "2inch", "3inch", "cinewhoop"],
    "cine":       ["cinewhoop", "3inch", "ducted"],
    "mini":       ["freestyle", "3inch", "5inch"],
    "freestyle":  ["5inch", "freestyle"],
    "heavy_5":    ["5inch", "freestyle", "racing"],
    "mid_lr":     ["7inch", "longrange"],
    "long_range": ["7inch", "longrange", "efficient"],
    "ultra_lr":   ["7inch", "longrange", "efficient"],
}

# Maps flying style (already normalized by app.py to freestyle/racing/
# longrange) -> catalog compatibility tags.
STYLE_TAG_MAP = {
    "freestyle": ["freestyle"],
    "racing":    ["racing"],
    "longrange": ["longrange"],
}

# Thai labels for the small "why recommended" sentence.
_CLASS_LABEL_TH = {
    "nano": "นาโน/ไมโคร", "micro": "ไมโคร", "whoop": "วูป/ทูธพิค",
    "cine": "ซีนวูป", "mini": "มินิ 4 นิ้ว", "freestyle": "ฟรีสไตล์ 5 นิ้ว",
    "heavy_5": "5–6 นิ้วโหลดหนัก", "mid_lr": "มิดเรนจ์ 6–7.5 นิ้ว",
    "long_range": "ลองเรนจ์ 7.6–10 นิ้ว", "ultra_lr": "อัลตร้าลองเรนจ์ 10 นิ้ว+",
}
_STYLE_LABEL_TH = {"freestyle": "ฟรีสไตล์", "racing": "เรซซิ่ง", "longrange": "ลองเรนจ์"}

# Rough size (inches) -> catalog size tag, used only when a caller passes
# a raw size_inch with no drone_class (e.g. a manually-built /fpv-gear URL).
_SIZE_TAG_BANDS = [
    (0.0, 2.75, "2inch"),
    (2.75, 4.0, "3inch"),
    (4.0, 6.0, "5inch"),
    (6.0, 99.0, "7inch"),
]


@lru_cache(maxsize=1)
def _load_catalog():
    """Load + cache the catalog JSON. Returns {} if the file is missing or
    malformed — callers must treat every result of this module as optional
    (the page degrades to an empty state, never a 500)."""
    try:
        with open(_DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _size_tag(size_inch):
    try:
        s = float(size_inch)
    except (TypeError, ValueError):
        return None
    for lo, hi, tag in _SIZE_TAG_BANDS:
        if lo <= s < hi:
            return tag
    return None


def _target_tags(drone_class=None, style=None, size_inch=None):
    tags = set()
    if drone_class:
        tags.update(CLASS_TAG_MAP.get(str(drone_class).strip().lower(), []))
    if style:
        tags.update(STYLE_TAG_MAP.get(str(style).strip().lower(), []))
    if not drone_class:
        st = _size_tag(size_inch)
        if st:
            tags.add(st)
    return tags


def _score(product, target_tags):
    ptags = {str(t).strip().lower() for t in product.get("compatibility_tags", [])}
    return len(ptags & target_tags)


def _why_text(product, drone_class, style, target_tags):
    matched = sorted({str(t) for t in product.get("compatibility_tags", [])
                       if str(t).lower() in target_tags})
    bits = []
    if drone_class:
        bits.append("เข้ากับโดรนคลาส " + _CLASS_LABEL_TH.get(str(drone_class).lower(), str(drone_class)))
    if style:
        bits.append("เหมาะกับสไตล์ " + _STYLE_LABEL_TH.get(str(style).lower(), str(style)))
    if matched:
        bits.append("แท็กที่ตรงกัน: " + ", ".join(matched[:4]))
    return " · ".join(bits) if bits else "อุปกรณ์มาตรฐานที่นิยมใช้ในหมวดนี้"


def get_categories():
    """{category_id: {label_th, label_en, icon}} in catalog-file order."""
    return _load_catalog().get("categories", {})


def get_disclaimer():
    catalog = _load_catalog()
    return {
        "th": catalog.get("disclaimer_th", ""),
        "en": catalog.get("disclaimer_en", ""),
    }


def recommend(drone_class=None, style=None, size_inch=None, limit_per_category=3):
    """Map (drone_class, style, size_inch) -> {category: [product, ...]}.

    Each returned product dict is enriched with a "why" string. Returns
    None when there isn't enough context to make a meaningful match (no
    class, style, or size at all) — callers should fall back to
    get_starter_kits() in that case, per the "no data -> starter kits"
    requirement.
    """
    target_tags = _target_tags(drone_class, style, size_inch)
    if not target_tags:
        return None

    catalog = _load_catalog()
    products = catalog.get("products", [])
    if not products:
        return None

    by_cat = {}
    for p in products:
        score = _score(p, target_tags)
        if score <= 0:
            continue
        by_cat.setdefault(p.get("category"), []).append((score, p))

    if not by_cat:
        return None

    result = {}
    for cat, scored in by_cat.items():
        scored.sort(key=lambda t: t[0], reverse=True)
        chosen = [p for _, p in scored[:limit_per_category]]
        result[cat] = [
            {**p, "why": _why_text(p, drone_class, style, target_tags)}
            for p in chosen
        ]
    return result


def resolve_products_by_id(ids):
    """Return catalog product dicts for the given id list, preserving order."""
    catalog = _load_catalog()
    by_id = {p["id"]: p for p in catalog.get("products", [])}
    return [by_id[i] for i in ids if i in by_id]


def get_starter_kits():
    """Return starter kits with product_ids already resolved to full
    product dicts (each tagged with a simple kit-level "why")."""
    catalog = _load_catalog()
    kits = []
    for kit in catalog.get("starter_kits", []):
        items = resolve_products_by_id(kit.get("product_ids", []))
        items = [
            {**p, "why": "เลือกมาเพื่อ " + kit.get("title_th", "ชุดเริ่มต้นนี้")}
            for p in items
        ]
        kits.append({
            "id": kit.get("id"),
            "title_th": kit.get("title_th", ""),
            "title_en": kit.get("title_en", ""),
            "note_th": kit.get("note_th", ""),
            "products": items,
        })
    return kits
