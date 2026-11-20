"""Transfer scripts or execute them through the established SSH alias."""
import argparse
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
REMOTE = '/home/ysheng4/research/segformer_b5_p1_20261117'
SSH = ['ssh', '-F', 'C:/Users/sissi/.ssh/config', '-o', 'BatchMode=yes',
       '-o', 'ConnectTimeout=15', 'home-wsl']


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['upload', 'exec', 'collect'])
    parser.add_argument('--script', type=Path)
    args = parser.parse_args()
    if args.mode == 'upload':
        files = {str(p.relative_to(ROOT)).replace('\\', '/'): p.read_text(encoding='utf-8')
                 for p in [ROOT / 'plan.json', *sorted(p for p in (ROOT / 'scripts').iterdir()
                     if p.suffix in ('.py', '.sh'))]}
        payload = json.dumps(files, ensure_ascii=True)
        code = ('import json,pathlib\n'
                'root=pathlib.Path(' + repr(REMOTE) + ')\n'
                'files=json.loads(' + repr(payload) + ')\n'
                'for name,content in files.items():\n'
                ' p=root/name\n p.parent.mkdir(parents=True,exist_ok=True)\n'
                ' if name in ("plan.json","scripts/run_p1.py") and p.exists() and (root/"started.json").exists() and p.read_text()!=content:\n'
                '  raise RuntimeError("Active experiment source differs: "+name)\n'
                ' p.write_text(content)\n'
                'print("UPLOADED",len(files),root)\n')
        command = SSH + ['python3 -']
    elif args.mode == 'exec':
        code = args.script.read_text(encoding='utf-8')
        command = SSH + ['bash -s']
    else:
        code = ('import pathlib,tarfile,sys\n'
                'root=pathlib.Path(' + repr(REMOTE) + ')\n'
                'with tarfile.open(fileobj=sys.stdout.buffer,mode="w|gz") as tar:\n'
                ' for p in sorted(root.rglob("*")):\n'
                '  if p.is_file() and p.suffix in (".json",".jsonl",".csv",".npy",".md",".py",".sh",".log",".txt"):\n'
                '   tar.add(p,arcname=str(p.relative_to(root)))\n')
        command = SSH + ['python3 -']
    if args.mode == 'collect':
        with (ROOT / 'evidence.tar.gz').open('wb') as output:
            result = subprocess.run(command, input=code.encode(), stdout=output, check=True)
        print('COLLECTED', ROOT / 'evidence.tar.gz')
    else:
        result = subprocess.run(command, input=code.replace('\r\n', '\n').encode())
    raise SystemExit(result.returncode)


if __name__ == '__main__':
    main()
