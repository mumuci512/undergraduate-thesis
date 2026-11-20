"""Read the first metadata line of an official training log, not the weights."""
import datetime
import hashlib
import json
import pathlib
import urllib.request

root = pathlib.Path(__file__).resolve().parent
url = 'https://download.openmmlab.com/mmsegmentation/v0.5/segformer/segformer_mit-b5_8x1_1024x1024_160k_cityscapes/segformer_mit-b5_8x1_1024x1024_160k_cityscapes_20211206_072934.log.json'
with urllib.request.urlopen(url, timeout=30) as response:
    data = response.readline(200000)
metadata = json.loads(data)
(root / 'official_cityscapes_training_log_first_line.json').write_bytes(data)
(root / 'official_cityscapes_training_config_20211206.py').write_text(metadata['config'], encoding='utf-8')
manifest_path = root / 'SOURCE_MANIFEST.json'
manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
manifest['sources'] = [r for r in manifest['sources'] if r['file'] != 'official_cityscapes_training_log_first_line.json']
manifest['sources'].append({
    'file': 'official_cityscapes_training_log_first_line.json',
    'url': url, 'read_scope': 'first JSONL line only; complete training metadata/config; training iterations not downloaded',
    'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
    'retrieved_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'derived_config_file': 'official_cityscapes_training_config_20211206.py',
})
manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(), 'keys': list(metadata)}, ensure_ascii=False))
