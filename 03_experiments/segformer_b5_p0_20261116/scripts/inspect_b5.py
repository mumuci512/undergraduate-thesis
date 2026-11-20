import json
from pathlib import Path
import mmseg
from mmengine.config import Config

root = Path('/home/ysheng4/research/GSMF-RS-DIL')
print('HEAD')
import subprocess
print(subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode())
for folder in [root/'checkpoints/pretrained', root/'configs/road', root/'tools/road']:
    print('FILES', folder, [p.name for p in folder.iterdir()])
base = Path(mmseg.__file__).parent/'.mim/configs/segformer'
print('CONFIG_DIR', base, base.exists())
if base.exists():
    for p in base.glob('*b5*city*'):
        cfg = Config.fromfile(str(p))
        print('B5_CONFIG', str(p), cfg.pretty_text)
for folder in [root/'data/cityscapes', root/'data/acdc']:
    for p in folder.iterdir():
        print('DATA', p, [x.name for x in p.iterdir()] if p.is_dir() else p.stat().st_size)
for p in (root/'configs/road').glob('*.py'):
    if 'source' in p.name:
        print('SOURCE_CONFIG', p, p.read_text()[:14000])
