#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../.."
ROAD_PYTHON="${ROAD_PYTHON:-/home/ysheng4/miniconda3/envs/GSMF_RS_DIL/bin/python}"
record="$(mktemp -d "$PWD/experiments/road_clear_to_fog/session-recovery-XXXXXXXX")"
session="road-recovery-$(date +%Y%m%d-%H%M%S)-$$"
printf '%s\n' "$session" > "$record/session.txt"
printf '%s\n' "$PWD" > "$record/cwd.txt"
launch=(bash experiments/road_clear_to_fog/recovery_session.sh "$record" "$ROAD_PYTHON" "$@")
printf -v quoted '%q ' "${launch[@]}"
printf '%s\n' "$quoted" > "$record/launch-command.sh"
tmux new-session -d -s "$session" -c "$PWD" "$quoted"
printf 'Session: %s\nSession records: %s\n' "$session" "$record"
