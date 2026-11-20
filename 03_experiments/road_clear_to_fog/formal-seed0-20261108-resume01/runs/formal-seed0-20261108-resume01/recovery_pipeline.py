#!/usr/bin/env python
"""One authorized seed0 recovery chain, using existing train/resume/eval entries."""
import argparse
from datetime import datetime
import gc
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tarfile
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from formal_control import preflight, read, save, sha
from tools.road.pipeline import code_fingerprint


def main(args):
    import torch
    os.chdir(ROOT)
    parent = args.parent.resolve()
    checkpoint = args.checkpoint.resolve()
    output = args.output.resolve()
    assert args.confirmed_seed0
    output.mkdir(parents=True, exist_ok=False)
    active = 'recovery_preflight'

    def event(**kwargs):
        state = dict(time_utc=datetime.utcnow().isoformat() + 'Z', pid=os.getpid(), **kwargs)
        with (output / 'events.jsonl').open('a') as f:
            f.write(json.dumps(state) + '\n')
        tmp = output / 'status.tmp'
        tmp.write_text(json.dumps(state, indent=2) + '\n')
        tmp.replace(output / 'status.json')

    def run(name, arguments):
        nonlocal active
        active = name
        command = [sys.executable, str(ROOT / 'tools/road/run.py')] + list(map(str, arguments))
        event(stage=name, state='running', command=command)
        with (output / (name + '-command.sh')).open('x') as f:
            f.write(shlex.join(command) + '\n')
        start = time.monotonic()
        with (output / (name + '-console.log')).open('x') as log:
            process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT)
            event(stage=name, state='running', child_pid=process.pid, command=command)
            code = process.wait()
        event(stage=name, state='complete' if code == 0 else 'failed', exit_code=code,
              seconds=time.monotonic() - start)
        if code:
            raise subprocess.CalledProcessError(code, command)

    try:
        event(stage=active, state='running')
        preflight(output / 'recovery-preflight.json')
        expected = read(parent / 'interruption-audit-20261108-001/diagnosis.json')['recovery_candidate']
        assert checkpoint == parent / expected['path']
        assert sha(checkpoint) == expected['sha256']
        saved = torch.load(str(checkpoint), map_location='cpu')
        assert saved['meta']['iter'] == 40000
        assert {int(v['step']) for v in saved['optimizer']['state'].values() if 'step' in v} == {40000}
        scheduler = saved['param_schedulers'][0]
        assert scheduler['end'] == 60000 and scheduler['_global_step'] == scheduler['last_step'] == 40000
        assert saved['optimizer']['param_groups'][0]['lr'] == scheduler['_last_value'][0]
        save(output / 'recovery-state-before-run.json', dict(
            checkpoint=str(checkpoint), sha256=expected['sha256'], iteration=40000,
            optimizer_steps=40000, scheduler=scheduler, remaining_updates=20000,
            limitation='MMEngine 0.8.2 restores model/optimizer/scheduler/iteration. '
            'Original checkpoint has no RNG or dataloader cursor state; not bitwise equivalent to uninterrupted training.'))
        del saved
        gc.collect()
        fingerprint = code_fingerprint()
        save(output / 'provenance.json', dict(argv=sys.argv, parent_run=str(parent),
             recovery_checkpoint=str(checkpoint), recovery_checkpoint_sha256=expected['sha256'],
             code=fingerprint, seed=0, mode='formal-recovery', source_start=40000, source_end=60000,
             ft_steps=4000, gsmf_steps=4000, python=sys.executable,
             gpu_sharing_authorized=args.allow_shared_gpu,
             git_head=subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()))
        for name, command in [('git-status.txt', ['git', 'status', '--short']),
                              ('git-diff.patch', ['git', 'diff', '--binary'])]:
            with (output / name).open('x') as f:
                subprocess.run(command, stdout=f, check=True)
        with tarfile.open(str(output / 'code-snapshot.tar.gz'), 'x:gz') as tar:
            for name in fingerprint['files']:
                tar.add(str(ROOT / name), arcname=name)
        for name in ('formal_control.py', 'recovery_pipeline.py'):
            shutil.copyfile(Path(__file__).parent / name, output / name)
        event(stage=active, state='complete', exit_code=0)
        active = 'environment'
        event(stage=active, state='running')
        with (output / 'preflight-console.log').open('x') as f:
            subprocess.run([sys.executable, str(ROOT / 'tools/road/preflight.py'),
                            '--output', str(output / 'environment.json')], stdout=f,
                           stderr=subprocess.STDOUT, check=True)
        event(stage=active, state='complete', exit_code=0)

        # Use the existing, smoke-validated full-state resume shell/entry point.
        active = 'train_source'
        (output / 'source').mkdir()
        source_record = output / 'source-session'
        source_record.mkdir()
        command = ['bash', str(ROOT / 'tools/road/resume_session.sh'), str(source_record),
                   sys.executable, 'source', str(output / 'source'), str(checkpoint)]
        with (output / 'train_source-command.sh').open('x') as f:
            f.write(shlex.join(command) + '\n')
        (output / 'train_source-console.log').symlink_to(source_record / 'console.log')
        start = time.monotonic()
        process = subprocess.Popen(command)
        event(stage=active, state='running', child_pid=process.pid, command=command)
        code = process.wait()
        event(stage=active, state='complete' if code == 0 else 'failed', exit_code=code,
              seconds=time.monotonic() - start, resumed_from_iteration=40000)
        if code:
            raise subprocess.CalledProcessError(code, command)

        source = output / 'source/iter_60000.pth'
        assert source.is_file()
        for domain in ('A', 'B'):
            run('eval_source_' + domain, ['eval', '--stage', 'source', '--domain', domain,
                '--checkpoint', source, '--work-dir', output / ('eval_source_' + domain)])
        run('convert', ['convert', '--source', source, '--output', output / 'conversion'])
        for stage in ('ft', 'gsmf'):
            report = read(output / 'conversion/conversion.json')
            assert report['status'] == 'PASS'
            initial = output / 'conversion' / (stage + '_init.pth')
            assert sha(initial) == report['stages'][stage]['sha256']
            run('train_' + stage, ['train', '--stage', stage, '--work-dir', output / stage,
                                  '--load', initial])
            final = output / stage / 'iter_4000.pth'
            assert final.is_file()
            for domain in ('A', 'B'):
                run('eval_' + stage + '_' + domain, ['eval', '--stage', stage, '--domain', domain,
                     '--checkpoint', final, '--work-dir', output / ('eval_' + stage + '_' + domain)])
        run('summary', ['summary', '--directory', output])
        source_seconds = next(x['seconds'] for x in map(json.loads, (output / 'events.jsonl').read_text().splitlines())
                              if x.get('stage') == 'train_source' and x.get('state') == 'complete')
        original_events = [json.loads(x) for x in (parent / 'events.jsonl').read_text().splitlines()]
        begin = next(x['time_utc'] for x in original_events if x.get('stage') == 'train_source' and x.get('state') == 'running')
        # Parse an explicit UTC offset, independent of host timezone.
        started = datetime.fromisoformat(begin.replace('Z', '+00:00')).timestamp()
        useful_prior = checkpoint.stat().st_mtime - started
        interrupted_end = read(parent / 'interruption-audit-20261108-001/diagnosis.json')['last_log_local']
        last_observed = datetime.fromisoformat(interrupted_end.replace(' +08:00', '+08:00')).timestamp()
        save(output / 'resource-accounting.json', dict(
            source_prior_checkpoint_wall_seconds=useful_prior,
            source_resume_wall_seconds=source_seconds,
            source_useful_segments_wall_seconds=useful_prior + source_seconds,
            source_observed_prior_attempt_wall_seconds=last_observed - started,
            source_observed_total_attempts_wall_seconds=last_observed - started + source_seconds,
            source_discarded_updates=10000,
            note='Current summary source training wall time covers resumed 40000..60000 only. '
                 'Prior useful segment ends at iter40000 checkpoint mtime; excludes its subsequent validation. '
                 'Interrupted-attempt duration ends at last observed log and is a lower bound.'))
        event(stage='all', state='complete', exit_code=0)
    except BaseException as error:
        code = error.returncode if isinstance(error, subprocess.CalledProcessError) else 1
        event(stage=active, state='failed', exit_code=code, error=repr(error))
        save(output / ('failure-%d.json' % time.time_ns()), dict(stage=active, error=repr(error), exit_code=code))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--parent', type=Path, required=True)
    parser.add_argument('--checkpoint', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--confirmed-seed0', action='store_true')
    parser.add_argument('--allow-shared-gpu', action='store_true')
    main(parser.parse_args())
