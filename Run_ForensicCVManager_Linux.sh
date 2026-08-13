#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
export FCV_PORTABLE_ROOT="$ROOT"
exec "$ROOT/Linux/ForensicCVManager"
