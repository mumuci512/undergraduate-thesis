"""Capture final model identities, replay byte budgets and payload hashes."""
import hashlib
import importlib.util
import json
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[1]
P0 = ROOT.parent / 'segformer_b5_p0_20261116'


def read(path):
    return json.loads(path.read_text())


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(4 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def main():
    if (ROOT / 'finalized.json').exists():
        print('Evidence already finalized')
        return
    assert (ROOT / 'completed.json').exists(), 'Training is still pending'
    plan = read(ROOT / 'plan.json')
    models = {}
    for method in ('ft', 'er', 'joint'):
        choice = read(ROOT / (method + '_selection.json'))['selected']
        checkpoint = Path(choice['checkpoint'])
        if method != 'joint':
            checkpoint = ROOT / 'jobs' / (method + '_E') / ('step_' + str(choice['steps']) + '.pth')
        models[method] = dict(path=str(checkpoint), sha256=digest(checkpoint),
            checkpoint_bytes=checkpoint.stat().st_size, selection=choice)
    (ROOT / 'final_models.json').write_text(json.dumps(models, indent=2))
    # Import only the fixed replay membership logic, independent of model execution.
    spec = importlib.util.spec_from_file_location('p1_runtime', ROOT / 'scripts/run_p1.py')
    runtime = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runtime)
    replay = {}
    for stage in 'BCDE':
        domains = list('ABCDE'[:'ABCDE'.index(stage)])
        rows = runtime.memory_rows(domains)
        entries = [dict(id=row['id'], domain=row['domain'],
            image_bytes=Path(row['image']).stat().st_size,
            label_bytes=Path(row['label']).stat().st_size,
            image_sha256=row['image_sha256'], label_sha256=row['label_sha256']) for row in rows]
        replay[stage] = dict(images=len(rows), entries=entries,
            compressed_image_and_label_bytes=sum(item['image_bytes'] + item['label_bytes'] for item in entries))
    (ROOT / 'replay_cost.json').write_text(json.dumps(replay, indent=2))
    costs = {}
    for path in sorted((ROOT / 'jobs').glob('*/complete.json')):
        costs[path.parent.name] = read(path)
    for path in sorted(ROOT.rglob('metrics.json')):
        metrics = read(path)
        costs[str(path.parent.relative_to(ROOT))] = dict(evaluation_seconds=metrics['elapsed_seconds'],
            peak_allocated_MiB=metrics['peak_allocated_MiB'])
    (ROOT / 'costs.json').write_text(json.dumps(costs, indent=2))
    payload = []
    extensions = ('.json', '.jsonl', '.csv', '.npy', '.md', '.py', '.sh', '.log', '.txt')
    for path in sorted(ROOT.rglob('*')):
        if path.is_file() and path.suffix in extensions and path.name not in ('EVIDENCE_MANIFEST.json', 'finalize.log'):
            payload.append(dict(path=str(path.relative_to(ROOT)), bytes=path.stat().st_size, sha256=digest(path)))
    (ROOT / 'EVIDENCE_MANIFEST.json').write_text(json.dumps(dict(
        generated_unix=time.time(), files=payload), indent=2))
    print(json.dumps(dict(payload_files=len(payload), final_models=list(models),
        replay_capacity=plan['er_capacity_images'])))


if __name__ == '__main__':
    main()
