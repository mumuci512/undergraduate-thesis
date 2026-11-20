"""Export small P0 evidence; leave model weights on the GPU workstation."""
import hashlib
import inspect
import json
import subprocess
import sys
import tarfile
from datetime import datetime, timezone
from pathlib import Path
import torch, mmseg, mmcv, mmengine

root = Path('/home/ysheng4/research/segformer_b5_p0_20261116')
out = root
assert (out/'source_state_check.json').is_file(), 'Source evaluation incomplete'
assert (out/'train_amp_scale256/result.json').is_file(), 'Resource run incomplete'
prep = json.loads((out/'prepare.json').read_text())
probe = json.loads((out/'train_amp_scale256/result.json').read_text())
(out/'effective_probe_config.json').write_text(json.dumps(dict(
    model_config='train_amp_scale256/resolved.py',
    executed_loop='run_b5_p0.py:train; manual loop overrides inherited train_cfg and scheduler',
    optimizer_steps=200, scheduler=None, amp_initial_scale=256,
    amp_dtype='float16', gradient_checkpointing=False, microbatch=1,
    accumulation=1, effective_batch=1, train_domain='Fog',
    subset='B_train.jsonl first 32 entries', num_workers=2,
    learning_rate=probe['lr'], parameter_groups='official paramwise_cfg; head lr x10',
    seed=0, deterministic_algorithms_requested=False),indent=2))
meta = torch.load(prep['checkpoint'], map_location='cpu')['meta']
(out/'checkpoint_meta_config.py').write_text(meta.pop('config'))
(out/'checkpoint_meta.json').write_text(json.dumps(meta,indent=2,default=str))
(out/'pip_freeze.txt').write_bytes(subprocess.check_output([sys.executable,'-m','pip','freeze']))
from mmseg.models.backbones import MixVisionTransformer
from mmseg.models.decode_heads import SegformerHead
from mmseg.models.segmentors import EncoderDecoder
from mmseg.models.data_preprocessor import SegDataPreProcessor
source = out/'runtime_source'
source.mkdir(exist_ok=True)
for cls in [MixVisionTransformer, SegformerHead, EncoderDecoder, SegDataPreProcessor]:
    p = Path(inspect.getfile(cls))
    (source/p.name).write_bytes(p.read_bytes())
(out/'environment.json').write_text(json.dumps(dict(
    exported_at=datetime.now(timezone.utc).isoformat(), python=sys.version,
    torch=torch.__version__, mmseg=mmseg.__version__, mmcv=mmcv.__version__,
    mmengine=mmengine.__version__, cuda=torch.version.cuda,
    gpu=subprocess.check_output(['/usr/lib/wsl/lib/nvidia-smi','--query-gpu=name,memory.total,memory.used,utilization.gpu','--format=csv,noheader']).decode(),
    current_project_root=str(root),
    source_script_sha256=hashlib.sha256((root/'run_b5_p0.py').read_bytes()).hexdigest(),
    checkpoint_location=prep['checkpoint'],
    smoke_checkpoint_location=str(out/'train_amp_scale256/smoke_200.pth')), indent=2))
files = sorted(p for p in out.rglob('*') if p.is_file()
    and p.suffix not in ['.pth','.part','.pyc'] and '__pycache__' not in p.parts
    and 'handoff_exports' not in p.relative_to(out).parts
    and p.name != 'EVIDENCE_MANIFEST.json')
manifest = {p.relative_to(out).as_posix():dict(bytes=p.stat().st_size,
    sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in files}
mf = out/'EVIDENCE_MANIFEST.json'
mf.write_text(json.dumps(manifest,indent=2))
files.append(mf)
archive = root/'handoff_exports/segformer_b5_p0_20261116-current.tar.gz'
archive.parent.mkdir(exist_ok=True)
assert not archive.exists(), 'Refuse overwrite existing archive'
with tarfile.open(str(archive),'w:gz') as tar:
    for p in files:
        tar.add(str(p),arcname=p.relative_to(out).as_posix(),recursive=False)
print(json.dumps(dict(archive=str(archive), bytes=archive.stat().st_size,
    sha256=hashlib.sha256(archive.read_bytes()).hexdigest(), files=len(files))))
