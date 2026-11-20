#!/usr/bin/env bash
set -eu
cd /home/ysheng4/research/segformer_b5_p0_20261116
export PYTHONPATH=
out=.
py=/home/ysheng4/miniconda3/envs/GSMF_RS_DIL/bin/python
sha256sum "$out/run_b5_p0.py"
/usr/lib/wsl/lib/nvidia-smi
"$py" "$out/run_b5_p0.py" audit
"$py" "$out/run_b5_p0.py" train
"$py" "$out/run_b5_p0.py" eval
printf 'P0_EXECUTION_COMPLETE\n'
