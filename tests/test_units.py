# tests/test_units.py — OBIXConfig Doctor
"""
Tests for analyzer/units.py (the consolidated battery cell-count parser)
and the bugs that were found/fixed alongside it.
"""
import pytest
from analyzer.units import cells_from_battery_string, is_valid_battery_string


class TestCellsFromBatteryString:
    @pytest.mark.parametrize("s,expected", [
        ("4S", 4), ("4s", 4), ("6S", 6), ("1S", 1),
        ("4s2p", 4),          # compound notation — used to crash naive parsers
        ("6S+", 6),
        ("4S 1500mAh", 4),
        ("6S2P", 6),
        ("4", 4),             # bare number, no S suffix
        (6, 6), (6.0, 6),     # numeric input
    ])
    def test_parses_common_formats(self, s, expected):
        assert cells_from_battery_string(s) == expected

    @pytest.mark.parametrize("bad", [None, "", "garbage", "S", []])
    def test_falls_back_to_default_on_unparseable(self, bad):
        assert cells_from_battery_string(bad, default=4) == 4
        assert cells_from_battery_string(bad, default=6) == 6

    def test_clamps_to_range(self):
        assert cells_from_battery_string("20S", lo=1, hi=12) == 12
        assert cells_from_battery_string("0S", lo=1, hi=12) == 1

    def test_never_raises(self):
        for bad in [None, "", object(), {"a": 1}, "4s2p", "garbage", -5, 99999]:
            cells_from_battery_string(bad)  # must not raise


class TestIsValidBatteryString:
    def test_valid_strings(self):
        for s in ["4S", "6s", "4s2p", "6S+", "4S 1500mAh", "4", 4, 6.0]:
            assert is_valid_battery_string(s) is True

    def test_invalid_strings(self):
        for s in [None, "", "garbage", "S"]:
            assert is_valid_battery_string(s) is False


class TestConsistencyAcrossModules:
    """The whole point of consolidating into analyzer/units.py: every module
    that needs a cell count from a battery string must now agree."""

    def test_all_modules_agree_on_compound_notation(self):
        from logic.presets import _pick_baseline_key
        from analyzer.thrust_logic import estimate_battery_runtime

        # "6s2p" must be read as 6 cells everywhere — before the fix,
        # logic/presets.py's naive parser would silently fall back to a
        # default of 4 here instead.
        assert cells_from_battery_string("6s2p") == 6
        # freestyle + 6 cells should route to the explicit "freestyle_6s"
        # validated baseline, not silently stay on the plain "freestyle" (4S) one
        assert _pick_baseline_key("freestyle", "6s2p") == "freestyle_6s"


class TestThrustWeightFallbackIsPhysical:
    """calculate_thrust_weight's fallback used to compute TWR from a 0-6
    motor_load *score* with no real units — physically meaningless."""

    def test_uses_real_thrust_data_when_available(self):
        from analyzer.thrust_logic import calculate_thrust_weight
        # 4 motors x 300g max thrust each, 600g AUW -> TWR should be exactly 2.0
        twr = calculate_thrust_weight(motor_load=3, weight=600,
                                       max_thrust_per_motor_g=300, motor_count=4)
        assert twr == 2.0

    def test_falls_back_to_score_estimate_without_thrust_data(self):
        from analyzer.thrust_logic import calculate_thrust_weight
        twr = calculate_thrust_weight(motor_load=6, weight=600)
        assert twr == 3.0  # (6/6)*3.0, unchanged legacy placeholder behavior

    def test_never_raises_on_bad_input(self):
        from analyzer.thrust_logic import calculate_thrust_weight
        assert calculate_thrust_weight(None, 0) == 0.0
        assert calculate_thrust_weight("x", "y") == 0.0
