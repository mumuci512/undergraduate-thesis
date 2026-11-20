#!/usr/bin/env bash
set -euo pipefail
cd /home/ysheng4/research/segformer_b5_p1_20261117
env -u PYTHONPATH /home/ysheng4/miniconda3/envs/GSMF_RS_DIL/bin/python scripts/run_p1.py smoke > preflight.log 2>&1 || { tail -n 20 preflight.log; exit 1; }
tail -n 3 preflight.log
cat smoke.json
