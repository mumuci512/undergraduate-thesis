#!/usr/bin/env bash
set -euo pipefail
cd /home/ysheng4/research/segformer_b5_p1_20261117
exec 9>finish.lock
flock -x 9
touch finish_waiting.ready
if flock -x run.lock bash -c 'test -f completed.json && env -u PYTHONPATH /home/ysheng4/miniconda3/envs/GSMF_RS_DIL/bin/python scripts/finalize_evidence.py > finalize.log 2>&1'; then
    python3 - <<'PY'
import json, pathlib, time
pathlib.Path('finalized.json').write_text(json.dumps(dict(status='finalized', unix=time.time())))
PY
else
    python3 - <<'PY'
import json, pathlib, time
pathlib.Path('finalize_failure.json').write_text(json.dumps(dict(status='requires_diagnosis', unix=time.time())))
PY
    exit 1
fi
