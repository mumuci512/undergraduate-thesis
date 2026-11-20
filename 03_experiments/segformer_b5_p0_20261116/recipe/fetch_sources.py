"""Fetch small, official recipe sources; never download model weights."""
import concurrent.futures
import datetime
import hashlib
import json
import pathlib
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent
MMSEG = 'https://raw.githubusercontent.com/open-mmlab/mmsegmentation/v1.2.1/'
SOURCES = {
    'mmseg_v1.2.1_segformer_README.md': MMSEG + 'configs/segformer/README.md',
    'segformer_mit-b5_8xb1-160k_cityscapes-1024x1024.py': MMSEG + 'configs/segformer/segformer_mit-b5_8xb1-160k_cityscapes-1024x1024.py',
    'segformer_mit-b0_8xb1-160k_cityscapes-1024x1024.py': MMSEG + 'configs/segformer/segformer_mit-b0_8xb1-160k_cityscapes-1024x1024.py',
    'base_segformer_mit-b0.py': MMSEG + 'configs/_base_/models/segformer_mit-b0.py',
    'base_cityscapes_1024x1024.py': MMSEG + 'configs/_base_/datasets/cityscapes_1024x1024.py',
    'base_cityscapes.py': MMSEG + 'configs/_base_/datasets/cityscapes.py',
    'base_schedule_160k.py': MMSEG + 'configs/_base_/schedules/schedule_160k.py',
    'base_default_runtime.py': MMSEG + 'configs/_base_/default_runtime.py',
    'mmseg_cityscapes_dataset.py': MMSEG + 'mmseg/datasets/cityscapes.py',
    'mmseg_mit2mmseg_converter.py': MMSEG + 'tools/model_converters/mit2mmseg.py',
    'NVlabs_README.md': 'https://raw.githubusercontent.com/NVlabs/SegFormer/master/README.md',
    'NVlabs_b5_cityscapes.py': 'https://raw.githubusercontent.com/NVlabs/SegFormer/master/local_configs/segformer/B5/segformer.b5.1024x1024.city.160k.py',
    'SATS_README.md': 'https://raw.githubusercontent.com/QIU023/SATS_Continual_Semantic_Seg/master/README.md',
    'SATS_argparser.py': 'https://raw.githubusercontent.com/QIU023/SATS_Continual_Semantic_Seg/master/argparser.py',
    'SATS_run.py': 'https://raw.githubusercontent.com/QIU023/SATS_Continual_Semantic_Seg/master/run.py',
    'MILE_arxiv_v2.html': 'https://arxiv.org/html/2605.03555v2',
    'MILE_arxiv_abstract.html': 'https://arxiv.org/abs/2605.03555v2',
    'SegFormer_arxiv.html': 'https://arxiv.org/html/2105.15203',
}

def fetch(pair):
    name, url = pair
    result = {'file': name, 'url': url}
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'research-recipe-audit/1.0'})
        with urllib.request.urlopen(req, timeout=35) as response:
            data = response.read(3_000_000)
            result.update({'resolved_url': response.url, 'status': response.status})
        (ROOT / name).write_bytes(data)
        result.update({'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
    except Exception as e:
        result['error'] = str(e)
    print(json.dumps(result, ensure_ascii=False), flush=True)
    return result

if __name__ == '__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(fetch, SOURCES.items()))
    report = {'retrieved_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'sources': results}
    (ROOT / 'SOURCE_MANIFEST.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
