#!/usr/bin/env bash
set -eu
cd /home/ysheng4/research/GSMF-RS-DIL
cat AGENTS.md
ls
ls data
ls tools
pgrep -af python || true
/home/ysheng4/miniconda3/envs/GSMF_RS_DIL/bin/python - <<'PY'
import torch, mmseg, mmcv, mmengine
from pathlib import Path
print('VERSIONS', torch.__version__, mmseg.__version__, mmcv.__version__, mmengine.__version__)
print('MMSEG', mmseg.__file__)
print('CUDA', torch.cuda.is_available())
for root in ('configs', 'checkpoints', 'data', 'datasets'):
    p = Path(root)
    if p.exists():
        print('ROOT', root, [str(x) for x in p.iterdir()])
PY
