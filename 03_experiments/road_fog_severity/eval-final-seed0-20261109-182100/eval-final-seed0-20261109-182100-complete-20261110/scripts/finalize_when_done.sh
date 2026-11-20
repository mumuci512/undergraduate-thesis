#!/bin/bash
set -u
cd /home/ysheng4/research/GSMF-RS-DIL
run=experiments/road_fog_severity/eval-final-seed0-20261109-182100
while [ ! -f "$run/acquisition-20261110/driver.exit" ]; do sleep 15; done
if [ "$(cat "$run/acquisition-20261110/driver.exit")" != 0 ]; then
  printf '%s\n' 'driver failed; no finalization attempted' > "$run/acquisition-20261110/finalizer.exit"
  exit 1
fi
/home/ysheng4/miniconda3/envs/GSMF_RS_DIL/bin/python -u "$run/scripts/finalize.py" > "$run/acquisition-20261110/finalizer.log" 2>&1
rc=$?
printf '%s\n' "$rc" > "$run/acquisition-20261110/finalizer.exit"
if [ "$rc" -ne 0 ]; then
  printf '\n最终独立复核或打包失败；查看 `acquisition-20261110/finalizer.log`，请勿标记完成。\n' >> "$run/STATUS.md"
fi
exit "$rc"
