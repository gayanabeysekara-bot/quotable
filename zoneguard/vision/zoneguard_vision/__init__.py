"""ZoneGuard AI shared computer-vision pipeline.

This package is used by both the cloud API (for uploaded staged video analysis)
and the edge agent (for live RTSP processing on the customer's network).

Design constraints (see docs/SECURITY_PRIVACY.md):
* No facial recognition, no biometric templates, no persistent identity.
* Track IDs are anonymous, short-lived and local to a single camera view.
* Experimental / simulated detectors are always labelled as such in their output.
"""

__version__ = "0.1.0"
