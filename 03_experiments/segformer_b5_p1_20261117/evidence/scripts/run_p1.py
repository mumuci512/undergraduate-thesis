"""Official-split B5 FT, real image replay and offline Joint calibration.

Each job owns exact sampler tokens and deterministic per-token augmentation.
Atomic checkpoints include optimizer, AMP scaler, model and RNG states.
The runner reads train and val manifests only. Test access is a later workflow.
"""
import argparse
from collections import Counter
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import random
import time

import cv2
import mmengine
import numpy as np
import torch
from mmcv.transforms import Compose

ROOT = Path(__file__).resolve().parents[1]
P0 = ROOT.parent / 'segformer_b5_p0_20261116'
PLAN = json.loads((ROOT / 'plan.json').read_text())
spec = importlib.util.spec_from_file_location('p0_runtime', P0 / 'run_b5_p0.py')
runtime = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runtime)


def write_json(path, value):
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False))
    temporary.replace(path)


def seed_all(seed):
    random.seed(seed)
    np.random.seed(seed % 2**32)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def read_rows(domain, split):
    assert split in ('train', 'val')
    rows = runtime.records(domain + '_' + split + '.jsonl')
    assert all(row['split'] == split and row['domain'] == domain for row in rows)
    return rows


def memory_rows(domains):
    """Nested per-domain random rankings, rebalanced to a fixed total capacity."""
    capacity = PLAN['er_capacity_images']
    selected = []
    for index, domain in enumerate(domains):
        rows = read_rows(domain, 'train')
        random.Random(PLAN['seed'] + ord(domain)).shuffle(rows)
        quota = capacity // len(domains) + int(index < capacity % len(domains))
        selected.extend(rows[:quota])
    assert len(selected) == capacity
    return selected


class TrainingDataset(torch.utils.data.Dataset):
    def __init__(self, rows):
        self.rows = rows
        self.pipeline = Compose([
            dict(type='RandomResize', scale=(2048, 1024), ratio_range=(0.5, 2.0), keep_ratio=True),
            dict(type='RandomCrop', crop_size=(1024, 1024), cat_max_ratio=0.75),
            dict(type='RandomFlip', prob=0.5), dict(type='PhotoMetricDistortion'),
            dict(type='PackSegInputs')])

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, token):
        index, augmentation_seed = token
        random.seed(augmentation_seed)
        np.random.seed(augmentation_seed)
        row = self.rows[index]
        image = cv2.imread(row['image'])
        assert image is not None, row['image']
        truth = runtime.label(row)
        assert image.shape[:2] == truth.shape
        return self.pipeline(dict(img=image, img_path=row['image'],
            ori_shape=image.shape[:2], img_shape=image.shape[:2],
            gt_seg_map=truth, seg_fields=['gt_seg_map'], reduce_zero_label=False))


def training_tokens(method, domain, steps, seed):
    if method == 'joint':
        rows = []
        for item in 'ABCDE':
            current = read_rows(item, 'train')
            rows.extend(current)
        pools = [list(range(len(rows)))]
    else:
        rows = read_rows(domain, 'train')
        pools = [list(range(len(rows)))]
        if method == 'er':
            previous = list('ABCDE'[:'ABCDE'.index(domain)])
            buffer = memory_rows(previous)
            pools.append(list(range(len(rows), len(rows) + len(buffer))))
            rows.extend(buffer)
    generator = random.Random(seed)
    queues = [[] for _ in pools]
    tokens = []
    for step in range(steps):
        if method == 'er':
            pool_index = int((step + 1) % PLAN['er_replay_every'] == 0)
        else:
            pool_index = 0
        if not queues[pool_index]:
            queues[pool_index] = list(pools[pool_index])
            generator.shuffle(queues[pool_index])
        tokens.append((queues[pool_index].pop(), generator.randrange(2**32)))
    return rows, tokens


def evaluate(checkpoint, destination, domains):
    destination.mkdir(parents=True, exist_ok=True)
    result_file = destination / 'metrics.json'
    if result_file.exists():
        return json.loads(result_file.read_text())
    seed_all(PLAN['seed'])
    model, _ = runtime.model_and_cfg()
    model.load_state_dict(torch.load(str(checkpoint), map_location='cpu')['state_dict'], strict=True)
    model.eval()
    before = runtime.fingerprint(model)
    pipeline = Compose([dict(type='LoadImageFromFile'),
        dict(type='Resize', scale=(2048, 1024), keep_ratio=True), dict(type='PackSegInputs')])
    metrics = {}
    begin = time.monotonic()
    torch.cuda.reset_peak_memory_stats()
    for domain in domains:
        matrix_file = destination / (domain + '_confusion.npy')
        if matrix_file.exists():
            matrix = np.load(matrix_file)
        else:
            matrix = np.zeros((19, 19), dtype=np.int64)
            for index, row in enumerate(read_rows(domain, 'val')):
                data = pipeline(dict(img_path=row['image']))
                with torch.no_grad():
                    sample = model.test_step(dict(inputs=[data['inputs']],
                        data_samples=[data['data_samples']]))[0]
                prediction = sample.pred_sem_seg.data.cpu().numpy()[0]
                truth = runtime.label(row)
                assert prediction.shape == truth.shape
                keep = truth != 255
                matrix += np.bincount(19 * truth[keep].astype(np.int64) + prediction[keep],
                    minlength=361).reshape(19, 19)
                if (index + 1) % 50 == 0:
                    print('VAL', destination, domain, index + 1, flush=True)
            temporary = matrix_file.with_suffix('.tmp')
            with temporary.open('wb') as handle:
                np.save(handle, matrix)
            temporary.replace(matrix_file)
            np.savetxt(destination / (domain + '_confusion.csv'), matrix, delimiter=',', fmt='%d')
        union = matrix.sum(0) + matrix.sum(1) - matrix.diagonal()
        assert (union > 0).all()
        iou = matrix.diagonal() / union * 100
        metrics[domain] = dict(mIoU_percent=float(iou.mean()), per_class_IoU_percent=iou.tolist(),
            count=len(read_rows(domain, 'val')), valid_pixels=int(matrix.sum()))
    assert before == runtime.fingerprint(model)
    result = dict(domains=metrics, checkpoint_sha256=runtime.sha(checkpoint),
        mean_percent=float(np.mean([item['mIoU_percent'] for item in metrics.values()])),
        elapsed_seconds=time.monotonic() - begin, state_unchanged=True,
        peak_allocated_MiB=torch.cuda.max_memory_allocated() / 1024**2)
    write_json(result_file, result)
    del model
    torch.cuda.empty_cache()
    return result


def checkpoint_path(job, step):
    return job / ('step_' + str(step) + '.pth')


def train(job, method, domain, learning_rate, steps, initial, checkpoints, horizon):
    job.mkdir(parents=True, exist_ok=True)
    configuration = dict(method=method, domain=domain, learning_rate=learning_rate,
        steps=steps, horizon=horizon, checkpoints=checkpoints, seed=PLAN['seed'],
        initial_sha256=runtime.sha(initial), plan_sha256=runtime.sha(ROOT / 'plan.json'),
        source_code_sha256=runtime.sha(Path(__file__)))
    config_path = job / 'config.json'
    if config_path.exists():
        assert json.loads(config_path.read_text()) == configuration, 'Job configuration changed'
    else:
        write_json(config_path, configuration)
    if (job / 'complete.json').exists():
        return
    seed_all(PLAN['seed'])
    model, cfg = runtime.model_and_cfg()
    cfg.optim_wrapper.optimizer.lr = learning_rate
    optimizer = runtime.build_optim_wrapper(model, cfg.optim_wrapper).optimizer
    scaler = torch.cuda.amp.GradScaler(init_scale=256)
    rows, tokens = training_tokens(method, domain, steps, PLAN['seed'])
    latest = job / 'latest.pth'
    resume = torch.load(str(latest if latest.exists() else initial), map_location='cpu')
    model.load_state_dict(resume['state_dict'], strict=True)
    start = 0
    previous_seconds = 0.0
    if latest.exists():
        optimizer.load_state_dict(resume['optimizer'])
        scaler.load_state_dict(resume['scaler'])
        start = resume['step']
        previous_seconds = resume['elapsed_seconds']
        random.setstate(resume['python_rng'])
        np.random.set_state(resume['numpy_rng'])
        torch.set_rng_state(resume['torch_rng'])
        torch.cuda.set_rng_state_all(resume['cuda_rng'])
    del resume
    write_json(job / 'training_pool.json', [dict(id=row['id'], domain=row['domain'],
        image_sha256=row['image_sha256'], label_sha256=row['label_sha256']) for row in rows])
    loader = torch.utils.data.DataLoader(TrainingDataset(rows), batch_size=1,
        sampler=tokens[start:], num_workers=2, persistent_workers=True,
        collate_fn=mmengine.dataset.pseudo_collate, pin_memory=True,
        generator=torch.Generator().manual_seed(PLAN['seed']))
    base_rates = [group['lr'] for group in optimizer.param_groups]
    # Resume restores scheduled rates. Recover group multipliers from the official optimizer recipe.
    for group, rate in zip(optimizer.param_groups, base_rates):
        group.setdefault('base_lr', rate)
    model.train()
    torch.cuda.reset_peak_memory_stats()
    begin = time.monotonic()
    log_path = job / 'steps.jsonl'
    # A crash may leave a suffix newer than the last atomic checkpoint.
    if log_path.exists():
        committed = [line for line in log_path.read_text().splitlines()
                     if json.loads(line)['step'] <= start]
        log_path.write_text(''.join(line + '\n' for line in committed))
    with log_path.open('a') as log:
        for offset, batch in enumerate(loader):
            step = start + offset + 1
            factor = (1 - (step - 1) / horizon) ** PLAN['poly_power']
            factor *= min(1.0, 0.001 + 0.999 * step / PLAN['warmup_steps'])
            for group in optimizer.param_groups:
                group['lr'] = group['base_lr'] * factor
            optimizer.zero_grad(set_to_none=True)
            with torch.cuda.amp.autocast():
                data = model.data_preprocessor(batch, training=True)
                losses = model(**data, mode='loss')
                loss, _ = model.parse_losses(losses)
            assert torch.isfinite(loss), 'Nonfinite loss'
            scaler.scale(loss).backward()
            scaler.unscale_(optimizer)
            norm = torch.stack([parameter.grad.detach().float().norm()
                for parameter in model.parameters() if parameter.grad is not None]).norm()
            # GradScaler safely skips an overflowing update and adjusts its scale.
            old_scale = scaler.get_scale()
            scaler.step(optimizer)
            scaler.update()
            torch.cuda.synchronize()
            applied = scaler.get_scale() >= old_scale
            row_index = tokens[step - 1][0]
            log.write(json.dumps(dict(step=step, sample_id=rows[row_index]['id'],
                sample_domain=rows[row_index]['domain'], loss=float(loss.detach()),
                grad_norm=float(norm) if torch.isfinite(norm) else None,
                optimizer_applied=applied, scale=scaler.get_scale(),
                lr=optimizer.param_groups[0]['lr'],
                elapsed_seconds=previous_seconds + time.monotonic() - begin)) + '\n')
            log.flush()
            if step % 50 == 0:
                write_json(ROOT / 'progress.json', dict(job=str(job.relative_to(ROOT)),
                    step=step, total=steps, loss=float(loss.detach()), pid=os.getpid(),
                    updated_unix=time.time(), phase='training'))
                print('TRAIN', job.name, step, '/', steps, float(loss.detach()), flush=True)
            if step % PLAN['checkpoint_interval'] == 0 or step in checkpoints or step == steps:
                state = dict(state_dict=model.state_dict(), optimizer=optimizer.state_dict(),
                    scaler=scaler.state_dict(), step=step,
                    elapsed_seconds=previous_seconds + time.monotonic() - begin,
                    python_rng=random.getstate(), numpy_rng=np.random.get_state(),
                    torch_rng=torch.get_rng_state(), cuda_rng=torch.cuda.get_rng_state_all())
                temporary = job / 'latest.tmp'
                torch.save(state, str(temporary))
                temporary.replace(latest)
                if step in checkpoints:
                    destination = checkpoint_path(job, step)
                    # A hard link keeps one exact serialized checkpoint without another write.
                    if not destination.exists():
                        os.link(str(latest), str(destination))
    elapsed = previous_seconds + time.monotonic() - begin
    records = [json.loads(line) for line in log_path.read_text().splitlines()]
    assert len(records) == steps
    seen = {item['sample_id'] for item in records}
    eligible = {row['id'] for row in rows}
    assert seen == eligible, 'Budget did not cover the entire eligible training pool'
    write_json(job / 'complete.json', dict(status='complete', training_seconds=elapsed,
        attempted_steps=steps, applied_steps=sum(item['optimizer_applied'] for item in records),
        skipped_amp_steps=sum(not item['optimizer_applied'] for item in records),
        image_counts_by_domain=dict(Counter(item['sample_domain'] for item in records)),
        unique_images_seen=len(seen), eligible_images=len(eligible), full_pool_seen=True,
        peak_allocated_MiB=torch.cuda.max_memory_allocated() / 1024**2))
    del model, optimizer, scaler, loader
    torch.cuda.empty_cache()


def select(method, checkpoints, domains):
    candidates = []
    horizon = max(checkpoints)
    for index, learning_rate in enumerate(PLAN['learning_rates']):
        job = ROOT / 'jobs' / (method + '_search_lr' + str(index))
        train(job, method, 'B', learning_rate, horizon, Path(runtime.PREP['checkpoint']),
            checkpoints, horizon)
        for step in checkpoints:
            checkpoint = checkpoint_path(job, step)
            result = evaluate(checkpoint, job / ('val_' + str(step)), domains)
            candidates.append(dict(lr=learning_rate, steps=step, checkpoint=str(checkpoint),
                score=result['mean_percent'], metrics=result['domains']))
    selected = sorted(candidates, key=lambda item: (-item['score'], item['steps'], item['lr']))[0]
    write_json(ROOT / (method + '_selection.json'), dict(candidates=candidates, selected=selected,
        selection_domains=list(domains), selection_split='official_val'))
    return selected


def audit():
    assert runtime.sha(Path(runtime.PREP['checkpoint'])) == PLAN['source_sha256']
    expected = {'A': (2975, 500), 'B': (400, 100), 'C': (400, 100),
                'D': (400, 100), 'E': (400, 106)}
    manifests = ROOT / 'manifests'
    manifests.mkdir(exist_ok=True)
    results = {}
    for domain, counts in expected.items():
        train_rows, val_rows = read_rows(domain, 'train'), read_rows(domain, 'val')
        assert (len(train_rows), len(val_rows)) == counts
        assert not {r['image_sha256'] for r in train_rows} & {r['image_sha256'] for r in val_rows}
        for split, rows in [('train', train_rows), ('val', val_rows)]:
            assert all(Path(row['image']).is_file() and Path(row['label']).is_file() for row in rows)
            source = P0 / 'manifests' / (domain + '_' + split + '.jsonl')
            (manifests / source.name).write_bytes(source.read_bytes())
        results[domain] = dict(train=counts[0], val=counts[1], full_official_train=True,
            exact_train_val_overlap=0)
    write_json(ROOT / 'data_audit.json', results)
    write_json(ROOT / 'runtime_provenance.json', dict(plan_sha256=runtime.sha(ROOT / 'plan.json'),
        runner_sha256=runtime.sha(Path(__file__)), p0_runner_sha256=runtime.sha(P0 / 'run_b5_p0.py'),
        source_sha256=PLAN['source_sha256'], torch_version=torch.__version__,
        cuda_name=torch.cuda.get_device_name(0), cuda_memory_bytes=torch.cuda.get_device_properties(0).total_memory))


def pipeline():
    audit()
    if not (ROOT / 'started.json').exists():
        write_json(ROOT / 'started.json', dict(unix=time.time(), pid=os.getpid()))
    matrices = {}
    source = json.loads((P0 / 'source_results.json').read_text())
    for method in ('ft', 'er'):
        selected = select(method, PLAN['incremental_checkpoints'], 'AB')
        checkpoint = Path(selected['checkpoint'])
        matrix = {'A': {domain: source[domain]['mIoU_percent'] for domain in 'ABCDE'}}
        for domain in 'BCDE':
            if domain != 'B':
                job = ROOT / 'jobs' / (method + '_' + domain)
                train(job, method, domain, selected['lr'], selected['steps'], checkpoint,
                    [selected['steps']], max(PLAN['incremental_checkpoints']))
                checkpoint = checkpoint_path(job, selected['steps'])
            result = evaluate(checkpoint, ROOT / 'matrices' / method / domain, 'ABCDE')
            matrix[domain] = {item: result['domains'][item]['mIoU_percent'] for item in 'ABCDE'}
            write_json(ROOT / (method + '_matrix.json'), matrix)
        matrices[method] = matrix
    select('joint', PLAN['joint_checkpoints'], 'ABCDE')
    summary = {}
    for method, matrix in matrices.items():
        final = matrix['E']
        forgetting = {}
        for domain in 'ABCD':
            history = [matrix[stage][domain] for stage in 'ABCDE'['ABCDE'.index(domain):]]
            forgetting[domain] = max(history) - final[domain]
        summary[method] = dict(final_by_domain=final, final_mean_percent=float(np.mean(list(final.values()))),
            worst_domain_percent=min(final.values()), forgetting_by_domain_pp=forgetting,
            mean_old_domain_forgetting_pp=float(np.mean(list(forgetting.values()))))
    joint = json.loads((ROOT / 'joint_selection.json').read_text())['selected']
    summary['joint'] = joint
    write_json(ROOT / 'summary.json', summary)
    write_json(ROOT / 'completed.json', dict(unix=time.time(), status='complete',
        official_test_status='reserved_for_final_website_evaluation_account_pending'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['audit', 'smoke', 'run'])
    args = parser.parse_args()
    runtime.register_all_modules()
    cv2.setNumThreads(0)
    torch.set_num_threads(4)
    torch.backends.cudnn.benchmark = False
    with (ROOT / 'run.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if args.mode == 'audit':
            audit()
        elif args.mode == 'smoke':
            smoke = {}
            # Exercise the normal data, optimizer and strict checkpoint entry points.
            for method in ('ft', 'er', 'joint'):
                seed_all(PLAN['seed'])
                rows, tokens = training_tokens(method, 'B', 30, 0)
                dataset = TrainingDataset(rows)
                for token in tokens[:5]:
                    sample = dataset[token]
                    assert max(sample['inputs'].shape[-2:]) <= 1024
                model, cfg = runtime.model_and_cfg()
                optimizer = runtime.build_optim_wrapper(model, cfg.optim_wrapper).optimizer
                scaler = torch.cuda.amp.GradScaler(init_scale=256)
                model.train()
                token = tokens[3] if method == 'er' else tokens[0]
                sample = dataset[token]
                with torch.cuda.amp.autocast():
                    data = model.data_preprocessor(mmengine.dataset.pseudo_collate([sample]), training=True)
                    assert data['inputs'].shape == (1, 3, 1024, 1024)
                    loss, _ = model.parse_losses(model(**data, mode='loss'))
                assert torch.isfinite(loss)
                scaler.scale(loss).backward()
                scaler.unscale_(optimizer)
                assert all(torch.isfinite(p.grad).all() for p in model.parameters() if p.grad is not None)
                scaler.step(optimizer)
                scaler.update()
                smoke[method] = dict(loss=float(loss.detach()), sample_domain=rows[token[0]]['domain'],
                    pool_images=len(rows))
                target = ROOT / ('smoke_' + method + '.pth')
                torch.save(dict(state_dict=model.state_dict()), str(target))
                fingerprint = runtime.fingerprint(model)
                model.load_state_dict(torch.load(str(target), map_location='cpu')['state_dict'], strict=True)
                assert runtime.fingerprint(model) == fingerprint
                target.unlink()
                del model, optimizer, scaler, loss, data
                torch.cuda.empty_cache()
                print('SMOKE_OK', method, smoke[method], flush=True)
            audit()
            write_json(ROOT / 'smoke.json', smoke)
        else:
            try:
                pipeline()
            except Exception as error:
                write_json(ROOT / 'failure.json', dict(unix=time.time(), error=repr(error), pid=os.getpid()))
                raise
