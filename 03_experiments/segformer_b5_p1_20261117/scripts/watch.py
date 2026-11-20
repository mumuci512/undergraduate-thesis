"""Monitor the authorized remote experiment and persist machine-readable status."""
import json
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
REMOTE = '/home/ysheng4/research/segformer_b5_p1_20261117'
SSH = ['ssh', '-F', 'C:/Users/sissi/.ssh/config', '-o', 'BatchMode=yes',
       '-o', 'ConnectTimeout=15', 'home-wsl', 'python3 -']
CODE = '''
import json, pathlib, subprocess, time
root=pathlib.Path(REMOTE_ROOT)
def read(name):
    p=root/name
    return json.loads(p.read_text()) if p.exists() else None
log=root/'execution.log'
lines=log.read_text(errors='replace').splitlines() if log.exists() else []
running=subprocess.run(['pgrep','-af','scripts/run_p1.py'],capture_output=True,text=True).stdout
completed=list((root/'jobs').glob('*/complete.json'))
selections={m:read(m+'_selection.json') for m in ('ft','er','joint')}
progress=read('progress.json')
current=[]
if progress:
    p=root/progress['job']/'steps.jsonl'
    if p.exists():
        current=[json.loads(line) for line in p.read_text().splitlines()]
data=dict(checked_unix=time.time(),progress=progress,running=bool(running.strip()),
    failure=read('failure.json'),completed=read('completed.json'),
    completed_jobs=len(completed),
    selections={m:(v['selected'] if v else None) for m,v in selections.items()},
    current_applied=sum(x['optimizer_applied'] for x in current),
    current_skipped=sum(not x['optimizer_applied'] for x in current),
    current_unique_images=len({x['sample_id'] for x in current}),
    log_age_seconds=time.time()-log.stat().st_mtime if log.exists() else None,
    tail=lines[-8:])
print(json.dumps(data))
'''.replace('REMOTE_ROOT', repr(REMOTE))


def main():
    previous = None
    while True:
        try:
            result = subprocess.run(SSH, input=CODE.encode(), capture_output=True, timeout=55)
            if result.returncode:
                raise RuntimeError(result.stderr.decode(errors='replace'))
            status = json.loads(result.stdout)
            temporary = ROOT / 'STATUS.tmp'
            temporary.write_text(json.dumps(status, indent=2), encoding='utf-8')
            temporary.replace(ROOT / 'STATUS.json')
            progress = status['progress'] or {}
            marker = (progress.get('job'), progress.get('step', 0) // 500,
                      status['completed_jobs'], bool(status['failure']), bool(status['completed']))
            if marker != previous:
                print(json.dumps(status), flush=True)
                previous = marker
            if status['completed']:
                return
            if status['failure'] or not status['running']:
                raise SystemExit('Remote training requires diagnosis. See STATUS.json.')
            if status['log_age_seconds'] is not None and status['log_age_seconds'] > 900:
                print('STALL_CHECK ' + json.dumps(status), flush=True)
        except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as error:
            print('CONNECTION_RETRY ' + str(error), flush=True)
        time.sleep(60)


if __name__ == '__main__':
    main()
