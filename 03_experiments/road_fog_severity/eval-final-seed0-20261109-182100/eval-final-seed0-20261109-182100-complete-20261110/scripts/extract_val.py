#!/usr/bin/env python3
"""Extract precisely audited val PNGs, exclusively, with ZIP CRC verification."""
import hashlib,json,re,sys,shutil
from pathlib import Path
from zipfile import ZipFile
root=Path('/home/ysheng4/research/GSMF-RS-DIL')
zpath=root/'data/road_raw/leftImg8bit_trainvaltest_foggy.zip'
out=root/'data/cityscapes/leftImg8bit_foggy'
evidence=root/'experiments/road_fog_severity/eval-final-seed0-20261109-182100/acquisition-20261110'
pattern=re.compile(r'^leftImg8bit_foggy/val/([a-z]+)/([a-z]+_[0-9]{6}_[0-9]{6})_leftImg8bit_foggy_beta_(0\.005|0\.01|0\.02)\.png$')
records=[json.loads(x) for x in (root/'experiments/road_clear_to_fog/data/A_val.jsonl').read_text().splitlines()]
expected={(Path(r['image']).name.replace('_leftImg8bit.png',''), b) for r in records for b in ('0.005','0.01','0.02')}
with ZipFile(zpath) as z:
 entries=[i for i in z.infolist() if not i.is_dir() and i.filename.startswith('leftImg8bit_foggy/val/')]
 found={}
 for i in entries:
  m=pattern.fullmatch(i.filename)
  if not m or m.group(2).split('_')[0]!=m.group(1):raise ValueError('unexpected ZIP val entry: '+i.filename)
  key=(m.group(2),m.group(3))
  if key in found:raise ValueError('duplicate ZIP member '+i.filename)
  found[key]=i
 if set(found)!=expected:raise ValueError('ZIP does not contain precisely required val set: missing=%d extra=%d'%(len(expected-set(found)),len(set(found)-expected)))
 if out.exists():raise FileExistsError('refusing to overwrite '+str(out))
 out.mkdir(parents=True,exist_ok=False)
 log=[]
 for index,(key,info) in enumerate(sorted(found.items()),1):
  dest=root/'data/cityscapes'/info.filename;dest.parent.mkdir(parents=True,exist_ok=True)
  h=hashlib.sha256()
  with z.open(info) as src, dest.open('xb') as dst:
   while True:
    b=src.read(8*1024*1024)
    if not b:break
    h.update(b);dst.write(b)
  if dest.stat().st_size!=info.file_size:raise ValueError('size mismatch '+info.filename)
  log.append(dict(path=str(dest),zip_member=info.filename,crc32='%08x'%info.CRC,bytes=info.file_size,sha256=h.hexdigest()))
  if index%250==0:print('extracted and CRC checked:',index,flush=True)
 (evidence/'extraction.json').write_text(json.dumps(dict(status='PASS',archive=str(zpath),selection='official val only',count=len(log),files=log),indent=2)+'\n')
 print('PASS 1500 val files CRC checked')
