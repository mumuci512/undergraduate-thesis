#!/bin/bash
set -u
cd /home/ysheng4/research/GSMF-RS-DIL
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 PYTHONUNBUFFERED=1
run=experiments/road_five_domain/formal-A-plan-20261111-140000
/home/ysheng4/miniconda3/envs/GSMF_RS_DIL/bin/python "$run/scripts/complete_A.py" > "$run/completion-supervisor.log" 2>&1
rc=$?
printf '%s\n' "$rc" > "$run/completion-shell.exit"
exit "$rc"
