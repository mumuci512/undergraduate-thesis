#!/usr/bin/env bash
set -euo pipefail
cd /home/ysheng4/research/segformer_b5_p1_20261117
nohup bash scripts/finalize_after_training.sh < /dev/null > finalizer_launcher.log 2>&1 &
printf '%s\n' "$!" > finalizer.pid
for attempt in $(seq 1 50); do
    if test -f finish_waiting.ready; then
        cat finalizer.pid
        exit 0
    fi
    sleep 0.1
done
exit 1
