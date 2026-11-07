#!/bin/bash
# Render every episode in order; logs to out/render.log
cd "$(dirname "$0")/.." && for e in ep1 ep2 ep3 ep4 ep5 ep6 ep7; do node tools/render.js $e --workers 4 || echo "FAILED $e"; done
