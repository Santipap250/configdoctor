# analyzer/units.py — OBIXConfig Doctor
# ============================================================
# Single source of truth for small shared parsing/unit helpers
# used across the Drone Analyzer pipeline (app.py, logic/presets.py,
# analyzer/thrust_logic.py, analyzer/rpm_filter_calc.py,
# analyzer/advanced_analysis.py).
#
# WHY THIS FILE EXISTS:
# Before this fix, FIVE different modules each had their own
# hand-rolled "parse battery string into cell count" function.
# They disagreed with each other on:
#   - valid clamp range (1–8 vs 1–12 vs 2–12)
#   - which string formats they could parse ("4S" vs "4s2p" vs "4S+")
# A user entering a perfectly normal battery label like "4S2P" or
# "6S 1500mAh" could silently get DIFFERENT cell counts in different
# parts of the same analysis, or — in app.py's case — could trigger
# an uncaught ValueError that silently discarded the entire propeller
# physics calculation for that request (see app.py _handle_analysis_post).
#
# This module replaces all of those with one tested implementation.
# ============================================================
from __future__ import annotations
import re
from typing import Optional, Union

# Real-world FPV battery packs run from 1S (tiny whoop) up to 12S
# (heavy long-range / cargo hex/octo builds), which is within the
# 1"-15" frame range this app explicitly supports.
MIN_CELLS = 1
MAX_CELLS = 12
DEFAULT_CELLS = 4

_CELL_RE = re.compile(r'(\d+)\s*[Ss]')


# ============================================================
# DEFAULT BATTERY CAPACITY (mAh) — used only when the user leaves the
# battery-capacity field blank, to estimate flight time.
#
# WHY THIS EXISTS: analyzer/advanced_analysis.py and analyzer/thrust_logic.py
# each had their own default-mAh guess table — one keyed by size+cell count,
# the other by size only (ignoring cell count entirely). Both run in the
# SAME request (app.py's /app and /api/analyze both call make_advanced_report
# AND estimate_battery_runtime_detail back to back) and their numbers were
# never reconciled: for a 5" 6S build with no mAh entered, advanced_analysis
# guessed 1100 mAh while thrust_logic guessed 1500 mAh — a 36% gap, exposed
# as two disagreeing flight-time numbers (est_flight_time_min vs
# flight_time_detail.avg_flight_min) in the same /api/analyze JSON response.
#
# Per-project decision (Tony, 2026-07-07): the size+cell-aware table
# (originally in advanced_analysis.py) is the more physically accurate one —
# more series cells for the same pack size generally means fewer parallel
# groups and therefore lower mAh at the same energy/weight — so it wins
# wherever it has data. For the four sizes it didn't cover (4.5", 5.5",
# 7.5", 10"), we keep thrust_logic's flat (cell-agnostic) values rather
# than inventing new numbers. No existing table value was changed — this
# only decides which existing value wins when they disagreed.
# ============================================================
DEFAULT_BATTERY_MAH_TABLE = {
    2.5: {3: 450, 4: 450},
    3.0: {3: 550, 4: 650},
    3.5: {3: 650, 4: 850},
    4.0: {3: 850, 4: 1000},
    4.5: 1200,   # thrust_logic-only size — no per-cell breakdown available
    5.0: {4: 1500, 5: 1300, 6: 1100},
    5.5: 1500,   # thrust_logic-only size
    6.0: {4: 1800, 5: 1500, 6: 1300},
    7.0: {5: 2200, 6: 2200, 7: 1500},
    7.5: 2200,   # thrust_logic-only size
    8.0: {6: 3000, 7: 2200, 8: 1800},
    10.0: 3500,  # thrust_logic-only size
}


def default_battery_mah(size_inch: float, cells: int) -> int:
    """
    Guess a default battery capacity (mAh) from frame size and cell count,
    for use when the user hasn't entered a capacity. See
    DEFAULT_BATTERY_MAH_TABLE above for why this is the one place this
    guess should happen.
    """
    try:
        size_inch = float(size_inch)
    except (TypeError, ValueError):
        size_inch = 5.0
    keys = sorted(DEFAULT_BATTERY_MAH_TABLE.keys())
    closest = min(keys, key=lambda k: abs(k - size_inch))
    entry = DEFAULT_BATTERY_MAH_TABLE[closest]
    if isinstance(entry, dict):
        try:
            cells = int(cells)
        except (TypeError, ValueError):
            cells = DEFAULT_CELLS
        if cells in entry:
            return entry[cells]
        available = sorted(entry.keys())
        return entry[min(available, key=lambda c: abs(c - cells))]
    return entry


def cells_from_battery_string(
    battery: Optional[Union[str, int, float]],
    default: int = DEFAULT_CELLS,
    lo: int = MIN_CELLS,
    hi: int = MAX_CELLS,
) -> int:
    """
    Parse a battery label into a cell (S) count.

    Accepts: "4S", "4s", "6S+", "4s2p", "4S 1500mAh", "6S2P", plain "4",
    or a bare int/float. Falls back to `default` (clamped to [lo, hi])
    for anything unparseable, instead of raising — callers that need to
    know parsing failed should check `is_valid_battery_string()` first.
    """
    if battery is None:
        return max(lo, min(default, hi))
    try:
        # Bare numeric input (int, float, or numeric string with no "S")
        if isinstance(battery, (int, float)):
            return max(lo, min(int(battery), hi))
        s = str(battery).strip()
        m = _CELL_RE.search(s)
        if m:
            return max(lo, min(int(m.group(1)), hi))
        # No "S" suffix found — try parsing the whole string as a number
        # (handles plain "4" with no suffix at all).
        return max(lo, min(int(float(s)), hi))
    except (TypeError, ValueError):
        return max(lo, min(default, hi))


def is_valid_battery_string(battery: Optional[Union[str, int, float]]) -> bool:
    """True if `battery` contains a recognizable cell count at all (used by validation)."""
    if battery is None:
        return False
    if isinstance(battery, (int, float)):
        return True
    s = str(battery).strip()
    if _CELL_RE.search(s):
        return True
    try:
        float(s)
        return True
    except (TypeError, ValueError):
        return False


__all__ = ["cells_from_battery_string", "is_valid_battery_string", "MIN_CELLS", "MAX_CELLS", "DEFAULT_CELLS"]
