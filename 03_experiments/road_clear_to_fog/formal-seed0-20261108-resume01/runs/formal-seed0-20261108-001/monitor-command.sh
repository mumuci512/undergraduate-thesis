#!/usr/bin/env bash
set -u
cd /home/ysheng4/research/GSMF-RS-DIL
printf '%s\n' "$$" > experiments/road_clear_to_fog/formal-seed0-20261108-001/monitor-shell.pid
OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 /home/ysheng4/miniconda3/envs/GSMF_RS_DIL/bin/python experiments/road_clear_to_fog/formal_control.py watch --run experiments/road_clear_to_fog/formal-seed0-20261108-001 --session experiments/road_clear_to_fog/session-formal-t2rn7qx2 > experiments/road_clear_to_fog/formal-seed0-20261108-001/monitor-console.log 2>&1
code=$?
printf '%s\n' "$code" > experiments/road_clear_to_fog/formal-seed0-20261108-001/monitor-shell-exit-code.txt
exit "$code"
