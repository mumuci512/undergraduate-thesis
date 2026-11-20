#!/bin/bash
set -u
cd /home/ysheng4/research/GSMF-RS-DIL
p=experiments/road_five_domain/prepare-20261111-140000
printf 'persistent tmux probe; no training\n' > "$p/tmux-probe.log"
ps -o pid,ppid,comm -p $$ >> "$p/tmux-probe.log"
printf '0\n' > "$p/tmux-probe.exit"
