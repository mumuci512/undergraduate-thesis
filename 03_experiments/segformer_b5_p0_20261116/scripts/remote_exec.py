"""Run a UTF-8 script over the existing SSH alias; preserve exact output."""
import argparse
from pathlib import Path
import subprocess

p = argparse.ArgumentParser()
p.add_argument('script', type=Path)
p.add_argument('--python', action='store_true')
p.add_argument('--log', type=Path, required=True)
a = p.parse_args()
remote = 'bash -s'
if a.python:
    remote = ('cd /home/ysheng4/research/segformer_b5_p0_20261116 && env -u PYTHONPATH '
              '/home/ysheng4/miniconda3/envs/GSMF_RS_DIL/bin/python -')
cmd = ['ssh', '-F', 'C:/Users/sissi/.ssh/config', '-o', 'BatchMode=yes',
       '-o', 'ConnectTimeout=15', 'home-wsl', remote]
a.log.parent.mkdir(parents=True, exist_ok=True)
with a.log.open('wb') as output:
    proc = subprocess.run(cmd, input=a.script.read_bytes().replace(b'\r\n', b'\n'),
                          stdout=output, stderr=subprocess.STDOUT)
print(a.log.read_text(encoding='utf-8', errors='replace'))
raise SystemExit(proc.returncode)
