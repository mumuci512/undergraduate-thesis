"""Capture official log and version sources used in the bounded deviation audit.

This script does not evaluate a model or modify P0 execution evidence.
"""
import concurrent.futures
import datetime
import difflib
import hashlib
import json
import pathlib
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent
MMSEG = 'https://raw.githubusercontent.com/open-mmlab/mmsegmentation/'
LOG = ('https://download.openmmlab.com/mmsegmentation/v0.5/segformer/'
       'segformer_mit-b5_8x1_1024x1024_160k_cityscapes/'
       'segformer_mit-b5_8x1_1024x1024_160k_cityscapes_20211206_072934.log.json')
SOURCES = {'official_cityscapes_training_log_20211206.jsonl': LOG}
for version in ['v0.19.0', 'v1.2.1']:
    for name, path in [
        ('encoder_decoder', 'mmseg/models/segmentors/encoder_decoder.py'),
        ('mit', 'mmseg/models/backbones/mit.py'),
        ('embed', 'mmseg/models/utils/embed.py'),
        ('segformer_head', 'mmseg/models/decode_heads/segformer_head.py'),
    ]:
        SOURCES['version_' + version + '_' + name + '.py'] = MMSEG + version + '/' + path
SOURCES['version_v1.2.1_segmentor_base.py'] = MMSEG + 'v1.2.1/mmseg/models/segmentors/base.py'
SOURCES['version_v1.2.1_decode_head.py'] = MMSEG + 'v1.2.1/mmseg/models/decode_heads/decode_head.py'

def fetch(pair):
    name, url = pair
    with urllib.request.urlopen(url, timeout=35) as response:
        data = response.read(4_000_000)
    (ROOT / name).write_bytes(data)
    record = {'file': name, 'url': url, 'bytes': len(data),
              'sha256': hashlib.sha256(data).hexdigest(),
              'retrieved_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}
    print(json.dumps(record), flush=True)
    return record

def derived(name, data, source_files):
    raw = data.encode('utf-8')
    (ROOT / name).write_bytes(raw)
    return {'file': name, 'source_files': source_files,
            'provenance': 'deterministically derived from captured official source files',
            'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}

if __name__ == '__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        records = list(pool.map(fetch, SOURCES.items()))
    log_name = 'official_cityscapes_training_log_20211206.jsonl'
    rows = [json.loads(line) for line in (ROOT / log_name).read_text(encoding='utf-8').splitlines()]
    vals = [row for row in rows if row.get('mode') == 'val']
    summary = {
        'source': log_name,
        'val_count': len(vals),
        'val_sequence_mIoU_percent': [100 * row['mIoU'] for row in vals],
        'last_val': vals[-1],
        'max_logged_val_mIoU_percent': 100 * max(row['mIoU'] for row in vals),
        'p0_observed_CS_mIoU_percent': 82.0842075,
        'published_CS_SS_mIoU_percent': 82.25,
        'p0_minus_published_pp': 82.0842075 - 82.25,
        'causal_attribution': 'not established; version source differences are leads only',
        'comparison_limit': 'v0.19.0 tag is not an exact reconstruction of upstream 0.19.0+ commit/environment',
    }
    records.append(derived('source_deviation_summary.json', json.dumps(summary, indent=2) + '\n', [log_name]))
    parts = []
    files = []
    for name in ['encoder_decoder', 'mit', 'embed', 'segformer_head']:
        old = 'version_v0.19.0_' + name + '.py'
        new = 'version_v1.2.1_' + name + '.py'
        files.extend([old, new])
        parts.append(''.join(difflib.unified_diff(
            (ROOT / old).read_text(encoding='utf-8').splitlines(True),
            (ROOT / new).read_text(encoding='utf-8').splitlines(True),
            fromfile=old, tofile=new, n=3)))
    records.append(derived('mmseg_v0.19.0_vs_v1.2.1.diff', '\n'.join(parts), files))
    manifest_path = ROOT / 'SOURCE_MANIFEST.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    names = {record['file'] for record in records}
    manifest['sources'] = [r for r in manifest['sources'] if r['file'] not in names] + records
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
