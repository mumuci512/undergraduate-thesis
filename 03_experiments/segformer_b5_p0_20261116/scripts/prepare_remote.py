import hashlib, json, subprocess, urllib.request
from pathlib import Path
from datetime import datetime, timezone
import torch, mmseg
from mmengine.config import Config

root = Path('/home/ysheng4/research/segformer_b5_p0_20261116')
out = root
out.mkdir(exist_ok=True)
assert not (out/'prepare.json').exists(), 'Existing P0 run: inspect before reuse'
url = ('https://download.openmmlab.com/mmsegmentation/v0.5/segformer/'
       'segformer_mit-b5_8x1_1024x1024_160k_cityscapes/'
       'segformer_mit-b5_8x1_1024x1024_160k_cityscapes_20211206_072934-87a052ec.pth')
weight = out/'source_cityscapes_official.pth'
if not weight.exists():
    print('DOWNLOAD_START', url, flush=True)
    urllib.request.urlretrieve(url, str(weight)+'.part')
    Path(str(weight)+'.part').rename(weight)
sha = hashlib.sha256(weight.read_bytes()).hexdigest()
assert sha.startswith('87a052ec'), sha
cfgpath = Path(mmseg.__file__).parent/'.mim/configs/segformer/segformer_mit-b5_8xb1-160k_cityscapes-1024x1024.py'
cfg = Config.fromfile(str(cfgpath))
cfg.model.backbone.init_cfg = None
cfg.dump(str(out/'official_resolved.py'))
ckpt = torch.load(str(weight), map_location='cpu')
print('CHECKPOINT', len(ckpt['state_dict']), str(ckpt.get('meta', {}))[:2000], flush=True)
from mmseg.utils import register_all_modules
from mmseg.registry import MODELS
register_all_modules()
model = MODELS.build(cfg.model)
model.load_state_dict(ckpt['state_dict'], strict=True)
print('STRICT_LOAD_OK', sum(p.numel() for p in model.parameters()), flush=True)
files = {p.name:str(p) for p in sorted((root/'manifests').glob('*.jsonl'))}
assert all(d+'_'+split+'.jsonl' in files for d in 'ABCDE' for split in ['train','val'])
print('MANIFESTS', files, flush=True)
for name, path in files.items():
    print('MANIFEST', name, sum(1 for _ in open(path)), open(path).readline().strip(), flush=True)
(out/'prepare.json').write_text(json.dumps(dict(
    created_at=datetime.now(timezone.utc).isoformat(), root=str(root),
    output=str(out), checkpoint=str(weight), checkpoint_url=url, checkpoint_sha256=sha,
    checkpoint_bytes=weight.stat().st_size, strict_load=True,
    config=str(cfgpath), parameters=sum(p.numel() for p in model.parameters()),
    source_script_sha256=hashlib.sha256((root/'run_b5_p0.py').read_bytes()).hexdigest(),
    manifests=files), indent=2))
print('PREPARED', out, flush=True)
