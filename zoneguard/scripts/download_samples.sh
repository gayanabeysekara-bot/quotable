#!/usr/bin/env bash
# Downloads OpenCV's public pedestrian sample clip for LOCAL DEVELOPMENT ONLY.
# Its original provenance/licence is not documented by OpenCV; do not redistribute it or use it
# in marketing. Replace with your own staged, consented footage for pilots (see evaluation/README.md).
set -euo pipefail
cd "$(dirname "$0")/../samples"
[ -f vtest.avi ] || curl -fsSL -o vtest.avi https://raw.githubusercontent.com/opencv/opencv/4.x/samples/data/vtest.avi
echo "45cddc9490be69345cbdab64ca583be65987e864ca408038e648db99e10516cf  vtest.avi" | sha256sum -c -
