# tests/test_default_battery_mah_consistency.py — OBIXConfig Doctor
"""
Regression test for a bug found in this pass: analyzer/advanced_analysis.py
and analyzer/thrust_logic.py each guessed a default battery capacity (mAh)
- used only when the user leaves the mAh field blank - from two different
tables. advanced_analysis.py's table was keyed by size + cell count;
thrust_logic.py's was keyed by size only (ignoring cell count entirely).

Both run in the same request (app.py's /app and /api/analyze both call
make_advanced_report AND estimate_battery_runtime_detail back to back), so
for a 5" 6S build with no mAh entered, advanced_analysis guessed 1100 mAh
while thrust_logic guessed 1500 mAh - a 36% gap, exposed as two disagreeing
flight-time numbers (est_flight_time_min vs flight_time_detail.avg_flight_min)
in the same /api/analyze JSON response.

Both now delegate to analyzer.units.default_battery_mah, the single source
of truth. These tests guard against the two drifting apart again.
"""
import pytest

from analyzer.units import default_battery_mah
from analyzer.advanced_analysis import _guess_batt_mAh
from analyzer.thrust_logic import _default_mah_for_size


class TestDefaultBatteryMahConsistency:
    @pytest.mark.parametrize("size_inch,cells", [
        (2.5, 3), (2.5, 4),
        (3.0, 3), (3.0, 4),
        (4.0, 3), (4.0, 4),
        (5.0, 4), (5.0, 5), (5.0, 6),   # the originally-reported 5"/6S case
        (6.0, 4), (6.0, 5), (6.0, 6),
        (7.0, 5), (7.0, 6), (7.0, 7),
        (8.0, 6), (8.0, 7), (8.0, 8),
        (4.5, 4), (5.5, 4), (7.5, 6), (10.0, 6),  # thrust_logic-only sizes
    ])
    def test_both_modules_agree_with_shared_table(self, size_inch, cells):
        expected = default_battery_mah(size_inch, cells)
        assert _guess_batt_mAh(size_inch, cells) == expected
        assert _default_mah_for_size(size_inch, cells) == expected

    def test_5in_6s_no_longer_disagrees(self):
        # The exact case that exposed the bug: 5" 6S build, no mAh entered.
        advanced = _guess_batt_mAh(5.0, 6)
        thrust = _default_mah_for_size(5.0, 6)
        assert advanced == thrust == 1100

    def test_10s_no_longer_clamped_or_mismatched(self):
        advanced = _guess_batt_mAh(10.0, 10)
        thrust = _default_mah_for_size(10.0, 10)
        assert advanced == thrust
