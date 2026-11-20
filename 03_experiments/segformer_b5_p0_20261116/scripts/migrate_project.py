"""Relocate this P0 experiment only; preserve execution evidence and data."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import shutil

research = Path('/home/ysheng4/research').resolve(strict=True)
gsmf = research/'GSMF-RS-DIL'
old = gsmf/'experiments/segformer_b5_p0_20261116'
new = research/'segformer_b5_p0_20261116'
archive = gsmf/'handoff_exports/segformer_b5_p0_20261116.tar.gz'
assert old.resolve(strict=True) == research/'GSMF-RS-DIL/experiments/segformer_b5_p0_20261116'
assert not old.is_symlink() and not new.exists() and not new.is_symlink()
assert new.resolve().parent == research
print('VERIFIED_MOVE_SCOPE', str(old), '->', str(new), flush=True)

def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda:f.read(4*1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()

before = {p.relative_to(old).as_posix():{'bytes':p.stat().st_size,'sha256':sha(p)}
          for p in old.rglob('*') if p.is_file()}
assert sha(archive) == 'c3cae0eeea90ad7b5168780a3b1da05d75aff803c28bbee51a75d64602b1d44f'
old.rename(new)
for name, rec in before.items():
    p = new/name
    assert p.stat().st_size == rec['bytes'] and sha(p) == rec['sha256'], name
assert not old.exists()
provenance = new/'provenance'
provenance.mkdir()
archive.rename(provenance/'segformer_b5_p0_20261116.original.tar.gz')
original = provenance/'original'
original.mkdir()
for name in ['prepare.json','environment.json','run_b5_p0.py','EVIDENCE_MANIFEST.json']:
    shutil.copy2(new/name,original/name)
(new/'EVIDENCE_MANIFEST.json').rename(provenance/'EVIDENCE_MANIFEST.original.json')
shutil.copytree(new/'manifests', original/'manifests')

prep = json.loads((new/'prepare.json').read_text())
data = new/'data'
data.mkdir()
datasets = set()
pair_count = 0
for path in (new/'manifests').glob('*.jsonl'):
    rows = [json.loads(x) for x in path.read_text().splitlines()]
    for row in rows:
        for key in ['image','label']:
            rel = Path(row[key]).relative_to(gsmf/'data')
            datasets.add(rel.parts[0])
            row[key] = str(data/rel)
        pair_count += 1
    path.write_text(''.join(json.dumps(r)+'\n' for r in rows))
for name in sorted(datasets):
    target = (gsmf/'data'/name).resolve(strict=True)
    assert target.is_dir()
    (data/name).symlink_to(target,target_is_directory=True)
for path in (new/'manifests').glob('*.jsonl'):
    for line in path.read_text().splitlines():
        row = json.loads(line)
        assert Path(row['image']).is_file() and Path(row['label']).is_file()
prep['initial_execution_root'] = prep['root']
prep['initial_execution_git_head'] = prep.pop('git_head')
prep['root'] = prep['output'] = str(new)
prep['checkpoint'] = str(new/'source_cityscapes_official.pth')
prep['manifests'] = {name:str(new/'manifests'/name) for name in prep['manifests']}
prep['layout_migrated_at'] = datetime.now(timezone.utc).isoformat()
(new/'prepare.json').write_text(json.dumps(prep,indent=2))
env = json.loads((new/'environment.json').read_text())
env['checkpoint_location'] = prep['checkpoint']
env['smoke_checkpoint_location'] = str(new/'train_amp_scale256/smoke_200.pth')
env['initial_execution_git_head'] = env.pop('git_head')
env['initial_execution_git_status'] = env.pop('git_status')
env['current_project_root'] = str(new)
env['data_access'] = 'Read-only reuse via data symlinks; original datasets unchanged'
(new/'environment.json').write_text(json.dumps(env,indent=2))
assert sha(new/'source_cityscapes_official.pth') == prep['checkpoint_sha256']
assert sha(new/'train_amp_scale256/smoke_200.pth') == json.loads((new/'train_amp_scale256/result.json').read_text())['checkpoint_sha256']
receipt = dict(migrated_at=prep['layout_migrated_at'],source=str(old),destination=str(new),
    original_file_count=len(before),all_original_files_byte_identical_after_move=True,
    original_files=before,source_removed=not old.exists(),original_archive_moved=True,
    source_weight_sha256=prep['checkpoint_sha256'],smoke_weight_sha256=sha(new/'train_amp_scale256/smoke_200.pth'),
    manifest_pairs_checked=pair_count,dataset_symlinks={x:str((data/x).resolve()) for x in sorted(datasets)},
    preserved_original_evidence=str(provenance),training_or_evaluation_rerun=False)
(new/'MIGRATION.json').write_text(json.dumps(receipt,indent=2))
print(json.dumps({k:v for k,v in receipt.items() if k!='original_files'},indent=2),flush=True)
