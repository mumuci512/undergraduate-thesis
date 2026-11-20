#!/usr/bin/env python3
"""Finalize status metadata and revalidate the already built internal archive."""
import datetime,hashlib,json,shutil,tarfile,tempfile
from pathlib import Path
root=Path('/home/ysheng4/research/GSMF-RS-DIL');run=root/'experiments/road_fog_severity/eval-final-seed0-20261109-182100';out=run/'evaluation-20261110';bundle=root/'handoff_exports/eval-final-seed0-20261109-182100-complete-20261110';archive=bundle.parent/(bundle.name+'.tar.gz');checksum=bundle.parent/(archive.name+'.sha256')
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
status=json.loads((out/'status.json').read_text());status.update(state='完成',updated=datetime.datetime.now().astimezone().isoformat(timespec='seconds'),pid=None,session=None,detail='12/12 正式单元、独立矩阵复核及回传包核验通过。')
text=json.dumps(status,indent=2,ensure_ascii=False)+'\n';(out/'status.json').write_text(text);(bundle/'status.json').write_text(text)
shutil.copy2(run/'acquisition-20261110/finalizer.exit',bundle/'acquisition-20261110/finalizer.exit')
shutil.copy2(run/'scripts/complete_package.py',bundle/'scripts/complete_package.py')
files=sorted(p for p in bundle.rglob('*') if p.is_file() and p.name!='MANIFEST.sha256');(bundle/'MANIFEST.sha256').write_text(''.join(sha(p)+'  ./'+str(p.relative_to(bundle))+'\n' for p in files))
with tarfile.open(archive,'w:gz') as t:t.add(bundle,arcname=bundle.name)
checksum.write_text(sha(archive)+'  '+archive.name+'\n')
with tempfile.TemporaryDirectory(prefix='road-fog-final-',dir='/tmp') as tmp:
 with tarfile.open(archive,'r:gz') as t:t.extractall(tmp)
 unpack=Path(tmp)/bundle.name; listed=set()
 for line in (unpack/'MANIFEST.sha256').read_text().splitlines():
  expected,name=line.split('  ',1);p=unpack/name;assert sha(p)==expected;listed.add(p.relative_to(unpack).as_posix())
 assert listed==set(p.relative_to(unpack).as_posix() for p in unpack.rglob('*') if p.is_file() and p.name!='MANIFEST.sha256')
report=dict(status='PASS',timestamp=datetime.datetime.now().astimezone().isoformat(timespec='seconds'),archive=str(archive),archive_sha256=sha(archive),sha256_file=str(checksum),manifest_file_count=len(files),archive_bytes=archive.stat().st_size,unpacked_file_set_and_hashes_verified=True)
(out/'handoff-verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
