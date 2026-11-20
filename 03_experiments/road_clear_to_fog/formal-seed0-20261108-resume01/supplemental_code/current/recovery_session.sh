#!/usr/bin/env bash
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
record="$1"; road_python="$2"; shift 2
printf '%s\n' "$$" > "$record/pid.txt"
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 PYTHONUNBUFFERED=1 "$road_python" experiments/road_clear_to_fog/recovery_pipeline.py "$@" > "$record/console.log" 2>&1
code=$?
printf '%s\n' "$code" > "$record/exit-code.txt"
exit "$code"
