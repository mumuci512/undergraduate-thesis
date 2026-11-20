"""Offline receipt and numeric audit of stages B/C. Never executes archived code.

Run: python -I review_received_stage5BC.py
Weights, full predictions and raw datasets are not included; no model rerun.
"""
import ast
import csv
import hashlib
import json
import math
import statistics
import tarfile
from pathlib import Path, PurePosixPath

HERE = Path(__file__).resolve().parent
REAL = ('clear', 'fog', 'rain', 'snow', 'night')
COUNTS = dict(clear=500, fog=100, rain=100, snow=100, night=106,
              fog005=500, fog010=500, fog020=500)
CHECKS = []


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sha(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def check(name, passed):
    CHECKS.append(dict(name=name, passed=bool(passed)))


def close(a, b):
    return a is None and b is None or (a is not None and b is not None
        and math.isclose(a, b, abs_tol=1e-9, rel_tol=0))


def literal(node):
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'dict' and not node.args:
        return {k.arg: literal(k.value) for k in node.keywords}
    if isinstance(node, (ast.List, ast.Tuple)):
        return [literal(v) for v in node.elts]
    if isinstance(node, ast.Dict):
        return {literal(k): literal(v) for k, v in zip(node.keys, node.values)}
    return ast.literal_eval(node)


def selected_config(path):
    wanted = {'randomness', 'train_cfg', 'optim_wrapper', 'road_checkpoint_meta'}
    return {n.targets[0].id: literal(n.value) for n in ast.parse(path.read_text(encoding='utf-8')).body
            if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name)
            and n.targets[0].id in wanted}


def calculate(cell):
    m = cell['confusion_matrix']
    assert len(m) == 19 and all(len(row) == 19 for row in m)
    assert all(type(x) is int and x >= 0 for row in m for x in row)
    gt = list(map(sum, m))
    pred = [sum(row[c] for row in m) for c in range(19)]
    iou = [100*m[c][c]/(gt[c]+pred[c]-m[c][c])
           if gt[c]+pred[c]-m[c][c] else None for c in range(19)]
    return gt, iou, statistics.mean(v for v in iou if v is not None)


def audit(phase, previous):
    run = f'formal-{phase}-plan-20261111-140000'
    received = HERE/run
    root = received/run
    archive = received/(run+'-light.tar.gz')
    digest = sha(archive)
    check(phase+':archive_sha', digest == (received/(archive.name+'.sha256')).read_text().split()[0])
    with tarfile.open(archive) as t:
        members = t.getmembers()
        names = [m.name.casefold() for m in members]
        check(phase+':safe_members', len(names) == len(set(names)) and all(
            PurePosixPath(m.name).parts[0] == run and not PurePosixPath(m.name).is_absolute()
            and '..' not in PurePosixPath(m.name).parts and ':' not in m.name and '\\' not in m.name
            and (m.isfile() or m.isdir()) for m in members))
        archived = {m.name: hashlib.sha256(t.extractfile(m).read()).hexdigest()
                    for m in members if m.isfile()}
    files = {p.relative_to(root).as_posix(): p for p in root.rglob('*') if p.is_file()}
    check(phase+':archive_file_set', {run+'/'+n for n in files} == set(archived))
    hashes = {n: sha(p) for n, p in files.items()}
    check(phase+':archive_bytes', all(hashes[n] == archived[run+'/'+n] for n in files))
    manifest = read(root/'MANIFEST.json')['files']
    check(phase+':manifest_json_set', set(manifest) == set(files)-{'MANIFEST.json', 'MANIFEST.sha256'})
    for n, spec in manifest.items():
        check(phase+':payload:'+n, hashes.get(n) == spec['sha256'] and files[n].stat().st_size == spec['bytes'])
    sha_manifest = {}
    for line in (root/'MANIFEST.sha256').read_text().splitlines():
        h, n = line.split(maxsplit=1)
        sha_manifest[n.lstrip('*')] = h
    check(phase+':manifest_sha_set', set(sha_manifest) == set(files)-{'MANIFEST.sha256'})
    check(phase+':manifest_sha_bytes', all(hashes.get(n) == h for n, h in sha_manifest.items()))
    provenance = read(root/'provenance.json')
    code = provenance['code']['files']
    with tarfile.open(root/'source/formal-training-source.tar.gz') as t:
        source_hashes = {m.name.removeprefix('./'): hashlib.sha256(t.extractfile(m).read()).hexdigest()
                         for m in t.getmembers() if m.isfile()}
    check(phase+':source_fingerprints', source_hashes == code)
    source_receipt = read(root/'execution/formal-source-snapshot-verification.json')
    check(phase+':source_snapshot_receipt', source_receipt['status'] == 'PASS'
          and source_receipt['archive_sha256'] == hashes['source/formal-training-source.tar.gz'])
    auth = read(root/f'authorization-{phase}.json')
    check(phase+':authorization', auth['confirmed'] and auth['phase'] == phase
          and auth['ready_sha256'] == provenance['ready_sha256'])
    check(phase+':training_exit_zero', (root/'exit-code.txt').read_text().strip() == '0'
          and read(root/'execution/status.json')['exit_code'] == 0)
    index = read(root/'results-index.json')
    check(phase+':result_index', hashes['results/cells.json'] == index['cells_sha256']
          and hashes['results/verification.json'] == index['verification_sha256'])
    cells = read(root/'results/cells.json')
    new = [c for c in cells if c['provenance'] == 'new']
    expected_new, expected_images, expected_runs = (104, 26496, 16) if phase == 'B' else (46, 10248, 8)
    check(phase+':cell_count', len(new) == expected_new and len(cells) == expected_new+8)
    check(phase+':image_count', sum(c['images'] for c in new) == expected_images)
    check(phase+':unique_cells', len({(c['model'], c['condition']) for c in cells}) == len(cells))
    protocol = read(root/'results/protocol-independent-check.json')
    check(phase+':remote_protocol_receipt', protocol['status'] == 'PASS' and all(
        c['exact_ID_paths_encoding'] and c['GT_histogram_exact'] and c['student_only']
        and c['state_unchanged'] for c in protocol['cells']))
    for c in cells:
        name = phase+':cell:'+c['model']+':'+c['condition']
        gt, iou, mean = calculate(c)
        check(name+':metrics', gt == c['gt_histogram'] and sum(gt) == c['valid_pixels']
              and c['images'] == COUNTS[c['condition']] and close(mean, c['mIoU'])
              and all(close(x, y) for x, y in zip(iou, c['IoU'].values())))
        if c['model'] == 'source':
            old = next(x for x in previous if x['model'] == 'source' and x['condition'] == c['condition'])
            check(name+':reuse', c['confusion_matrix'] == old['confusion_matrix']
                  and c['checkpoint_sha256'] == old['checkpoint_sha256'])
    training = read(root/'results/training-independent-check.json')
    runs = training['runs']
    check(phase+':training_count', training['status'] == 'PASS' and len(runs) == expected_runs
          and len(training['periodic_checkpoints']) == expected_runs*4)
    order = 'BCDE' if phase == 'B' else 'EDCB'
    source_sha = next(c for c in cells if c['model'] == 'source')['checkpoint_sha256']
    for name, item in runs.items():
        conf = selected_config(root/'training'/name/'resolved.py')
        meta = conf['road_checkpoint_meta']
        fresh = read(root/'training'/name/'fresh-optimizer.json')
        pos = order.index(item['domain'])
        parent = source_sha if pos == 0 else runs[name[:-1]+order[pos-1]]['final_checkpoint_sha256']
        check(phase+':train:'+name, item['iterations'] == 4000 and item['losses_all_finite']
              and item['periodic_all_complete'] and item['parent_sha256'] == parent == meta['parent_sha256']
              and conf['randomness']['seed'] == item['seed'] == fresh['seed']
              and fresh['iteration'] == 0 and fresh['optimizer_state_empty']
              and conf['train_cfg']['max_iters'] == 4000
              and conf['optim_wrapper']['optimizer']['type'] == 'AdamW'
              and meta['road_order'] == 'A'+order
              and all(c['checkpoint_sha256'] == item['final_checkpoint_sha256'] for c in new if c['model'] == name))
    if phase == 'B':
        resume = read(root/'execution/resume-audit-reconciliation.json')
        check('B:resume_receipt', resume['status'] == 'PASS' and resume['prefix_steps'] == 3000
              and resume['resumed_steps'] == 1000 and resume['loss_history_exactly_preserves_prefix']
              and resume['supplemental_images'] == 100)
    receipt_dir = received if phase == 'C' else (
        HERE/'formal-C-plan-20261111-140000/formal-C-plan-20261111-140000/reviewed-B')
    completion = read(receipt_dir/'completion.json')
    external = read(receipt_dir/('handoff-verification.json' if phase == 'C' else 'handoff/handoff-verification.json'))
    check(phase+':external_completion', completion['status'] == 'complete'
          and completion['phase'] == phase and external['status'] == 'PASS'
          and external['archive_sha256'] == digest == completion['handoff']['archive_sha256'])
    check(phase+':completion_result_hashes', completion['training_check_sha256'] == hashes['results/training-independent-check.json']
          and completion['protocol_check_sha256'] == hashes['results/protocol-independent-check.json']
          and completion['independent_result_check_sha256'] == hashes['results/verification.json'])
    return cells, dict(archive_sha256=digest, payload_files=len(manifest),
        sha_manifest_files=len(sha_manifest), source_files=len(code), cells=len(cells),
        new_cells=len(new), new_images=sum(c['images'] for c in new), training_runs=len(runs),
        completion_receipt=(receipt_dir/'completion.json').relative_to(HERE).as_posix())


def summarize(main_cells, b_cells, c_cells):
    all_main = {(c['model'], c['condition']): c for c in main_cells+b_cells}
    results = {}
    names = ['Source', 'Fog', 'Rain', 'Snow', 'Night']
    matrices = read(HERE/'formal-B-plan-20261111-140000/formal-B-plan-20261111-140000/results/three-seed-stage-matrices.json')
    summaries = {}
    for method in ('ft', 'gsmf'):
        for seed in range(3):
            models = ['source']+[method+'_'+w if seed == 0 and w in ('fog', 'rain')
                else f'{method}-seed{seed}-{d}' for w, d in zip(REAL[1:], 'BCDE')]
            rows = matrices[f'{method}-seed{seed}-ABCDE']
            vals = [{d: all_main[(model, d)]['mIoU'] for d in REAL} for model in models]
            for i, row in enumerate(rows):
                check(f'statistics:matrix:{method}:{seed}:{i}', all(close(row['values'][d], vals[i][d]) for d in REAL)
                      and close(row['seen_domain_equal_mean'], statistics.mean(vals[i][d] for d in REAL[:i+1])))
            seen = [statistics.mean(v[d] for d in REAL[:i+1]) for i, v in enumerate(vals)]
            forgetting = {d: max(vals[i][d] for i in range(j, 4))-vals[4][d] for j, d in enumerate(REAL[:4])}
            summaries[(method, seed)] = dict(seen=seen, forgetting=statistics.mean(forgetting.values()))
    csvpath = HERE/'formal-B-plan-20261111-140000/formal-B-plan-20261111-140000/results/three-seed-statistics.csv'
    for row in csv.DictReader(csvpath.open(encoding='utf-8')):
        values = [float(row[f'seed{i}']) for i in range(3)]
        check('statistics:csv:'+row['stage']+':'+row['condition']+':'+row['method'],
              close(statistics.mean(values), float(row['mean'])) and close(statistics.stdev(values), float(row['sample_std'])))
        if row['stage'] in names:
            stage = names.index(row['stage'])
            method = row['method']
            condition = row['condition']
            for seed, value in enumerate(values):
                model = 'source' if stage == 0 else (method+'_'+REAL[stage] if seed == 0 and stage in (1, 2)
                    else f'{method}-seed{seed}-'+('ABCDE'[stage]))
                check(f'statistics:csv_cell:{method}:{seed}:{stage}:{condition}', close(value, all_main[(model, condition)]['mIoU']))
    for i, stage in enumerate(names):
        ft = [summaries[('ft', s)]['seen'][i] for s in range(3)]
        gsmf = [summaries[('gsmf', s)]['seen'][i] for s in range(3)]
        diff = [g-f for f, g in zip(ft, gsmf)]
        results[stage] = {k: dict(per_seed=v, mean=statistics.mean(v), sample_std=statistics.stdev(v))
                          for k, v in [('ft', ft), ('gsmf', gsmf), ('paired_gsmf_minus_ft', diff)]}
    results['old_domain_mean_forgetting'] = {m: [summaries[(m, s)]['forgetting'] for s in range(3)] for m in ('ft', 'gsmf')}
    c_map = {(c['model'], c['condition']): c for c in c_cells}
    results['reverse_final'] = {m: {d: c_map[(f'{m}-seed0-B', d)]['mIoU'] for d in REAL} for m in ('ft', 'gsmf')}
    for vals in results['reverse_final'].values():
        vals['five_real_equal_mean'] = statistics.mean(vals.values())
    return results


def main():
    a = read(HERE/'formal-A-plan-20261111-140000/formal-A-plan-20261111-140000/results/cells.json')
    b, bmeta = audit('B', a)
    c, cmeta = audit('C', a)
    numeric = summarize(a, b, c)
    failed = [c for c in CHECKS if not c['passed']]
    out = dict(date='2026-11-13', status='PASS' if not failed else 'FAIL',
               scope='Offline hashes, receipt consistency and metric recomputation; no model rerun.',
               B=bmeta, C=cmeta, numeric=numeric, check_count=len(CHECKS), failed=failed, checks=CHECKS)
    target = HERE/'REVIEW_stagesBC_2026-11-13_checks.json'
    target.write_text(json.dumps(out, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in out.items() if k not in ('checks', 'numeric')}, ensure_ascii=False, indent=2))
    print(json.dumps(numeric, ensure_ascii=False, indent=2))
    raise SystemExit(bool(failed))


if __name__ == '__main__':
    main()
