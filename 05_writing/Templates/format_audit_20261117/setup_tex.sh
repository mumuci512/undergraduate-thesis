#!/usr/bin/env bash
set -e
audit_dir=/mnt/c/undergraduate_thesis/05_writing/Templates/format_audit_20261117
export PATH="$audit_dir/tools-full/.TinyTeX/bin/x86_64-linux:$PATH"
export TEXMFHOME="$audit_dir/texmf-home"
export TEXMFVAR="$audit_dir/texmf-var"
export TEXMFCONFIG="$audit_dir/texmf-config"
tlmgr --repository https://mirrors.ustc.edu.cn/CTAN/systems/texlive/tlnet update --self
tlmgr option docfiles 0
tlmgr option srcfiles 0
tlmgr --repository https://mirrors.ustc.edu.cn/CTAN/systems/texlive/tlnet install xetex ctex newtx biblatex-gb7714-2015 fancyhdr lastpage eso-pic emptypage setspace enumitem alphalph circledsteps pict2e haranoaji ulem hologo tocloft amsmath amscls amsfonts was chngcntr multirow booktabs threeparttable threeparttablex caption algorithms algorithmicx listings fvextra tcolorbox cleveref siunitx pgf
