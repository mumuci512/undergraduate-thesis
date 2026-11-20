import hashlib,json
from pathlib import Path
root=Path('/home/ysheng4/research/GSMF-RS-DIL')
out=root/'experiments/road_fog_severity/eval-final-seed0-20261109-182100/precheck/manifests'
records=[json.loads(x) for x in (root/'experiments/road_clear_to_fog/data/A_val.jsonl').read_text().splitlines()]
selected=[records[0],records[-1]]
p=out/'A_val_debug.jsonl'; p.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in selected))
h=hashlib.sha256(p.read_bytes()).hexdigest()
(out/'audit.json').write_text(json.dumps(dict(status='PASS',full_official_counts=False,manifest_sha256={p.name:h},description='two clear val scenes only; not the four-condition precheck or formal evaluation'),indent=2)+'\n')
(out/'selection.json').write_text(json.dumps([r['id'] for r in selected],indent=2)+'\n')
