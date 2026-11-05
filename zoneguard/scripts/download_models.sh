#!/usr/bin/env bash
# Downloads the official YOLOX ONNX release weights (Apache-2.0) and verifies SHA-256.
set -euo pipefail
cd "$(dirname "$0")/../models"
BASE=https://github.com/Megvii-BaseDetection/YOLOX/releases/download/0.1.1rc0
declare -A SUMS=(
  [yolox_nano.onnx]=c789161ed43c8269fcd4e67c67eeeb4e80c622da2eb296a20bc6007bd18a0b7d
  [yolox_tiny.onnx]=427cc366d34e27ff7a03e2899b5e3671425c262ea2291f88bb942bc1cc70b0f7
  [yolox_s.onnx]=c5c2d13e59ae883e6af3b45daea64af4833a4951c92d116ec270d9ddbe998063
)
for f in "${!SUMS[@]}"; do
  if [ ! -f "$f" ]; then
    echo "downloading $f"; curl -fsSL -o "$f.part" "$BASE/$f"; mv "$f.part" "$f"
  fi
  echo "${SUMS[$f]}  $f" | sha256sum -c -
done
