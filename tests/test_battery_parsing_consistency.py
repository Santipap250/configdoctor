# tests/test_battery_parsing_consistency.py — OBIXConfig Doctor
"""
Regression tests for a bug found in this pass: analyzer/thrust_logic.py,
analyzer/advanced_analysis.py, and analyzer/secret_sauce.py each had their
own hand-rolled battery/cell-count parser instead of using the shared one
in analyzer/units.py (app.py, logic/presets.py, and
analyzer/rpm_filter_calc.py had already been migrated).

Two concrete, silent bugs this caused:

1. thrust_logic._cells_from_str and secret_sauce._cells used
   `int(str(s).upper().replace("S", ""))`, which raises on any label with
   trailing info after the cell count ("6S2P", "4S 1500mAh", "6S+") and
   silently fell back to a default of 4 cells — e.g. a real 6S pack was
   treated as 4S for flight-time/power estimates and Secret Sauce CLI
   output, with no warning to the user.

2. advanced_analysis._cells_from_str used the same regex as
   analyzer.units, but clamped to a max of 8S instead of 12S. A 10S build
   (a real, supported config — the app explicitly supports up to 12S)
   got silently clamped to 8S in the flight-time/power model while every
   other part of the app used the real value of 10.

These tests assert all three modules now agree with analyzer.units (and
therefore with each other) for the label formats that used to break them.
"""
import pytest

from analyzer.units import cells_from_battery_string
from analyzer.thrust_logic import _cells_from_str as thrust_cells
from analyzer.advanced_analysis import _cells_from_str as advanced_cells
from analyzer.secret_sauce import _cells as sauce_cells


PARSERS = [thrust_cells, advanced_cells, sauce_cells]


class TestBatteryParsersAgreeWithSharedUnit:
    @pytest.mark.parametrize("label,expected", [
        ("4S", 4),
        ("6S", 6),
        ("6S2P", 6),      # used to silently become 4 in thrust_logic/secret_sauce
        ("4s2p", 4),
        ("6S+", 6),
        ("4S 1500mAh", 4),
        ("10S", 10),      # used to be clamped to 8 in advanced_analysis
        ("12S", 12),
    ])
    def test_all_parsers_match_shared_helper(self, label, expected):
        assert cells_from_battery_string(label, default=4, lo=1, hi=12) == expected
        for parser in PARSERS:
            assert parser(label) == expected, (
                f"{parser.__module__}.{parser.__name__}({label!r}) "
                f"disagreed with the shared parser"
            )

    def test_all_parsers_agree_with_each_other(self):
        for label in ["4S", "6S2P", "4s2p", "6S+", "4S 1500mAh", "10S", "12S"]:
            results = {parser(label) for parser in PARSERS}
            assert len(results) == 1, (
                f"parsers disagree on {label!r}: "
                f"{[(p.__module__, p(label)) for p in PARSERS]}"
            )

    def test_no_parser_raises_on_malformed_input(self):
        for bad in [None, "", "garbage", "S", 0, -5]:
            for parser in PARSERS:
                parser(bad)  # must not raise
