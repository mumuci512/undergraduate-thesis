#!/bin/bash
set -euo pipefail
cd /home/ysheng4/research/GSMF-RS-DIL
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2
p=/home/ysheng4/miniconda3/envs/GSMF_RS_DIL/bin/python
run=experiments/road_fog_severity/eval-final-seed0-20261109-182100
trained=experiments/road_clear_to_fog/formal-seed0-20261108-resume01
for stage in source ft gsmf; do
  if [ "$stage" = source ]; then ck="$trained/source/iter_60000.pth"; else ck="$trained/$stage/iter_4000.pth"; fi
  set +e
  "$p" tools/road/run.py eval --stage "$stage" --domain A --checkpoint "$ck" --manifests "$run/precheck/manifests" --work-dir "$run/precheck/$stage" --debug > "$run/logs/precheck-$stage.log" 2>&1
  rc=$?
  set -e
  printf '%s\n' "$rc" > "$run/logs/precheck-$stage.exit"
  if [ "$rc" -ne 0 ]; then exit "$rc"; fi
done
