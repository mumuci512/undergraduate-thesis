#!/bin/bash
# Run from a tmux session on a CUDA-capable host after an audit and prepare_eval.py.
# Fails on any existing cell; no automatic skip or overwrite.
set -euo pipefail
if [ "$#" -ne 3 ]; then echo 'usage: evaluate.sh PREPARED_DIR AUDIT_DIR NEW_OUTPUT_DIR' >&2; exit 2; fi
prepared=$(realpath "$1"); audit=$(realpath "$2"); output=$(realpath -m "$3")
root=/home/ysheng4/research/GSMF-RS-DIL
p=/home/ysheng4/miniconda3/envs/GSMF_RS_DIL/bin/python
trained=$root/experiments/road_clear_to_fog/formal-seed0-20261108-resume01
cd "$root"
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2
[ ! -e "$output" ] || { echo 'output exists; refusing to overwrite' >&2; exit 1; }
"$p" -c 'import torch; assert torch.cuda.is_available(), "CUDA unavailable; no CPU fallback"'
printf '%s  %s\n%s  %s\n%s  %s\n' \
 a66c958ee774d27566b901ad6570c0a3b83263e9d74389e1c2e025c6c2673d93 "$trained/source/iter_60000.pth" \
 99914df527d8506c33178ef6ea1caf7f0ed1d07369858e37275205d60a57d516 "$trained/ft/iter_4000.pth" \
 fc227c57dc3e47a134ef51b282964654a0210f3c06f00bd0d3e81b706850b24a "$trained/gsmf/iter_4000.pth" | sha256sum -c -
"$p" "$(dirname "$0")/verify_inputs.py" "$prepared" "$audit"
mkdir -p "$output/logs"
printf '%q ' "$0" "$@" > "$output/command.txt"; printf '\n' >> "$output/command.txt"
for phase in precheck full; do
 for stage in source ft gsmf; do
  if [ "$stage" = source ]; then ck=$trained/source/iter_60000.pth; else ck=$trained/$stage/iter_4000.pth; fi
  for beta in 0 0.005 0.01 0.02; do
   dir=$output/$phase/$stage/$beta
   mkdir -p "$(dirname "$dir")"
   log=$output/logs/$phase-$stage-$beta.log
   set +e
   "$p" tools/road/run.py eval --stage "$stage" --domain A --checkpoint "$ck" --manifests "$prepared/$phase/$beta" --work-dir "$dir" --debug > "$log" 2>&1
   rc=$?
   set -e
   printf '%s\n' "$rc" > "$output/logs/$phase-$stage-$beta.exit"
   if [ "$rc" -ne 0 ]; then echo "FAILED $phase $stage $beta; see $log" >&2; exit "$rc"; fi
   printf '%s\n' "$rc" > "$dir/exit-code.txt"
  done
 done
done
"$p" "$(dirname "$0")/aggregate.py" --prepared "$prepared" --audit "$audit" --runs "$output/full" --out "$output/results"
