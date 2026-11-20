#!/usr/bin/env python3
import csv,hashlib,json,sys
from pathlib import Path
def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
prepared=Path(sys.argv[1]); audit=Path(sys.argv[2]); manifest=audit/'available_manifest.csv';meta=json.loads((audit/'audit.json').read_text())
if sha(manifest)!=meta['manifest_sha256']:raise ValueError('audit manifest changed')
scenes=json.loads((prepared/'scene_ids.json').read_text()); common=meta['common_scene_ids']
if sorted(scenes)!=sorted(common) or len(scenes)!=len(set(scenes)) or len(scenes)<6:raise ValueError('scene set differs from audit')
rows=list(csv.DictReader(manifest.open())); records={(r['base_scene_id'],r['beta']):r for r in rows}
if len(records)!=len(rows):raise ValueError('duplicate scene/condition')
for phase,ids in [('precheck',sorted(scenes)[:2]),('full',sorted(scenes))]:
 for beta in ('0','0.005','0.01','0.02'):
  d=prepared/phase/beta; f=d/'A_val_debug.jsonl'; info=json.loads((d/'audit.json').read_text()); recs=[json.loads(x) for x in f.read_text().splitlines()]
  if sha(f)!=info['manifest_sha256'][f.name] or [r['id'] for r in recs]!=ids or info['source_manifest_sha256']!=meta['manifest_sha256']:raise ValueError('prepared manifest changed')
  for r in recs:
   x=records[r['id'],beta]
   if (r['image'],r['label'],r['encoding'])!=(x['image'],x['gt'],'labelIds'):raise ValueError('manifest does not match audit')
for s in scenes:
 for beta in ('0','0.005','0.01','0.02'):
  x=records[s,beta]
  if sha(x['image'])!=x['image_sha256'] or sha(x['gt'])!=x['gt_sha256']:raise ValueError('data bytes changed')
print('PASS: audited common scenes and manifest/file SHA-256')
