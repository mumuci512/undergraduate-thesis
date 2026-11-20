#!/usr/bin/env bash
set -e
audit_dir=/mnt/c/undergraduate_thesis/05_writing/Templates/format_audit_20261117
export PATH="$audit_dir/tools-full/.TinyTeX/bin/x86_64-linux:$PATH"
export TEXMFHOME="$audit_dir/texmf-home"
export TEXMFVAR="$audit_dir/texmf-var"
export TEXMFCONFIG="$audit_dir/texmf-config"
export TEXINPUTS="./style//:./chapters//:./figures//:"
cd "$audit_dir/TongjiThesis"
mktexlsr
xelatex -no-shell-escape -interaction=nonstopmode -halt-on-error proposal.tex > "$audit_dir/latex_compile_stdout.txt" 2>&1
cp proposal.pdf "$audit_dir/latex_default.pdf"
xelatex -no-shell-escape -interaction=nonstopmode -halt-on-error -jobname=proposal_blank ../audit_blank.tex > "$audit_dir/latex_blank_compile_stdout.txt" 2>&1
cp proposal_blank.pdf "$audit_dir/latex_blank.pdf"
