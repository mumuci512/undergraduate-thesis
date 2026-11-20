#!/usr/bin/env bash
set -euo pipefail
cd /home/ysheng4/research/segformer_b5_p1_20261117
nohup bash -c 'env -u PYTHONPATH /home/ysheng4/miniconda3/envs/GSMF_RS_DIL/bin/python -u scripts/run_p1.py run > execution.log 2>&1; code=$?; printf "%s\n" "$code" > exit_code.txt' < /dev/null > launcher.log 2>&1 &
printf '%s\n' "$!" > launcher.pid
cat launcher.pid
