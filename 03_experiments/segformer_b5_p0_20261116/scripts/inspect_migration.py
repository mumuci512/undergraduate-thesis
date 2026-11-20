from pathlib import Path
import json
import subprocess

home = Path('/home/ysheng4')
research = home/'research'
old = research/'GSMF-RS-DIL/experiments/segformer_b5_p0_20261116'
new = research/'segformer_b5_p0_20261116'
for p in [home/'AGENTS.md', research/'AGENTS.md']:
    if p.is_file():
        print('INSTRUCTIONS', p, '\n', p.read_text())
print('SOURCE_RESOLVED', old.resolve(strict=True))
print('DESTINATION_RESOLVED', new.resolve(), 'EXISTS', new.exists())
print('SOURCE_FILES', [str(p.relative_to(old)) for p in old.rglob('*') if p.is_file()])
print('PIDS', subprocess.run(['pgrep','-af','python'],capture_output=True,text=True).stdout)
prep = json.loads((old/'prepare.json').read_text())
prefixes = set()
for path in prep['manifests'].values():
    for line in Path(path).read_text().splitlines():
        row = json.loads(line)
        for key in ['image','label']:
            p = Path(row[key])
            data = research/'GSMF-RS-DIL/data'
            p.relative_to(data)
            prefixes.add(p.relative_to(data).parts[0])
print('DATASET_ROOTS', sorted(prefixes))
print('ARCHIVE', research/'GSMF-RS-DIL/handoff_exports/segformer_b5_p0_20261116.tar.gz')
