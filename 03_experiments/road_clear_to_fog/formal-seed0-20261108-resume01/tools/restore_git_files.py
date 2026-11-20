#!/usr/bin/env python3
import argparse,csv,hashlib,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,required=True);p.add_argument('--destination',type=Path,required=True);a=p.parse_args()
root=Path(__file__).resolve().parents[1]
for row in csv.DictReader((root/'GIT_FILES.tsv').open(),delimiter='\t'):
 data=subprocess.check_output(['git','-C',str(a.repo.resolve()),'show',row['commit']+':'+row['repository_path']])
 assert hashlib.sha256(data).hexdigest()==row['sha256'],row['repository_path']
 target=a.destination/row['repository_path'];target.parent.mkdir(parents=True,exist_ok=True)
 if target.exists():
  assert target.read_bytes()==data,'Refuse overwrite: '+str(target)
 else:
  with target.open('xb')as f:f.write(data)
print('Exact-commit Git restoration and SHA-256 verification PASS')
