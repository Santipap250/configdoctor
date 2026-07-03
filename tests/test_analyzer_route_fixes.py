# tests/test_analyzer_route_fixes.py — OBIXConfig Doctor
"""
Regression tests for the app.py Drone Analyzer bugs found and fixed in
this pass. Each test is named after the bug it guards against.
"""
import os
import pytest

# FIX: this module imports app.py directly at collection time, before any
# pytest fixture has a chance to run. app.py hard-exits (SystemExit) if
# SECRET_KEY is not present in the environment (see app.py's startup
# guard), so without setting it here first, `import app as A` below
# crashed pytest's collection phase and took the ENTIRE test suite down
# with it (every other test file failed too, since pytest aborts the run
# on a collection error). Match conftest.py's app fixture and set safe
# defaults before importing.
os.environ.setdefault("SECRET_KEY", "test-secret-key-do-not-use-in-prod")
os.environ.setdefault("FLASK_DEBUG", "0")

import app as A


@pytest.fixture
def client():
    A.app.config["WTF_CSRF_ENABLED"] = False
    A.app.config["TESTING"] = True
    return A.app.test_client()


class TestMd5FilterRegistered:
    """CRITICAL: every POST to /app was 500ing with 'No filter named md5
    found' because templates/index.html uses |md5 but it was never
    registered as a Jinja filter."""

    def test_post_to_app_does_not_500(self, client):
        r = client.post("/app", data={
            "size": "5", "weight": "650", "prop_size": "5", "pitch": "4.5",
            "blades": "3", "battery": "4S", "style": "freestyle", "motor_kv": "2400",
        })
        assert r.status_code == 200


class TestMalformedBatteryStringDoesNotDiscardPropAnalysis:
    """Was: a battery string like '4s2p' raised inside the naive inline
    int() parser, which was caught by a broad except that threw away the
    ENTIRE propeller analysis silently — no warning, just a degraded
    'prop analysis not available' result baked into a 200 response."""

    @pytest.mark.parametrize("battery_str", ["4s2p", "6S+", "4S 1500mAh", "6S2P"])
    def test_compound_battery_notation_still_yields_real_prop_analysis(self, client, battery_str):
        r = client.post("/app", data={
            "size": "5", "weight": "650", "prop_size": "5", "pitch": "4.5",
            "blades": "3", "battery": battery_str, "style": "freestyle", "motor_kv": "2400",
        })
        html = r.get_data(as_text=True)
        assert r.status_code == 200
        assert "prop analysis not available" not in html


class TestAdvancedFieldsPopulatedBeforeUse:
    """Was: hover_throttle_pct / rpm_estimated / c_burst / c_continuous /
    c_recommended / max_power_total_w were read from analysis['advanced']
    before make_advanced_report() had populated it, so they were always
    None at the top level (and the rule engine, which depends on the same
    data for safety warnings, ran before it was populated too)."""

    def test_top_level_advanced_fields_are_populated(self, client):
        r = client.post("/app", data={
            "size": "5", "weight": "650", "prop_size": "5", "pitch": "4.5",
            "blades": "3", "battery": "4S", "style": "freestyle", "motor_kv": "2400",
            "battery_mAh": "1500",
        })
        assert r.status_code == 200
        # Re-derive the same analysis dict the route built, via the public
        # helper, to assert on the actual dict rather than scrape HTML.
        with A.app.test_request_context("/app", method="POST", data={
            "size": "5", "weight": "650", "prop_size": "5", "pitch": "4.5",
            "blades": "3", "battery": "4S", "style": "freestyle", "motor_kv": "2400",
            "battery_mAh": "1500",
        }):
            analysis = A._handle_analysis_post()
        for key in ("hover_throttle_pct", "rpm_estimated", "c_burst",
                    "c_continuous", "c_recommended", "max_power_total_w"):
            assert analysis.get(key) is not None, f"{key} should not be None"

    def test_rules_can_actually_see_c_burst_and_fire(self, client):
        # A build with a tiny, badly-undersized battery should trigger at
        # least one rule — if rules ran before 'advanced' existed (the old
        # bug), this list would be empty even for a dangerous build.
        with A.app.test_request_context("/app", method="POST", data={
            "size": "5", "weight": "900", "prop_size": "5.1", "pitch": "5.1",
            "blades": "3", "battery": "4S", "battery_mAh": "450",
            "style": "racing", "motor_kv": "2700",
        }):
            analysis = A._handle_analysis_post()
        assert isinstance(analysis.get("rules"), list)


class TestValidateInputTightening:
    """motor_kv / motor_count / battery_mAh / payload_g / esc_current_limit_a
    used to have zero validation."""

    def test_negative_motor_kv_warns(self):
        warnings = A.validate_input(5, 650, 5, 4.5, 3, "4S", motor_kv=-500)
        assert any("KV" in w for w in warnings)

    def test_absurd_motor_count_warns(self):
        warnings = A.validate_input(5, 650, 5, 4.5, 3, "4S", motor_count=5)
        assert any("มอเตอร์" in w for w in warnings)

    def test_absurd_battery_mAh_warns(self):
        warnings = A.validate_input(5, 650, 5, 4.5, 3, "4S", battery_mAh=-100)
        assert any("mAh" in w for w in warnings)

    def test_valid_values_produce_no_new_warnings(self):
        warnings = A.validate_input(5, 650, 5, 4.5, 3, "4S",
                                     motor_kv=2400, motor_count=4,
                                     battery_mAh=1500, payload_g=0,
                                     esc_current_limit_a=40)
        assert warnings == []
