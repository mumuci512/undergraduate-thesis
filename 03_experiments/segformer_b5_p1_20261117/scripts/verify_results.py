"""Independently recompute development metrics and check P1 data permissions."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import tarfile

import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--extract', action='store_true')
    parser.add_argument('--partial', action='store_true')
    args = parser.parse_args()
    evidence = ROOT / 'evidence'
    if args.extract:
        evidence.mkdir(exist_ok=True)
        with tarfile.open(ROOT / 'evidence.tar.gz') as archive:
            for member in archive.getmembers():
                target = (evidence / member.name).resolve()
                assert target.is_relative_to(evidence.resolve())
                assert member.isfile() and not member.issym() and not member.islnk()
                with archive.extractfile(member) as source:
                    payload = source.read()
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(payload)
    plan = read(evidence / 'plan.json')
    checks = []

    def check(name, passed):
        checks.append(dict(name=name, passed=bool(passed)))

    manifests = {}
    for path in sorted((evidence / 'manifests').glob('*.jsonl')):
        manifests[path.stem] = [json.loads(line) for line in path.read_text().splitlines()]
        check(path.name + '_split', all(row['split'] == path.stem.split('_')[1]
            and row['domain'] == path.stem[0] for row in manifests[path.stem]))
    all_train = {row['id']: row for domain in 'ABCDE' for row in manifests[domain + '_train']}
    all_val_ids = {row['id'] for domain in 'ABCDE' for row in manifests[domain + '_val']}
    check('full_train_counts', [len(manifests[d + '_train']) for d in 'ABCDE'] == [2975, 400, 400, 400, 400])
    check('official_val_counts', [len(manifests[d + '_val']) for d in 'ABCDE'] == [500, 100, 100, 100, 106])
    manifest_file = evidence / 'EVIDENCE_MANIFEST.json'
    if manifest_file.exists():
        for entry in read(manifest_file)['files']:
            path = evidence / entry['path']
            check(entry['path'] + '_payload_sha', path.is_file()
                and hashlib.sha256(path.read_bytes()).hexdigest() == entry['sha256'])
    summaries = {}
    for path in sorted((evidence / 'jobs').glob('*/complete.json')):
        job = path.parent
        config = read(job / 'config.json')
        complete = read(path)
        pool = read(job / 'training_pool.json')
        log = [json.loads(line) for line in (job / 'steps.jsonl').read_text().splitlines()]
        ids = {row['id'] for row in pool}
        check(job.name + '_no_val_or_test', ids <= set(all_train) and not ids & all_val_ids)
        check(job.name + '_step_sequence', [row['step'] for row in log] == list(range(1, config['steps'] + 1)))
        check(job.name + '_full_pool_exposure', {row['sample_id'] for row in log} == ids)
        check(job.name + '_finite_losses', all(np.isfinite(row['loss']) for row in log))
        check(job.name + '_actual_steps', complete['applied_steps'] == sum(row['optimizer_applied'] for row in log))
        method = config['method']
        domain = config['domain']
        if method == 'ft':
            check(job.name + '_current_only', ids == {r['id'] for r in manifests[domain + '_train']})
        if method == 'er':
            current = {r['id'] for r in manifests[domain + '_train']}
            memory = ids - current
            check(job.name + '_complete_current', current <= ids)
            check(job.name + '_capacity', len(memory) == plan['er_capacity_images'])
            check(job.name + '_past_only', all(all_train[item]['domain'] < domain for item in memory))
            check(job.name + '_replay_schedule', all((row['sample_id'] in memory)
                == (row['step'] % plan['er_replay_every'] == 0) for row in log))
        summaries[job.name] = dict(training_seconds=complete['training_seconds'],
            steps=complete['attempted_steps'], applied=complete['applied_steps'],
            images_by_domain=dict(Counter(row['sample_domain'] for row in log)),
            peak_allocated_MiB=complete['peak_allocated_MiB'])
    matrix_values = {}
    for path in sorted(evidence.rglob('*_confusion.npy')):
        matrix = np.load(path)
        check(str(path.relative_to(evidence)) + '_shape', matrix.shape == (19, 19))
        check(str(path.relative_to(evidence)) + '_nonnegative', (matrix >= 0).all())
        union = matrix.sum(0) + matrix.sum(1) - matrix.diagonal()
        score = float((matrix.diagonal() / union).mean() * 100)
        domain = path.name[0]
        result = read(path.parent / 'metrics.json')['domains'][domain]
        check(str(path.relative_to(evidence)) + '_mIoU', abs(score - result['mIoU_percent']) < 1e-9)
        # GT marginals depend only on the official validation split.
        reference = np.zeros(19, dtype=np.int64)
        for row in manifests[domain + '_val']:
            for key, count in row['label_histogram'].items():
                if int(key) < 19:
                    reference[int(key)] += count
        check(str(path.relative_to(evidence)) + '_GT_marginal', np.array_equal(matrix.sum(1), reference))
        matrix_values[str(path.relative_to(evidence))] = score
    for method in ('ft', 'er', 'joint'):
        path = evidence / (method + '_selection.json')
        if not path.exists():
            check(method + '_selection_exists', args.partial)
            continue
        selection = read(path)
        candidates = selection['candidates']
        check(method + '_six_candidates', len(candidates) == 6)
        selected = sorted(candidates, key=lambda item: (-item['score'], item['steps'], item['lr']))[0]
        check(method + '_selection_rule', selected == selection['selected'])
        check(method + '_selection_domains', selection['selection_domains'] == list('ABCDE' if method == 'joint' else 'AB'))
        for candidate in candidates:
            step = candidate['steps']
            remote_job = Path(candidate['checkpoint']).parent.name
            metrics = read(evidence / 'jobs' / remote_job / ('val_' + str(step)) / 'metrics.json')
            check(method + '_' + remote_job + '_' + str(step), abs(candidate['score'] - metrics['mean_percent']) < 1e-9)
        if method in ('ft', 'er'):
            parent = read(evidence / 'matrices' / method / 'B' / 'metrics.json')['checkpoint_sha256']
            matrix = read(evidence / (method + '_matrix.json'))
            for stage in 'CDE':
                config = read(evidence / 'jobs' / (method + '_' + stage) / 'config.json')
                check(method + '_' + stage + '_parent_sha', config['initial_sha256'] == parent)
                check(method + '_' + stage + '_locked_hyperparameters',
                    config['learning_rate'] == selected['lr'] and config['steps'] == selected['steps'])
                result = read(evidence / 'matrices' / method / stage / 'metrics.json')
                parent = result['checkpoint_sha256']
            for stage in 'BCDE':
                result = read(evidence / 'matrices' / method / stage / 'metrics.json')
                check(method + '_' + stage + '_matrix_values', all(
                    abs(matrix[stage][d] - result['domains'][d]['mIoU_percent']) < 1e-9 for d in 'ABCDE'))
            if (evidence / 'summary.json').exists():
                summary = read(evidence / 'summary.json')[method]
                check(method + '_final_mean', abs(summary['final_mean_percent']
                    - np.mean(list(matrix['E'].values()))) < 1e-9)
                differences = [max(matrix[s][d] for s in 'ABCDE'['ABCDE'.index(d):])
                    - matrix['E'][d] for d in 'ABCD']
                check(method + '_forgetting', abs(summary['mean_old_domain_forgetting_pp']
                    - np.mean(differences)) < 1e-9)
    check('completed_receipt', args.partial or (evidence / 'completed.json').exists())
    result = dict(status='partial_verified' if args.partial else 'verified',
        archive_sha256=hashlib.sha256((ROOT / 'evidence.tar.gz').read_bytes()).hexdigest(),
        checks=checks, passed=sum(item['passed'] for item in checks),
        failed=sum(not item['passed'] for item in checks), jobs=summaries, matrices=matrix_values)
    (ROOT / 'VERIFICATION.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(dict(status=result['status'], passed=result['passed'], failed=result['failed'],
        completed_jobs=len(summaries), matrices=len(matrix_values))))
    assert result['failed'] == 0


if __name__ == '__main__':
    main()
