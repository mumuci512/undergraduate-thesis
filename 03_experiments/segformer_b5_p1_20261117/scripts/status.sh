#!/usr/bin/env bash
set -euo pipefail
cd /home/ysheng4/research/segformer_b5_p1_20261117
python3 - <<'PY'
import json, pathlib, subprocess, time
root = pathlib.Path('.')
for name in ('progress.json','failure.json','completed.json','ft_selection.json','er_selection.json','summary.json'):
    path = root/name
    if path.exists():
        data = json.loads(path.read_text())
        if name.endswith('_selection.json'):
            data = data['selected']
        print(name, json.dumps(data))
print('processes', subprocess.run(['pgrep','-af','scripts/run_p1.py'],capture_output=True,text=True).stdout)
if (root/'execution.log').exists():
    print('tail', '\n'.join((root/'execution.log').read_text(errors='replace').splitlines()[-8:]))
if (root/'exit_code.txt').exists():
    print('exit_code', (root/'exit_code.txt').read_text())
PY
