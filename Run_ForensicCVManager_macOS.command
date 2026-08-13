#!/bin/bash
set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"
export FCV_PORTABLE_ROOT="$ROOT"
open "$ROOT/macOS/ForensicCVManager.app"
