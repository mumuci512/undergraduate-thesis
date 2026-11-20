#!/usr/bin/env python
"""Read-only preflight, persistent observation and independent final verification.

Never launches/retries training. Lives outside the validated training code tree.
"""
import argparse
import base64
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
import gc
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[2]
EXP = ROOT / 'experiments/road_clear_to_fog'
sys.path.insert(0, str(ROOT))
STAGES = ('source', 'ft', 'gsmf')
COUNTS = {'A_train': 2975, 'A_val': 500, 'B_train': 400, 'B_val': 100}
BEGIN, END = '<!-- ROAD_FORMAL_CURRENT_BEGIN -->', '<!-- ROAD_FORMAL_CURRENT_END -->'


def now():
    return (datetime.utcnow() + timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S +08:00')


def read(p):
    return json.loads(Path(p).read_text())


def save(p, value):
    with Path(p).open('x') as f:
        json.dump(value, f, indent=2, ensure_ascii=False, allow_nan=False)
        f.write('\n')


def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def records(name):
    return [json.loads(x) for x in (EXP / 'data' / (name + '.jsonl')).read_text().splitlines() if x.strip()]


def host_storage():
    """Check the physical Windows volume backing the verified WSL distro."""
    script = r'''[Console]::OutputEncoding=[System.Text.Encoding]::UTF8
$ProgressPreference='SilentlyContinue'
$distros=@(Get-ChildItem 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Lxss' | ForEach-Object {$p=Get-ItemProperty $_.PSPath;[pscustomobject]@{Name=[string]$p.DistributionName;BasePath=[string]$p.BasePath}})
$disks=@(Get-CimInstance Win32_LogicalDisk -Filter 'DriveType=3' | Select-Object DeviceID,FreeSpace)
[pscustomobject]@{Distros=$distros;Disks=$disks}|ConvertTo-Json -Depth 3 -Compress
'''
    encoded = base64.b64encode(script.encode('utf-16le')).decode()
    result = subprocess.run(['/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe',
        '-NoProfile', '-NonInteractive', '-EncodedCommand', encoded],
        capture_output=True, timeout=30, check=True)
    data = json.loads(result.stdout.decode('utf-8'))
    distro = next(x for x in data['Distros'] if x['Name'] == 'Ubuntu-22.04')
    drive = distro['BasePath'].removeprefix('\\\\?\\')[:2] if sys.version_info >= (3, 9) else distro['BasePath'].replace('\\\\?\\', '', 1)[:2]
    disk = next(x for x in data['Disks'] if x['DeviceID'].upper() == drive.upper())
    return {'vhd_base_path': distro['BasePath'], 'drive': drive, 'free_bytes': int(disk['FreeSpace'])}


def preflight(output):
    from mmengine.config import Config
    from tools.road.pipeline import code_fingerprint
    ready = read(EXP / 'ready.json')
    audit = read(EXP / 'data/audit.json')
    assert audit['status'] == 'PASS' and audit['full_official_counts'] and not audit['errors']
    assert sha(EXP / 'data/audit.json') == ready['data_audit_sha256']
    assert code_fingerprint()['sha256'] == ready['code_sha256']
    assert read(Path(ready['run_directory']) / 'status.json')['exit_code'] == 0
    assert read(EXP / 'real-validation-evidence-20261107.json')['status'] == 'PASS'
    for name, expected in audit['manifest_sha256'].items():
        assert sha(EXP / 'data' / name) == expected, name
    files = {}
    for name, count in COUNTS.items():
        rows = records(name)
        assert len(rows) == count
        for row in rows:
            assert row['domain'] + '_' + row['split'] == name
            for kind in ('image', 'label'):
                files[row[kind]] = row[kind + '_sha256']
    def check(item):
        path, expected = item
        assert sha(path) == expected, path
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(check, files.items()))
    configs = {}
    for stage in STAGES:
        steps = 60000 if stage == 'source' else 4000
        cfg = Config.fromfile(str(ROOT / 'configs/road' / {
            'source': 'source_cityscapes.py', 'ft': 'ft_acdc_fog.py', 'gsmf': 'gsmf_acdc_fog.py'}[stage]))
        assert cfg.train_cfg.max_iters == cfg.param_scheduler[0].end == steps
        assert cfg.randomness.seed == 0 and cfg.randomness.deterministic
        assert cfg.train_dataloader.batch_size == 2
        assert tuple(cfg.model.data_preprocessor.size) == (512, 512)
        assert cfg.optim_wrapper.optimizer.lr == (1e-4 if stage == 'source' else 1e-5)
        assert cfg.default_hooks.checkpoint.get('save_best') is None
        domain = 'A' if stage == 'source' else 'B'
        assert Path(cfg.train_dataloader.dataset.ann_file).name == domain + '_train.jsonl'
        assert Path(cfg.val_dataloader.dataset.ann_file).name == domain + '_val.jsonl'
        configs[stage] = {'steps': steps, 'batch_size': 2, 'crop': [512, 512], 'seed': 0,
                          'lr': cfg.optim_wrapper.optimizer.lr}
        short = Path(ready['run_directory']) / stage
        completion = read(next(short.glob('completion-*.json')))
        assert completion['status'] == 'PASS' and sha(completion['checkpoint']) == completion['sha256']
        diag = read(short / 'audit-end-8.json')
        assert diag['finite_all_checked_gradients'] and all(math.isfinite(x) for x in diag['losses'])
    gpu = subprocess.run(['/usr/lib/wsl/lib/nvidia-smi', '--query-compute-apps=pid,process_name,used_memory',
                          '--format=csv,noheader'], capture_output=True, text=True, check=True)
    assert not gpu.stdout.strip(), 'GPU compute process conflict: ' + gpu.stdout
    sessions = subprocess.run(['tmux', 'list-sessions'], capture_output=True, text=True)
    assert 'road-formal-' not in sessions.stdout, 'Existing formal session: ' + sessions.stdout
    assert shutil.disk_usage(ROOT).free >= 20 * 2**30
    storage = host_storage()
    assert storage['free_bytes'] >= 20 * 2**30, 'Physical Windows VHD volume lacks 20GiB: ' + str(storage)
    save(output, {'status': 'PASS', 'time_local': now(), 'verified_data_files': len(files),
                  'counts': COUNTS, 'configs': configs, 'code_sha256': ready['code_sha256'],
                  'data_audit_sha256': ready['data_audit_sha256'], 'free_bytes': shutil.disk_usage(ROOT).free,
                  'gpu_compute_processes': gpu.stdout, 'tmux_before_launch': sessions.stdout,
                  'windows_vhd_storage': storage,
                  'scope': 'seed0 source60000 ft4000 gsmf4000 only; no additional experiments'})
    print('Preflight PASS:', output, flush=True)


def update_block(path, body):
    path = Path(path)
    text = path.read_text()
    block = BEGIN + '\n' + body + '\n' + END
    if BEGIN in text:
        before, rest = text.split(BEGIN, 1)
        _, after = rest.split(END, 1)
        text = before + block + after
    else:
        first, rest = text.split('\n', 1)
        text = first + '\n\n' + block + '\n' + rest
    tmp = path.with_name(path.name + '.formal-tmp')
    tmp.write_text(text)
    tmp.replace(path)


def update_status(run, session, state, detail):
    lineage = read(run / 'provenance.json') if (run / 'provenance.json').exists() else {}
    recovery = ('\n- 本运行从原运行iter40000恢复模型/AdamW/PolyLR/迭代位置；原始损坏iter50000保留。'
                '原checkpoint未保存RNG及数据迭代器状态，不声称与不停机逐位一致。\n'
                if lineage.get('parent_run') else '')
    body = ('更新时间：' + now() + '\n\n'
            '正式seed0状态：**' + state + '**。' + detail + '\n\n'
            '- 输出：`' + str(run.relative_to(ROOT)) + '`\n'
            '- 持久训练会话：`' + (session / 'session.txt').read_text().strip() + '`\n'
            '- 预算：源60000、FT4000、GSMF4000；batch2/crop512；只运行本次授权范围。\n'
            '- 阶段退出码：运行目录events.jsonl；总退出码：会话目录exit-code.txt。\n'
            '- 监测每20秒检查事件与实际进程，不重试训练；全程结束后独立重读预测并更新RESULTS/REPRO。\n'
            '- 主机/WSL停机会中断训练和监测，须人工核对完整状态后resume。' + recovery)
    update_block(EXP / 'STATUS.md', body)
    update_block(ROOT / 'REPRO.md', body)


def verify(run, allow_debug=False):
    """Re-read PNGs and raw labels; implement mapping and metrics independently."""
    import numpy as np
    import torch
    from PIL import Image
    from road_dil.protocol import CLASSES, LABEL_IDS
    summary = read(sorted(run.glob('summary-*.json'))[-1])
    assert allow_debug or not summary['debug_only']
    audit_data = read(EXP / 'data/audit.json')
    result = {'time_local': now(), 'status': 'PASS', 'models': {}, 'metrics': {}}
    for stage in STAGES:
        steps = 8 if allow_debug else (60000 if stage == 'source' else 4000)
        checkpoint = run / stage / ('iter_%d.pth' % steps)
        c = torch.load(str(checkpoint), map_location='cpu')
        assert c['meta']['iter'] == steps
        assert {int(v['step']) for v in c['optimizer']['state'].values() if 'step' in v} == {steps}
        assert c['param_schedulers'][0]['end'] == steps
        assert c['param_schedulers'][0]['_global_step'] == steps
        digest = sha(checkpoint)
        prefixes = ('backbone_1.', 'decode_head_1.') if stage == 'gsmf' else ('backbone.', 'decode_head.')
        deploy_bytes = sum(v.numel() * v.element_size() for k, v in c['state_dict'].items() if k.startswith(prefixes))
        del c
        gc.collect()
        result['models'][stage] = {'checkpoint_sha256': digest, 'iteration': steps,
                                    'optimizer_steps': steps, 'deployment_state_bytes': deploy_bytes}
        result['metrics'][stage] = {}
        for domain in ('A', 'B'):
            directory = run / ('eval_%s_%s' % (stage, domain))
            ev = read(directory / 'evaluation.json')
            assert ev['checkpoint_sha256'] == digest and ev['state_unchanged'] and ev['full_official_split']
            assert allow_debug or (not ev['debug'] and not ev['synthetic_fixture'])
            if stage == 'gsmf':
                assert ev['forward_calls']['backbone'] == ev['forward_calls']['decode_head.conv_seg'] == 0
            rows = records(domain + '_val')
            assert len(rows) == ev['evaluated_images'] == COUNTS[domain + '_val']
            assert len(list((directory / 'predictions').glob('*.png'))) == len(rows)
            matrix = np.zeros((19, 19), dtype=np.int64)
            for row in rows:
                pred_path = directory / 'predictions' / (Path(row['image']).stem + '.png')
                with Image.open(pred_path) as img:
                    img.verify()
                with Image.open(pred_path) as img:
                    pred = np.array(img)
                with Image.open(row['label']) as img:
                    raw = np.array(img)
                assert pred.shape == raw.shape == tuple(row['shape'])
                assert pred.min() >= 0 and pred.max() < 19
                if row['encoding'] == 'labelIds':
                    target = np.full(raw.shape, 255, dtype=np.uint8)
                    for i, label_id in enumerate(LABEL_IDS):
                        target[raw == label_id] = i
                else:
                    assert row['encoding'] == 'trainIds'
                    target = raw
                mask = target != 255
                assert np.isin(target[mask], np.arange(19)).all()
                matrix += np.bincount((target[mask].astype(np.int64) * 19 + pred[mask]).ravel(),
                                      minlength=361).reshape(19, 19)
            expected = [audit_data['groups'][domain + '_val']['histogram'].get(str(i), 0) for i in range(19)]
            assert matrix.sum(1).tolist() == expected
            for name in ('independent-metrics.json', 'reloaded-prediction-metrics.json'):
                assert matrix.tolist() == read(directory / name)['confusion_matrix']
            union = matrix.sum(0) + matrix.sum(1) - matrix.diagonal()
            values = np.divide(matrix.diagonal().astype(float), union,
                               out=np.full(19, np.nan), where=union > 0) * 100
            mean = float(np.nanmean(values))
            assert abs(mean - summary['table'][stage][domain]['mIoU']) < 1e-10
            result['metrics'][stage][domain] = {'mIoU': mean, 'images': len(rows),
                'IoU': {k: float(v) if np.isfinite(v) else None for k, v in zip(CLASSES, values)},
                'confusion_matrix': matrix.tolist()}
            print('Independent verification PASS:', stage, domain, mean, flush=True)
    return result, summary


def publish(run, evidence, summary):
    from road_dil.protocol import CLASSES
    lines = ['# 道路seed0正式结果', '', '更新：' + now(), '',
             '实验：`' + str(run.relative_to(ROOT)) + '`。固定最终checkpoint；源60000步，FT/GSMF各4000步，batch2/crop512，AdamW/PolyLR，FP32。', '',
             'A=Cityscapes官方val500；B=ACDC fog官方val100。六组保存预测已独立重读，累计矩阵与框架及原始标签复算一致。', '',
             '| 模型 | A mIoU% | B mIoU% | A旧域下降pp | B新域增量pp | A/B等权均值% |',
             '|---|---:|---:|---:|---:|---:|']
    accounting = read(run / 'resource-accounting.json') if (run / 'resource-accounting.json').exists() else None
    if accounting:
        lines[8:8] = ['源训练从原运行iter40000完整恢复模型、优化器、调度器及计数。'
                  'MMEngine 0.8.2原checkpoint未保存RNG及数据迭代器状态，不能声称与不停机逐位一致；'
                  '原损坏iter50000及失败日志保留。资源成本另按恢复前后分段记录。', '']
    for s in STAGES:
        a, b = [evidence['metrics'][s][d]['mIoU'] for d in ('A', 'B')]
        drop = evidence['metrics']['source']['A']['mIoU'] - a
        gain = b - evidence['metrics']['source']['B']['mIoU']
        lines.append('| %s | %.4f | %.4f | %.4f | %.4f | %.4f |' % (s, a, b, drop, gain, (a+b)/2))
    lines += ['', '| 类别 | Source A | Source B | FT A | FT B | GSMF A | GSMF B |',
              '|---|---:|---:|---:|---:|---:|---:|']
    for name in CLASSES:
        values = [evidence['metrics'][s][d]['IoU'][name] for s in STAGES for d in ('A', 'B')]
        lines.append('| ' + name + ' | ' + ' | '.join('null' if v is None else '%.4f' % v for v in values) + ' |')
    lines += ['', '| 模型 | 训练墙钟秒（含周期验证/保存） | 稳态秒/步（含数据） | 峰值allocated MiB | 总/可训练参数 | checkpoint MiB | A/B评价秒 | 部署参数/状态MiB |',
              '|---|---:|---:|---:|---|---:|---|---|']
    for s in STAGES:
        c = summary['costs'][s]
        audit = read(run / s / ('audit-end-%d.json' % (60000 if s == 'source' else 4000)))
        total = c['total_parameters']
        deploy_params = total - 2364691 if s == 'source' else (47832297 if s == 'gsmf' else total)
        lines.append('| %s | %.2f | %.6f | %.2f | %d/%d | %.2f | %.2f/%.2f | %d/%.2f |' % (
            s, (accounting['source_useful_segments_wall_seconds'] if s == 'source' and accounting
                else c['training_wall_seconds']), audit['seconds_per_step_with_data_after_warmup'],
            c['train_peak_allocated_MiB'], total, c['trainable_parameters'],
            c['evaluation']['A']['checkpoint_bytes']/2**20,
            c['evaluation']['A']['seconds'], c['evaluation']['B']['seconds'], deploy_params,
            evidence['models'][s]['deployment_state_bytes']/2**20))
    if accounting:
        lines += ['', '源训练墙钟取原有效段加恢复段：%.2f + %.2f = %.2f秒；原中断后丢失10000次更新，'
                  '计入失败尝试的已观测总墙钟下界为%.2f秒。原有效段截至iter40000文件mtime，'
                  '不含随后验证；源稳态耗时/显存测量取恢复段。精确分段见resource-accounting.json。' % (
                      accounting['source_prior_checkpoint_wall_seconds'], accounting['source_resume_wall_seconds'],
                      accounting['source_useful_segments_wall_seconds'], accounting['source_observed_total_attempts_wall_seconds'])]
    lines += ['', '部署评价为原分辨率滑窗512/stride341、无TTA。A/B评价时间含PNG读取、指标与预测保存，并非纯GPU推理延迟；逐域峰值显存及精确资源见summary JSON。GSMF旧分支调用为0，两域均使用新分支。未另测正式模型GFLOPs。', '',
              '完整六个19×19混淆矩阵（行GT、列预测，类别顺序同上）和精确IoU见本运行 `final-independent-verification.json`；各组原始输出见 `eval_<stage>_<A/B>/`。', '',
              '旧域下降=Source A−增量后A；新域增量=增量后B−Source B；均值按域等权。差值可为负，不预设GSMF优于FT。', '',
              '本结果仅seed0，不能作统计显著性结论。两域跨数据集，地点、设备及场景差异与天气同时存在，不能把差异全部归因于雾天。未使用val选择checkpoint或追加预算。']
    text = '\n'.join(lines) + '\n'
    with (run / 'RESULTS.md').open('x') as f:
        f.write(text)
    current = EXP / 'RESULTS.md'
    shutil.copyfile(current, run / 'RESULTS-before-formal.md')
    tmp = current.with_name('RESULTS.md.formal-tmp')
    tmp.write_text(text)
    tmp.replace(current)


def watch(run, session):
    (run / 'monitor.pid').write_text(str(os.getpid()) + '\n')
    seen = None
    missing = 0
    while True:
        state = read(run / 'status.json') if (run / 'status.json').exists() else {'state': 'starting'}
        if state != seen:
            events = [json.loads(x) for x in (run / 'events.jsonl').read_text().splitlines()] if (run/'events.jsonl').exists() else []
            done = [x['stage'] for x in events if x.get('state') == 'complete']
            detail = '当前阶段：`%s`；已完成：%s。' % (state.get('stage', 'preflight'), ', '.join(done) or '无')
            update_status(run, session, state['state'], detail)
            with (run / 'monitor-events.jsonl').open('a') as f:
                f.write(json.dumps({'time_local': now(), 'observed': state, 'completed': done}) + '\n')
            print(now(), state, flush=True)
            seen = state
        exit_path = session / 'exit-code.txt'
        if exit_path.exists():
            code = int(exit_path.read_text())
            if code != 0:
                update_status(run, session, 'failed', '流水线实际退出码%d；后续依赖阶段停止。失败日志保留，不自动重试。' % code)
                return code if code > 0 else 1
            assert state.get('stage') == 'all' and state['state'] == 'complete'
            update_status(run, session, 'verifying', '训练与六组评价已exit0，正在独立重读最终预测；尚未宣布最终核验完成。')
            evidence, summary = verify(run)
            save(run / 'final-independent-verification.json', evidence)
            publish(run, evidence, summary)
            update_status(run, session, 'complete', '训练流水线exit0，最终独立核验PASS；正式结果及资源成本已写入RESULTS.md。')
            return 0
        pid = state.get('pid')
        if pid:
            try:
                os.kill(pid, 0)
                missing = 0
            except ProcessLookupError:
                missing += 1
                if missing >= 3:
                    save(run / 'monitor-interruption.json', {'time_local': now(), 'state': state,
                         'reason': 'pipeline PID absent and session exit code missing; no fabricated exit code'})
                    update_status(run, session, 'interrupted', '流水线进程消失且缺失实际退出码；保留现状，需核对checkpoint后resume。')
                    return 1
        heartbeat = run / 'monitor-heartbeat.json'
        tmp = run / 'monitor-heartbeat.tmp'
        tmp.write_text(json.dumps({'time_local': now(), 'pid': os.getpid(), 'pipeline_state': state}))
        tmp.replace(heartbeat)
        time.sleep(20)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=['preflight', 'watch', 'verify-debug'])
    p.add_argument('--run', type=Path)
    p.add_argument('--session', type=Path)
    p.add_argument('--output', type=Path)
    args = p.parse_args()
    try:
        if args.action == 'preflight':
            preflight(args.output)
            code = 0
        elif args.action == 'verify-debug':
            evidence, _ = verify(args.run.resolve(), allow_debug=True)
            save(args.output, evidence)
            code = 0
        else:
            code = watch(args.run.resolve(), args.session.resolve())
    except BaseException:
        error = traceback.format_exc()
        print(error, file=sys.stderr, flush=True)
        if args.action == 'watch':
            save(args.run / ('monitor-failure-%d.json' % time.time_ns()), {'time_local': now(), 'error': error})
            update_status(args.run.resolve(), args.session.resolve(), 'monitor_failed',
                          '监测/独立核验失败，查看monitor日志；不声称最终结果通过，不自动重试训练。')
        code = 1
    if args.action == 'watch':
        with (args.run / 'monitor-exit-code.txt').open('x') as f:
            f.write(str(code) + '\n')
    sys.exit(code)
