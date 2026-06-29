# affiliate/__init__.py — OBIXConfig Doctor extension layer
#
# This package is the "FPV Affiliate Gear" UI/recommendation layer.
# It is intentionally isolated from analyzer/ and logic/: it never imports
# from, and is never imported by, anything under analyzer/* or logic/*.
# It only reads the *output* of those systems (drone_class, style, size —
# plain strings/numbers passed in from app.py) to decide which catalog
# entries to surface. Deleting this whole package removes the feature
# with zero impact on PID/motor-prop/blackbox analysis.
