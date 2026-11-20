#!/usr/bin/env bash
# 复用本机 XeLaTeX；仅在缺少运行副本时从项目内工具包解包，不联网。
set -euo pipefail
proposal_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
workspace_dir="$(cd "$proposal_dir/../.." && pwd)"
proposal_package_dir="$workspace_dir/.codex-tmp/proposal_latex_20261119"
proposal_tools="${XDG_DATA_HOME:-$HOME/.local/share}/tongji-proposal-20261119"
proposal_engine="$proposal_tools/.TinyTeX/bin/x86_64-linux/xelatex"
if [ ! -f "$proposal_tools/.ready" ]; then
  proposal_archive="$proposal_package_dir/tools/TinyTeX-1-complete.tar.xz"
  if [ ! -f "$proposal_archive" ]; then
    printf 'Local TinyTeX archive not found: %s\nSee PROPOSAL_WORD.md.\n' "$proposal_archive" >&2
    exit 1
  fi
  mkdir -p "$proposal_tools/texmf-home"
  tar -xJf "$proposal_archive" -C "$proposal_tools"
  for proposal_package in "$proposal_package_dir"/extra_packages/*.tar.xz; do
    tar -xJf "$proposal_package" -C "$proposal_tools/texmf-home"
  done
  cat > "$proposal_tools/fonts.conf" <<EOF
<?xml version="1.0"?>
<!DOCTYPE fontconfig SYSTEM "urn:fontconfig:fonts.dtd">
<fontconfig>
  <dir>/mnt/c/Windows/Fonts</dir>
  <cachedir>$proposal_tools/font-cache</cachedir>
</fontconfig>
EOF
  "$proposal_tools/.TinyTeX/bin/x86_64-linux/mktexlsr" "$proposal_tools/texmf-home"
  touch "$proposal_tools/.ready"
fi
export PATH="$(dirname "$proposal_engine"):$PATH"
export TEXMFHOME="$proposal_tools/texmf-home"
export TEXMFVAR="$proposal_tools/texmf-var"
export TEXMFCONFIG="$proposal_tools/texmf-config"
export OSFONTDIR=/mnt/c/Windows/Fonts
export XDG_CACHE_HOME="$proposal_tools/cache"
export FONTCONFIG_FILE="$proposal_tools/fonts.conf"
export TEXINPUTS="./style//:./chapters//:./figures//:${TEXINPUTS:-}"
cd "$proposal_dir"
proposal_source="${1:-proposal.tex}"
for proposal_pass in 1 2; do
  "$proposal_engine" -no-shell-escape -interaction=nonstopmode -halt-on-error "$proposal_source"
done
