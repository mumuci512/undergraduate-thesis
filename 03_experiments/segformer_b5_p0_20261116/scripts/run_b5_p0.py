"""Bounded B5 resource calibration and immutable official-source evaluation.

Run with the existing package environment from this independent project root.
No original training code or data are modified. This is not a MILE reproduction.
"""
import argparse
import gc
import hashlib
import json
import random
import subprocess
import time
from pathlib import Path

import cv2
import mmcv
import mmengine
import mmseg
import numpy as np
import torch
from PIL import Image
from mmcv.transforms import Compose
from mmengine.config import Config
from mmengine.model import revert_sync_batchnorm
from mmengine.optim import build_optim_wrapper
from mmseg.registry import MODELS
from mmseg.utils import register_all_modules

ROOT = Path('/home/ysheng4/research/segformer_b5_p0_20261116')
OUT = ROOT
PREP = json.loads((OUT/'prepare.json').read_text())
ID_MAP = {7:0,8:1,11:2,12:3,13:4,17:5,19:6,20:7,21:8,22:9,
          23:10,24:11,25:12,26:13,27:14,28:15,31:16,32:17,33:18}

def dump(path, obj):
    path.write_text(json.dumps(obj, indent=2, allow_nan=False))

def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(4*1024*1024), b''):
            h.update(b)
    return h.hexdigest()

def fingerprint(model):
    h = hashlib.sha256()
    for k, v in model.state_dict().items():
        h.update(k.encode())
        h.update(v.detach().cpu().numpy().tobytes())
    return h.hexdigest()

def model_and_cfg(checkpointing=False):
    cfg = Config.fromfile(str(OUT/'official_resolved.py'))
    cfg.model.backbone.with_cp = checkpointing
    model = MODELS.build(cfg.model)
    # Full public segmentation checkpoint: reject all missing/unexpected keys.
    model.load_state_dict(torch.load(PREP['checkpoint'], map_location='cpu')['state_dict'], strict=True)
    model = revert_sync_batchnorm(model).cuda()
    cfg.model.decode_head.norm_cfg.type = 'BN'
    return model, cfg

def records(name):
    return [json.loads(x) for x in Path(PREP['manifests'][name]).read_text().splitlines()]

def label(row):
    arr = np.array(Image.open(row['label']))
    assert arr.ndim == 2
    if row['encoding'] == 'labelIds':
        mapped = np.full_like(arr, 255)
        for k, v in ID_MAP.items():
            mapped[arr == k] = v
        arr = mapped
    else:
        assert row['encoding'] == 'trainIds', row['encoding']
    assert np.isin(arr, list(range(19))+[255]).all()
    return arr

def audit():
    result = {}
    manifests = OUT/'manifests'
    manifests.mkdir(exist_ok=True)
    for key, source in PREP['manifests'].items():
        rows = records(key)
        # Keep the exact historical split with path and existing file hashes.
        (manifests/key).write_bytes(Path(source).read_bytes())
        missing = [r['id'] for r in rows if not Path(r['image']).is_file() or not Path(r['label']).is_file()]
        assert not missing, missing
        result[key] = dict(count=len(rows), sha256=sha(source),
                           encodings=sorted(set(r['encoding'] for r in rows)),
                           sequences=sorted(set(r['sequence'] for r in rows)),
                           first_label_values=np.unique(label(rows[0])).tolist(),
                           all_paths_exist=True)
    for d in 'ABCDE':
        tr, va = records(d+'_train.jsonl'), records(d+'_val.jsonl')
        assert not set(r['image'] for r in tr) & set(r['image'] for r in va)
        assert not set(r['image_sha256'] for r in tr) & set(r['image_sha256'] for r in va)
        result[d+'_isolation'] = dict(
            exact_image_overlap=0,
            shared_sequence_names=sorted(set(r['sequence'] for r in tr) & set(r['sequence'] for r in va)))
    dump(OUT/'data_audit.json', result)
    return result

class ResourceDataset(torch.utils.data.Dataset):
    def __init__(self):
        self.rows = records('B_train.jsonl')[:32]
        self.pipeline = Compose([
            dict(type='LoadImageFromFile'), dict(type='LoadAnnotations'),
            dict(type='RandomResize', scale=(2048,1024), ratio_range=(0.5,2.0), keep_ratio=True),
            dict(type='RandomCrop', crop_size=(1024,1024), cat_max_ratio=0.75),
            dict(type='RandomFlip', prob=0.5), dict(type='PhotoMetricDistortion'),
            dict(type='PackSegInputs')])
    def __len__(self):
        return len(self.rows)
    def __getitem__(self, i):
        r = self.rows[i]
        assert r['encoding'] == 'trainIds'
        return self.pipeline(dict(img_path=r['image'], seg_map_path=r['label'],
                                  reduce_zero_label=False, seg_fields=[], label_map=None))

def seed_worker(i):
    seed = torch.initial_seed() % 2**32
    random.seed(seed)
    np.random.seed(seed)

def train(checkpointing):
    tag = 'train_amp_cp' if checkpointing else 'train_amp_scale256'
    dest = OUT/tag
    dest.mkdir(exist_ok=True)
    assert not (dest/'result.json').exists(), 'Refuse overwrite completed run'
    model, cfg = model_and_cfg(checkpointing)
    cfg.optim_wrapper.optimizer.lr = 6e-5
    cfg.dump(str(dest/'resolved.py'))
    before = fingerprint(model)
    model.train()
    optimizer = build_optim_wrapper(model, cfg.optim_wrapper).optimizer
    scaler = torch.cuda.amp.GradScaler(init_scale=256)
    loader = torch.utils.data.DataLoader(ResourceDataset(), batch_size=1, num_workers=2,
        shuffle=True, collate_fn=mmengine.dataset.pseudo_collate, worker_init_fn=seed_worker,
        persistent_workers=True, pin_memory=True)
    it = iter(loader)
    torch.cuda.reset_peak_memory_stats()
    wall = time.perf_counter()
    rows = []
    try:
        with (dest/'steps.jsonl').open('w') as log:
            for step in range(200):
                torch.cuda.synchronize()
                begin = time.perf_counter()
                try:
                    batch = next(it)
                except StopIteration:
                    it = iter(loader)
                    batch = next(it)
                optimizer.zero_grad(set_to_none=True)
                with torch.cuda.amp.autocast():
                    data = model.data_preprocessor(batch, training=True)
                    assert data['inputs'].shape == (1,3,1024,1024)
                    losses = model(**data, mode='loss')
                    loss, _ = model.parse_losses(losses)
                assert torch.isfinite(loss), 'nonfinite loss'
                scaler.scale(loss).backward()
                scaler.unscale_(optimizer)
                grad_norm = torch.stack([p.grad.detach().float().norm() for p in model.parameters()
                                         if p.grad is not None]).norm()
                assert torch.isfinite(grad_norm), 'nonfinite gradients'
                old_scale = scaler.get_scale()
                scaler.step(optimizer)
                scaler.update()
                assert scaler.get_scale() >= old_scale, 'AMP skipped optimizer step'
                torch.cuda.synchronize()
                row = dict(step=step+1, seconds=time.perf_counter()-begin,
                           loss=float(loss.detach()), grad_norm=float(grad_norm),
                           scale=scaler.get_scale())
                rows.append(row)
                log.write(json.dumps(row)+'\n')
                log.flush()
                if (step+1) % 20 == 0:
                    print(tag, row, flush=True)
        training_elapsed = time.perf_counter()-wall
        training_peak_allocated = torch.cuda.max_memory_allocated()/1024**2
        training_peak_reserved = torch.cuda.max_memory_reserved()/1024**2
        after = fingerprint(model)
        assert after != before
        torch.save(dict(state_dict=model.cpu().state_dict(), meta=dict(p0_only=True, steps=200)), dest/'smoke_200.pth')
        reload_model, _ = model_and_cfg(checkpointing)
        reload_model.load_state_dict(torch.load(str(dest/'smoke_200.pth'), map_location='cpu')['state_dict'], strict=True)
        assert fingerprint(reload_model) == after
        result = dict(status='passed', optimizer_steps=200, seed=0,
            training_subset=32, microbatch=1, accumulation=1, effective_batch=1,
            crop=[1024,1024], amp='float16', gradient_checkpointing=checkpointing,
            optimizer='AdamW', lr=6e-5, lr_schedule='constant; resource probe only',
            elapsed_seconds=training_elapsed,
            amp_initial_scale=256,
            warmup_excluded_steps=20,
            mean_step_seconds=float(np.mean([r['seconds'] for r in rows[20:]])),
            median_step_seconds=float(np.median([r['seconds'] for r in rows[20:]])),
            images_per_second=180/sum(r['seconds'] for r in rows[20:]),
            peak_allocated_MiB=training_peak_allocated,
            peak_reserved_MiB=training_peak_reserved,
            fingerprint_before=before, fingerprint_after=after,
            checkpoint_sha256=sha(dest/'smoke_200.pth'), reload_strict_equal=True,
            all_losses_and_gradients_finite=True, all_optimizer_steps_applied=True)
        dump(dest/'result.json', result)
        print('TRAIN_DONE', result, flush=True)
    except Exception as e:
        dump(dest/'failure.json', dict(error=str(e), completed_steps=len(rows),
            peak_allocated_MiB=torch.cuda.max_memory_allocated()/1024**2,
            peak_reserved_MiB=torch.cuda.max_memory_reserved()/1024**2))
        raise

def evaluate():
    model, cfg = model_and_cfg()
    model.eval()
    initial = fingerprint(model)
    cfg.dump(str(OUT/'source_eval_resolved.py'))
    pipeline = Compose([dict(type='LoadImageFromFile'),
        dict(type='Resize', scale=(2048,1024), keep_ratio=True), dict(type='PackSegInputs')])
    results = {}
    for domain in 'ABCDE':
        rows = records(domain+'_val.jsonl')
        cm = np.zeros((19,19), dtype=np.int64)
        times = []
        torch.cuda.reset_peak_memory_stats()
        for index, row in enumerate(rows):
            data = pipeline(dict(img_path=row['image']))
            torch.cuda.synchronize()
            start = time.perf_counter()
            with torch.no_grad():
                pred = model.test_step(dict(inputs=[data['inputs']], data_samples=[data['data_samples']]))[0]
            torch.cuda.synchronize()
            times.append(time.perf_counter()-start)
            yhat = pred.pred_sem_seg.data.cpu().numpy()[0]
            truth = label(row)
            assert yhat.shape == truth.shape
            assert yhat.min() >= 0 and yhat.max() <= 18
            keep = truth != 255
            cm += np.bincount(19*truth[keep].astype(np.int64)+yhat[keep], minlength=361).reshape(19,19)
            if (index+1) % 50 == 0:
                print('EVAL', domain, index+1, '/',len(rows), flush=True)
        union = cm.sum(0)+cm.sum(1)-cm.diagonal()
        iou = np.divide(cm.diagonal(),union, out=np.full(19,np.nan),where=union>0)
        assert (union > 0).all(), 'Report absent classes explicitly'
        np.save(OUT/('source_'+domain+'_confusion.npy'),cm)
        np.savetxt(OUT/('source_'+domain+'_confusion.csv'),cm,delimiter=',',fmt='%d')
        results[domain] = dict(count=len(rows), mIoU_percent=float(iou.mean()*100),
            per_class_IoU_percent=(iou*100).tolist(), valid_pixels=int(cm.sum()),
            input_scale=[2048,1024], keep_ratio=True,
            slide_crop=[1024,1024], slide_stride=[768,768], tta=False, fp32=True,
            mean_inference_seconds=float(np.mean(times[1:])),
            peak_allocated_MiB=torch.cuda.max_memory_allocated()/1024**2,
            peak_reserved_MiB=torch.cuda.max_memory_reserved()/1024**2)
        dump(OUT/'source_results.json',results)
        print('EVAL_DONE',domain,results[domain]['mIoU_percent'],flush=True)
    final = fingerprint(model)
    assert initial == final
    dump(OUT/'source_state_check.json', dict(before=initial,after=final,unchanged=True,
        source_checkpoint_sha256=PREP['checkpoint_sha256']))

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('mode', choices=['train','eval','audit'])
    p.add_argument('--checkpointing', action='store_true')
    args = p.parse_args()
    register_all_modules()
    random.seed(0); np.random.seed(0); torch.manual_seed(0); torch.cuda.manual_seed_all(0)
    torch.backends.cudnn.benchmark = False
    cv2.setNumThreads(0)
    torch.set_num_threads(4)
    print('ENV',torch.__version__,mmseg.__version__,mmcv.__version__,mmengine.__version__,flush=True)
    if args.mode == 'audit': audit()
    elif args.mode == 'train': train(args.checkpointing)
    else: evaluate()
