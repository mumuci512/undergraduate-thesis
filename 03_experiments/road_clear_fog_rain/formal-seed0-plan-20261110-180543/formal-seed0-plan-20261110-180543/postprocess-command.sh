#!/bin/bash
# Actual authorized postprocessing commands; no training/inference updates.
cd /home/ysheng4/research/GSMF-RS-DIL
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 PYTHONUNBUFFERED=1
p=/home/ysheng4/miniconda3/envs/GSMF_RS_DIL/bin/python
prep=experiments/road_clear_fog_rain/prepare-seed0-20261110-180543
run=experiments/road_clear_fog_rain/formal-seed0-plan-20261110-180543
"$p" "$run/scripts/verify_and_report.py" --prepare "$prep" --run "$run" > "$run/independent-finalize.log" 2>&1
"$p" "$run/scripts/figures.py" --prepare "$prep" --run "$run" > "$run/figures.log" 2>&1
"$p" "$run/scripts/package_handoff.py" --prepare "$prep" --run "$run" > "$run/package-handoff.log" 2>&1
