#!/bin/bash
set -euo pipefail
cd /home/ysheng4/research/GSMF-RS-DIL
run=experiments/road_lwf_bn/formal-seed0-plan-20261110-153000
p=/home/ysheng4/miniconda3/envs/GSMF_RS_DIL/bin/python
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 PYTHONUNBUFFERED=1 MPLCONFIGDIR=/tmp/road-lwf-bn-matplotlib
mkdir -p "$MPLCONFIGDIR"
trap 'rc=$?; echo "$rc" > "$run/postprocess.exit"' EXIT
# A concrete persistent monitor. No restarts; stops if training pipeline fails.
while [ ! -f "$run/exit-code.txt" ]; do
 date -Iseconds > "$run/monitor-last-check.txt"
 if [ -f "$run/status.json" ]; then cat "$run/status.json" > "$run/monitor-stage.json"; fi
 if ! tmux has-session -t road-lwf-bn-20261110-160913 2>/dev/null; then
  echo 'Training session ended without pipeline exit-code; preserve scene and stop.' >&2; exit 1
 fi
 sleep 20
done
[ "$(cat "$run/exit-code.txt")" = 0 ] || { echo 'Training/evaluation pipeline failed; no postprocessing' >&2; exit 1; }
"$p" "$run/scripts/finalize_results.py" --run "$run" > "$run/independent-finalize.log" 2>&1
"$p" "$run/scripts/package_handoff.py" --run "$run" > "$run/package-handoff.log" 2>&1
