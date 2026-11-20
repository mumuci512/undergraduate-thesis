#!/bin/bash
cd /home/ysheng4/research/GSMF-RS-DIL
p=experiments/road_clear_fog_rain/prepare-seed0-20261110-180543
/home/ysheng4/miniconda3/envs/GSMF_RS_DIL/bin/python -c 'import torch; print("CUDA",torch.cuda.is_available()); assert torch.cuda.is_available(); print(torch.cuda.get_device_name(0))' > "$p/tmux-probe.log" 2>&1
rc=$?
printf '%s\n' "$rc" > "$p/tmux-probe.exit"
exit "$rc"
