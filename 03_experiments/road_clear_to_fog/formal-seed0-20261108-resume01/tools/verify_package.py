#!/usr/bin/env python3
import hashlib
from pathlib import Path
root=Path(__file__).resolve().parents[1];expected={}
for line in (root/'MANIFEST.sha256').read_text().splitlines():
 digest,name=line.split('  ',1);p=root/name
 assert p.is_file()and not p.is_symlink(),name
 assert hashlib.sha256(p.read_bytes()).hexdigest()==digest,name
 expected[name]=digest
actual={str(p.relative_to(root))for p in root.rglob('*')if p.is_file()and p.name!='MANIFEST.sha256'}
assert actual==set(expected),(actual-set(expected),set(expected)-actual)
print('MANIFEST PASS:',len(expected),'files')
