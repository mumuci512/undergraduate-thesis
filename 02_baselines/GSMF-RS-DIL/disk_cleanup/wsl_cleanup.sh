#!/usr/bin/env bash
# GSMF-RS-DIL 远程WSL空间清理脚本（2026-11-11）。在 home-wsl 里运行。
# 默认不删除任何东西：plan 只列清单，apply 重新生成清单并在输入 YES 后才删除。
# 完整流程见 ../REMOTE_DISK_CLEANUP_2026-11-11.md。
#
#   bash wsl_cleanup.sh scan                            查看空间占用（只读）
#   bash wsl_cleanup.sh plan  [--tier2] [--stageA]      生成待删清单并做引用检查（只读）
#   bash wsl_cleanup.sh apply [--tier2] [--stageA]      重新生成清单并与最近一次plan比对，输入 YES 后删除
#   bash wsl_cleanup.sh caches [--apply]                pip / conda 缓存（默认只看大小）
#   bash wsl_cleanup.sh export-zips <目录> [--apply]    原始zip复制到外部目录并校验SHA256；
#                                                       加 --apply 才在校验通过后删除原件
# 选项：
#   --tier2          加入第二档：已接收核验的4个正式运行的中间步（iter_4000/iter_60000保留）
#   --stageA         加入阶段A的中间步（要求阶段A status.json 已是 complete）
#   --run <相对目录> 追加其他正式运行目录（相对 experiments/，例如以后的阶段B），可重复
#   --yes            跳过 YES 确认（不建议）
set -eu

ROOT="${GSMF_ROOT:-$HOME/research/GSMF-RS-DIL}"
EXP="$ROOT/experiments"
PY="${GSMF_PY:-$HOME/miniconda3/envs/GSMF_RS_DIL/bin/python}"
CONDA_BIN="${GSMF_CONDA:-$HOME/miniconda3/bin/conda}"
LOGROOT="${CLEAN_LOG_ROOT:-$HOME/disk_cleanup_logs}"
ISPRS="$EXP/isprs-full-20261028-ucOKFM"
PREP="$EXP/road_five_domain/prepare-20261111-140000"
STAGEA_RUN="road_five_domain/formal-A-plan-20261111-140000"

# 第二档：已接收并在学校本机核验过的正式运行
TIER2_RUNS=(
  "road_clear_to_fog/formal-seed0-20261108-001"
  "road_clear_to_fog/formal-seed0-20261108-resume01"
  "road_lwf_bn/formal-seed0-plan-20261110-153000"
  "road_clear_fog_rain/formal-seed0-plan-20261110-180543"
)
# 没有终点权重、但已在别处续训完成的目录（Source 在 resume01 里续到 iter_60000）
RESUMED_ELSEWHERE=(
  "road_clear_to_fog/formal-seed0-20261108-001/source"
)
# 任何情况下都必须存在、绝不删除
MUST_KEEP=(
  "$ISPRS/base/iter_80000.pth"
  "$ISPRS/incremental/iter_10000.pth"
  "$ISPRS/conversion/iter_80000_DIL.pth"
  "$EXP/road_clear_to_fog/formal-seed0-20261108-resume01/source/iter_60000.pth"
)
ZIPS=(leftImg8bit_trainvaltest_foggy.zip rgb_anon_trainvaltest.zip leftImg8bit_trainvaltest.zip)

usage() { awk 'NR>1 && /^#/ {sub(/^# ?/, ""); print; next} NR>1 {exit}' "$0"; }

CMD="${1:-help}"
if [ $# -gt 0 ]; then shift; fi
TIER2=0; STAGEA=0; YES=0; APPLY=0; DEST=""; EXTRA_RUNS=()
while [ $# -gt 0 ]; do
  case "$1" in
    --tier2) TIER2=1 ;;
    --stageA) STAGEA=1 ;;
    --run) shift; EXTRA_RUNS+=("${1:?--run 后面要跟目录}") ;;
    --yes) YES=1 ;;
    --apply) APPLY=1 ;;
    -*) echo "未知选项：$1" >&2; exit 2 ;;
    *) DEST="$1" ;;
  esac
  shift
done

hr() { echo "------------------------------------------------------------"; }
space() { df -h / /mnt/c 2>/dev/null | sed 's/^/  /'; }
gb() { awk -v b="$1" 'BEGIN{printf "%.1f", b/1e9}'; }
gsmf_jobs() { pgrep -af '[e]nvs/GSMF_RS_DIL/bin/python' || true; }

check_keep() {
  local k missing=0
  for k in "${MUST_KEEP[@]}"; do
    if [ ! -f "$k" ]; then echo "错误：应保留的文件不存在：$k" >&2; missing=1; fi
  done
  if [ "$missing" -ne 0 ]; then echo "文件命名与11月11日核查时不一致，停止，未删除任何文件。" >&2; exit 1; fi
}

stageA_complete() {
  local s="$EXP/$STAGEA_RUN/status.json"
  [ -f "$s" ] && grep -qiE '"state"[[:space:]]*:[[:space:]]*"complete' "$s"
}

is_resumed_elsewhere() {
  local rel="${1#"$EXP"/}" r
  for r in "${RESUMED_ELSEWHERE[@]}"; do
    if [ "$rel" = "$r" ]; then return 0; fi
  done
  return 1
}

collect() {   # $1=输出目录；写 candidates.tsv（类别<TAB>字节<TAB>路径）
  local cand="$1/candidates.tsv" sub run dir
  : > "$cand"
  for sub in base incremental; do
    if [ -d "$ISPRS/$sub" ]; then
      find "$ISPRS/$sub" -maxdepth 1 -type f -regextype posix-extended -regex '.*/iter_[0-9]+\.pth' \
        -printf 'T1-isprs-intermediate\t%s\t%p\n' >> "$cand"
    fi
  done
  find "$EXP" -mindepth 3 -type f -regextype posix-extended \
    -regex '.*/experiments/road_[^/]+/(debug|synthetic|prepare)[^/]*/(.*/)?iter_[0-9]+\.pth' \
    -printf 'T1-road-debug-prepare\t%s\t%p\n' >> "$cand"
  find "$EXP" -mindepth 2 -type f -regextype posix-extended \
    -regex '.*/experiments/[^/]*smoke-20261028/(.*/)?iter_[0-9]+\.pth' \
    -printf 'T1-smoke\t%s\t%p\n' >> "$cand"
  for run in "${T2_SELECTED[@]}"; do
    case "$run" in /*|*..*) echo "跳过不安全的目录参数：$run" >&2; continue ;; esac
    if [ ! -d "$EXP/$run" ]; then echo "警告：第二档目录不存在：$run" >&2; continue; fi
    while IFS= read -r dir; do
      if [ -f "$dir/iter_4000.pth" ] || [ -f "$dir/iter_60000.pth" ] || is_resumed_elsewhere "$dir"; then
        find "$dir" -maxdepth 1 -type f -regextype posix-extended -regex '.*/iter_[0-9]+\.pth' \
          ! -name iter_4000.pth ! -name iter_60000.pth -printf 'T2-formal-intermediate\t%s\t%p\n' >> "$cand"
      else
        echo "警告：$dir 没有终点权重 iter_4000/iter_60000，可能未完成，跳过。" >&2
      fi
    done < <(find "$EXP/$run" -type f -regextype posix-extended -regex '.*/iter_[0-9]+\.pth' -printf '%h\n' | sort -u)
  done
}

protect() {   # 生成 protected.tsv（原因<TAB>路径）、delete.tsv、candidates-protected.tsv
  local d="$1" cand="$1/candidates.tsv" prot="$1/protected.tsv"
  local pat="$1/patterns.txt" deps="$1/dep-files.txt" k f x sub m
  : > "$prot"
  for k in "${MUST_KEEP[@]}"; do printf 'must-keep\t%s\n' "$k" >> "$prot"; done
  # 1) 阶段B/C计划与READY里出现的全部 .pth
  for f in "$PREP/formal-plans.json" "$PREP/READY.json"; do
    if [ -f "$f" ]; then
      grep -oE '[^"[:space:]]+\.pth' "$f" | sort -u | while IFS= read -r m; do
        case "$m" in /*) printf 'plan-ref\t%s\n' "$m" ;; *) printf 'plan-ref\t%s/%s\n' "$ROOT" "$m" ;; esac
      done >> "$prot" || true
    fi
  done
  # 2) 源码、配置、各运行 scripts/ 里出现的候选路径（绝对或相对路径）
  : > "$deps"
  for x in "$ROOT/tools" "$ROOT/road_dil" "$ROOT/configs"; do
    if [ -d "$x" ]; then
      find "$x" -type f \( -name '*.py' -o -name '*.sh' -o -name '*.json' -o -name '*.yaml' -o -name '*.yml' -o -name '*.txt' \) >> "$deps"
    fi
  done
  find "$EXP/road_five_domain" -type f -path '*/scripts/*' >> "$deps" 2>/dev/null || true
  for f in "$PREP/formal-plans.json" "$PREP/READY.json"; do
    if [ -f "$f" ]; then echo "$f" >> "$deps"; fi
  done
  cut -f3 "$cand" | while IFS= read -r m; do
    printf '%s\n%s\n%s\n' "$m" "${m#"$ROOT"/}" "${m#"$EXP"/}"
  done | sort -u > "$pat"
  if [ -s "$pat" ] && [ -s "$deps" ]; then
    tr '\n' '\0' < "$deps" | xargs -0 -r grep -hoF -f "$pat" 2>/dev/null | sort -u | while IFS= read -r m; do
      case "$m" in
        /*) printf 'referenced\t%s\n' "$m" ;;
        *) printf 'referenced\t%s/%s\nreferenced\t%s/%s\n' "$ROOT" "$m" "$EXP" "$m" ;;
      esac
    done >> "$prot" || true
  fi
  # 3) 正在被进程打开的 .pth
  find /proc/[0-9]*/fd -maxdepth 1 -type l -printf '%l\n' 2>/dev/null | grep -E '\.pth$' | sort -u \
    | sed 's/^/open-by-process\t/' >> "$prot" || true
  # 4) ISPRS 的 last_checkpoint 指向
  for sub in base incremental; do
    if [ -f "$ISPRS/$sub/last_checkpoint" ]; then
      printf 'last_checkpoint\t%s\n' "$(tr -d '\n' < "$ISPRS/$sub/last_checkpoint")" >> "$prot"
    fi
  done
  awk -F'\t' 'NR==FNR {keep[$2]=$1; next} !($3 in keep)' "$prot" "$cand" > "$d/delete.tsv"
  awk -F'\t' 'NR==FNR {keep[$2]=$1; next} ($3 in keep) {print keep[$3] "\t" $0}' "$prot" "$cand" > "$d/candidates-protected.tsv"
}

summary() {
  local d="$1"
  echo "将删除（按类别）："
  awk -F'\t' '{n[$1]++; s[$1]+=$2} END{for(k in n) printf "  %-24s %5d 个  %7.1f GB\n", k, n[k], s[k]/1e9}' "$d/delete.tsv" | sort
  awk -F'\t' '{n++; s+=$2} END{printf "  合计 %d 个文件，%.1f GB\n", n, s/1e9}' "$d/delete.tsv"
  if [ -s "$d/candidates-protected.tsv" ]; then
    echo "符合规则但被保护、不会删除："
    awk -F'\t' '{printf "  [%s] %s (%.1f GB)\n", $1, $4, $3/1e9}' "$d/candidates-protected.tsv"
  fi
  echo "按目录（前30）："
  awk -F'\t' '{p=$3; sub(/\/[^\/]+$/, "", p); sub(/.*\/experiments\//, "", p); n[p]++; s[p]+=$2}
    END{for(k in n) printf "%7.1f GB %4d  %s\n", s[k]/1e9, n[k], k}' "$d/delete.tsv" | sort -rn | head -30 | sed 's/^/  /'
}

do_apply() {
  local d="$1" n total ans cat size path
  n=$(wc -l < "$d/delete.tsv")
  total=$(awk -F'\t' '{s+=$2} END{printf "%.1f", s/1e9}' "$d/delete.tsv")
  if [ "$n" -eq 0 ]; then echo "没有需要删除的文件。"; return 0; fi
  if [ "$YES" -ne 1 ]; then
    if [ ! -t 0 ]; then echo "当前不是交互终端，未删除。请在终端里直接运行（或加 --yes）。" >&2; exit 1; fi
    read -r -p "确认删除以上 $n 个文件（$total GB）？输入 YES 继续：" ans
    if [ "$ans" != "YES" ]; then echo "已取消，未删除任何文件。"; exit 0; fi
  fi
  : > "$d/deleted.tsv"
  while IFS=$'\t' read -r cat size path; do
    if [ -f "$path" ]; then
      if rm -f -- "$path"; then
        printf '%s\t%s\t%s\t%s\n' "$(date -Is)" "$cat" "$size" "$path" >> "$d/deleted.tsv"
      else
        echo "删除失败：$path" >&2
      fi
    fi
  done < "$d/delete.tsv"
  echo "已删除 $(wc -l < "$d/deleted.tsv") 个文件，删除记录：$d/deleted.tsv"
}

compare_with_plan() {   # 把本次 apply 清单与最近一次 plan 的清单逐个路径比对
  local d="$1" last added removed
  last=$(ls -d "$LOGROOT"/*-plan 2>/dev/null | sort | tail -1 || true)
  if [ -z "$last" ] || [ ! -f "$last/delete.tsv" ]; then
    echo "没有找到之前的 plan 记录，无法比对（建议先运行 plan）。"; return 0
  fi
  cut -f3 "$last/delete.tsv" | sort > "$d/last-plan-paths.txt"
  cut -f3 "$d/delete.tsv" | sort > "$d/apply-paths.txt"
  added=$(comm -13 "$d/last-plan-paths.txt" "$d/apply-paths.txt" | wc -l)
  removed=$(comm -23 "$d/last-plan-paths.txt" "$d/apply-paths.txt" | wc -l)
  if [ "$added" -eq 0 ] && [ "$removed" -eq 0 ]; then
    echo "与上次预览 $last 的清单完全一致。"
  else
    echo "注意：与上次预览 $last 不一致：多出 $added 个，少了 $removed 个（多出的前20个如下）。"
    comm -13 "$d/last-plan-paths.txt" "$d/apply-paths.txt" | head -20 | sed 's/^/  + /'
    echo "如果参数和预览时不同，请按 Ctrl+C 或输入 NO 取消，改用相同参数。"
  fi
}

do_scan() {
  echo "磁盘（真实剩余空间看 /mnt/c 这一行，/ 这一行是虚拟盘上限）："; space
  hr; echo "家目录："; du -xh --max-depth=1 "$HOME" 2>/dev/null | sort -rh | head -8 | sed 's/^/  /'
  hr; echo "experiments："; du -xh --max-depth=1 "$EXP" 2>/dev/null | sort -rh | head -12 | sed 's/^/  /'
  hr; echo "data："; du -xh --max-depth=1 "$ROOT/data" 2>/dev/null | sort -rh | head -10 | sed 's/^/  /'
  hr; echo "周期checkpoint按目录（前25）："
  find "$EXP" -type f -name 'iter_*.pth' -printf '%h\t%s\n' \
    | awk -F'\t' '{p=$1; sub(/.*\/experiments\//, "", p); n[p]++; s[p]+=$2} END{for(k in n) printf "%7.1f GB %4d  %s\n", s[k]/1e9, n[k], k}' \
    | sort -rn | head -25 | sed 's/^/  /'
  hr; echo "原始zip："
  for z in "$ROOT"/data/road_raw/*.zip; do
    if [ -f "$z" ]; then printf '  %6s GB  %s\n' "$(gb "$(stat -c %s "$z")")" "$z"; fi
  done
  echo "缓存："; du -sh "$HOME/.cache/pip" "$HOME/miniconda3/pkgs" 2>/dev/null | sed 's/^/  /' || true
}

do_caches() {
  echo "缓存占用："; du -sh "$HOME/.cache/pip" "$HOME/miniconda3/pkgs" 2>/dev/null | sed 's/^/  /' || true
  if [ "$APPLY" -ne 1 ]; then echo "预览模式；加 --apply 才会执行 pip cache purge 和 conda clean --all -y。"; return 0; fi
  "$PY" -m pip cache purge || echo "pip cache purge 失败，可改用：rm -rf ~/.cache/pip"
  "$CONDA_BIN" clean --all -y || echo "conda clean 失败"
  du -sh "$HOME/.cache/pip" "$HOME/miniconda3/pkgs" 2>/dev/null | sed 's/^/  /' || true
}

do_export() {
  local real need=0 avail z src dst hs hd rec="$ROOT/data/road_raw/MOVED_ZIPS.tsv"
  if [ -z "$DEST" ]; then echo "用法：bash wsl_cleanup.sh export-zips <目标目录> [--apply]" >&2; exit 2; fi
  if [ ! -d "$DEST" ] || [ ! -w "$DEST" ]; then echo "目标目录不存在或不可写：$DEST" >&2; exit 1; fi
  real=$(readlink -f "$DEST")
  case "$real" in
    /mnt/c|/mnt/c/*) echo "目标在C盘（/mnt/c）上，移过去腾不出C盘空间。请用外置盘或其他机器。" >&2; exit 1 ;;
  esac
  if [ "$(stat -c %d "$real")" = "$(stat -c %d "$ROOT/data/road_raw")" ]; then
    echo "目标和原文件在同一个文件系统（WSL虚拟盘）里，移动无效。" >&2; exit 1
  fi
  for z in "${ZIPS[@]}"; do
    if [ -f "$ROOT/data/road_raw/$z" ]; then need=$((need + $(stat -c %s "$ROOT/data/road_raw/$z"))); fi
  done
  avail=$(df -B1 --output=avail "$real" | tail -1 | tr -d ' ')
  echo "需要 $(gb "$need") GB，目标可用 $(gb "$avail") GB"
  if [ "$avail" -le $((need + 1000000000)) ]; then echo "目标空间不足。" >&2; exit 1; fi
  for z in "${ZIPS[@]}"; do
    src="$ROOT/data/road_raw/$z"; dst="$real/$z"
    if [ ! -f "$src" ]; then echo "跳过（不存在，可能已移走）：$z"; continue; fi
    if [ -f "$dst" ] && [ "$(stat -c %s "$dst")" = "$(stat -c %s "$src")" ]; then
      echo "目标已有同样大小的文件，跳过复制：$z"
    else
      echo "复制 $z（$(gb "$(stat -c %s "$src")") GB）..."
      cp -- "$src" "$dst.partial"
      mv -- "$dst.partial" "$dst"
    fi
    echo "校验 SHA256：$z ..."
    hs=$(sha256sum -- "$src" | cut -d' ' -f1)
    hd=$(sha256sum -- "$dst" | cut -d' ' -f1)
    if [ "$hs" != "$hd" ]; then echo "SHA256不一致，保留原件：$z" >&2; continue; fi
    printf '%s  %s\n' "$hs" "$z" >> "$real/SHA256SUMS"
    printf '%s\t%s\t%s\t%s\t%s\n' "$(date -Is)" "$z" "$(stat -c %s "$src")" "$hs" "$dst" >> "$rec"
    if [ "$APPLY" -eq 1 ]; then
      rm -f -- "$src"; echo "已校验并删除原件：$z（去向记录在 $rec）"
    else
      echo "已校验，原件保留（加 --apply 才删除）：$z"
    fi
  done
}

case "$CMD" in
  scan) do_scan ;;
  plan|apply)
    T2_SELECTED=()
    if [ "$TIER2" -eq 1 ]; then T2_SELECTED+=("${TIER2_RUNS[@]}"); fi
    if [ "$STAGEA" -eq 1 ]; then
      if stageA_complete; then T2_SELECTED+=("$STAGEA_RUN")
      else echo "阶段A的 status.json 还不是 complete，不能清理阶段A的中间步。" >&2; exit 1; fi
    fi
    if [ "${#EXTRA_RUNS[@]}" -gt 0 ]; then T2_SELECTED+=("${EXTRA_RUNS[@]}"); fi
    check_keep
    OUT="$LOGROOT/$(date +%Y%m%d-%H%M%S)-$CMD"
    mkdir -p "$OUT"
    echo "当前空间："; space
    if [ -n "$(gsmf_jobs)" ]; then
      echo "注意：有GSMF训练/评价进程在运行（它们打开的文件会被自动保护）："
      gsmf_jobs | cut -c1-160 | sed 's/^/  /'
    fi
    hr
    collect "$OUT"
    protect "$OUT"
    summary "$OUT"
    hr
    echo "清单与记录：$OUT"
    if [ "$CMD" = apply ]; then
      compare_with_plan "$OUT"
      do_apply "$OUT"
      echo "删除后："; space
      echo "提示：WSL里已经释放了空间，但C盘可用空间要等压缩虚拟盘（compact_wsl_vhdx.ps1）之后才会增加。"
    else
      echo "以上只是预览，没有删除任何文件。确认无误后，把 plan 换成 apply 再运行一次。"
    fi
    ;;
  caches) do_caches ;;
  export-zips) do_export ;;
  *) usage ;;
esac
