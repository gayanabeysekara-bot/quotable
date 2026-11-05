#!/usr/bin/env bash
# Runs every automated suite that does not need a browser stack.
# Set ZG_TEST_DATABASE_URL to run backend tests against PostgreSQL (default: SQLite).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PY="${PYTHON:-python}"
echo "== vision + backend (pytest) =="; (cd "$ROOT/backend" && $PY -m pytest -q)
echo "== edge agent (pytest) =="; (cd "$ROOT/edge_agent" && $PY -m pytest -q tests)
echo "== evaluation metrics (pytest) =="; (cd "$ROOT" && $PY -m pytest -q evaluation/tests)
echo "== frontend (tsc + vitest) =="; (cd "$ROOT/frontend" && npx tsc --noEmit && npx vitest run)
echo "All suites passed. For the browser E2E test see README → Testing."
