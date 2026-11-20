"""MUSES P0 inventory using official metadata and remote ZIP directories only.

Run --fetch once online, then rerun without it to reproduce counts offline.
No RGB archive is downloaded; HTTP Range is required and checked.
"""
import argparse
import ast
import collections
import csv
import hashlib
import io
import json
import pathlib
import re
import urllib.request
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent
SRC = ROOT / 'sources'
BASE = 'https://muses.ethz.ch/MUSES_packages/'
SDK_SHA = 'ad09c1bca986c2e8a037b514e728b704d70037ed'
MANIFEST = []


def request(url, name, limit=3_000_000, headers=None):
    req = urllib.request.Request(url, headers={'User-Agent': 'MUSES-P0-research-audit', **(headers or {})})
    with urllib.request.urlopen(req, timeout=60) as response:
        if headers and 'Range' in headers and response.status != 206:
            raise RuntimeError('Server did not honor HTTP Range; refusing full download')
        data = response.read(limit + 1)
        if len(data) > limit:
            raise RuntimeError('Response exceeds bounded download limit')
        info = {'url': url, 'file': name, 'bytes': len(data),
                'sha256': hashlib.sha256(data).hexdigest(),
                'status': response.status, 'headers': dict(response.headers)}
    (SRC / name).write_bytes(data)
    MANIFEST.append(info)
    return data


class RemoteZip(io.RawIOBase):
    def __init__(self, url, stem):
        self.url, self.stem, self.pos, self.n = url, stem, 0, 0
        req = urllib.request.Request(url, method='HEAD')
        with urllib.request.urlopen(req, timeout=60) as response:
            self.size = int(response.headers['Content-Length'])
        self.cache = []

    def seekable(self):
        return True

    def readable(self):
        return True

    def tell(self):
        return self.pos

    def seek(self, offset, whence=0):
        self.pos = offset if whence == 0 else self.pos + offset if whence == 1 else self.size + offset
        return self.pos

    def read(self, n=-1):
        if n < 0:
            n = self.size - self.pos
        n = min(n, self.size - self.pos)
        if not n:
            return b''
        if n > 3_000_000:
            raise RuntimeError('Refusing large ZIP read')
        start, end = self.pos, self.pos + n
        for a, b, data in self.cache:
            if a <= start and end <= b:
                self.pos = end
                return data[start-a:end-a]
        self.n += 1
        name = f'{self.stem}.range{self.n:02d}.{start}-{end-1}.bin'
        data = request(self.url, name, headers={'Range': f'bytes={start}-{end-1}'})
        if len(data) != n:
            raise RuntimeError('Incorrect byte-range length')
        self.cache.append((start, end, data))
        self.pos = end
        return data


def fetch():
    SRC.mkdir(parents=True, exist_ok=True)
    for url, name in [
        ('https://muses.ethz.ch/', 'website_index.html'),
        (BASE, 'packages_index.html'),
        ('https://muses.ethz.ch/README.md', 'website_README.md'),
        (BASE + 'README.md', 'packages_README.md'),
        (f'https://raw.githubusercontent.com/timbroed/MUSES/{SDK_SHA}/README.md', 'sdk_README.md'),
        (f'https://raw.githubusercontent.com/timbroed/MUSES/{SDK_SHA}/License.pdf', 'sdk_License.pdf'),
        ('https://raw.githubusercontent.com/mcordts/cityscapesScripts/master/cityscapesscripts/helpers/labels.py', 'cityscapes_labels.py'),
    ]:
        request(url, name)
    data = request(BASE + 'gnss_trainvaltest.zip', 'gnss_trainvaltest.zip')
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        (SRC / 'gnss_archive_listing.json').write_text(json.dumps(z.namelist(), indent=2), encoding='utf-8')
        for name in z.namelist():
            if pathlib.PurePosixPath(name).name.lower() in {'meta.json', 'readme.md', 'license.pdf', 'calib.json'}:
                (SRC / pathlib.PurePosixPath(name).name).write_bytes(z.read(name))
    for stem in ['frame_camera_trainvaltest', 'gt_semantic_trainval']:
        remote = RemoteZip(BASE + stem + '.zip', stem)
        with zipfile.ZipFile(remote) as z:
            infos = [{'name': item.filename, 'bytes_uncompressed': item.file_size,
                      'bytes_compressed': item.compress_size, 'crc32': f'{item.CRC:08x}'} for item in z.infolist()]
        (SRC / (stem + '_listing.json')).write_text(json.dumps(infos, indent=2), encoding='utf-8')
    (SRC / 'FETCH_MANIFEST.json').write_text(json.dumps({'sdk_commit': SDK_SHA, 'sources': MANIFEST}, indent=2), encoding='utf-8')


def fetch_samples():
    """Decode only four train/val RGB-label pairs, never a full image archive."""
    sample_manifest = []
    for stem, suffix in [('frame_camera_trainvaltest', '_frame_camera.png'), ('gt_semantic_trainval', '_gt_labelTrainIds.png')]:
        remote = RemoteZip(BASE + stem + '.zip', stem + '.sample')
        with zipfile.ZipFile(remote) as z:
            for split in ['train', 'val']:
                for weather in ['rain', 'snow']:
                    # Stable lexical first scene makes image/label sampling align.
                    name = sorted(n for n in z.namelist() if f'/{split}/{weather}/night/' in n and n.endswith(suffix))[0]
                    data = z.read(name)
                    local_name = f'sample_{split}_{weather}_{pathlib.PurePosixPath(name).name}'
                    (SRC / local_name).write_bytes(data)
                    sample_manifest.append({'archive_url': BASE + stem + '.zip', 'archive_path': name,
                                            'file': local_name, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
    (SRC / 'SAMPLE_FETCH_MANIFEST.json').write_text(json.dumps({'files': sample_manifest, 'requests': MANIFEST}, indent=2), encoding='utf-8')


def parse_name(name):
    m = re.search(r'/(train|val|test)/(clear|fog|rain|snow)/(day|night)/([^/]+)', '/' + name)
    return m.groups() if m else None


def audit():
    rgb = json.loads((SRC / 'frame_camera_trainvaltest_listing.json').read_text(encoding='utf-8'))
    sem = json.loads((SRC / 'gt_semantic_trainval_listing.json').read_text(encoding='utf-8'))
    rgb_counts, sem_counts = collections.Counter(), collections.Counter()
    rows, rgb_keys, sem_keys = [], set(), set()
    label_paths = {}
    for info in rgb:
        p = parse_name(info['name'])
        if p and p[-1].endswith('_frame_camera.png'):
            split, weather, time, file = p
            scene = file[:-len('_frame_camera.png')]
            rgb_keys.add((split, weather, time, scene))
            rgb_counts[(split, weather, time)] += 1
            rows.append({'split': split, 'weather': weather, 'time_of_day': time,
                         'scene_id': scene, 'rgb_archive_path': info['name'],
                         'rgb_downloaded': False, 'rgb_decoded': False})
    for info in sem:
        p = parse_name(info['name'])
        if p and p[-1].endswith('_labelTrainIds.png'):
            split, weather, time, file = p
            scene = file[:-len('_gt_labelTrainIds.png')]
            sem_keys.add((split, weather, time, scene))
            label_paths[(split, weather, time, scene)] = info['name']
            sem_counts[(split, weather, time)] += 1
    counts = []
    for split in ['train', 'val', 'test']:
        for time in ['day', 'night']:
            for weather in ['clear', 'fog', 'rain', 'snow']:
                k = (split, weather, time)
                counts.append({'split': split, 'time_of_day': time, 'weather': weather,
                               'rgb_entries': rgb_counts[k], 'labelTrainIds_entries': sem_counts[k]})
    for r in rows:
        r['labelTrainIds_in_official_archive'] = (r['split'], r['weather'], r['time_of_day'], r['scene_id']) in sem_keys
        r['labelTrainIds_archive_path'] = label_paths.get((r['split'], r['weather'], r['time_of_day'], r['scene_id']))
    with (ROOT / 'split_counts.tsv').open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=counts[0].keys(), delimiter='\t')
        writer.writeheader()
        writer.writerows(counts)
    with (ROOT / 'rgb_inventory.jsonl').open('w', encoding='utf-8', newline='\n') as f:
        for r in sorted(rows, key=lambda r: (r['split'], r['weather'], r['time_of_day'], r['scene_id'])):
            f.write(json.dumps(r) + '\n')
    keys_by_split = {s: {k[3] for k in rgb_keys if k[0] == s} for s in ['train','val','test']}
    sequences_by_split = {s: {k.split('_frame_')[0] for k in keys_by_split[s]} for s in keys_by_split}
    pairs = [('train','val'), ('train','test'), ('val','test')]
    metadata = json.loads((SRC / 'meta.json').read_text(encoding='utf-8'))
    meta_keys = {(m['split'], m['weather'], m['time_of_day'], scene) for scene, m in metadata.items()}
    label_mapping = []
    for node in ast.walk(ast.parse((SRC / 'cityscapes_labels.py').read_text(encoding='utf-8'))):
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'labels' for t in node.targets):
            for item in node.value.elts:
                args = [ast.literal_eval(v) for v in item.args]
                if 0 <= args[2] <= 18:
                    label_mapping.append({'name': args[0], 'labelId': args[1], 'trainId': args[2]})
    (ROOT / 'cityscapes_19_class_mapping.json').write_text(json.dumps(label_mapping, indent=2), encoding='utf-8')
    decoded_samples = []
    samples = sorted(SRC.glob('sample_*.png'))
    if samples:
        from PIL import Image
        import numpy as np
        for sample in samples:
            with Image.open(sample) as img:
                img.load()
                record = {'file': sample.name, 'size': list(img.size), 'mode': img.mode}
                if sample.name.endswith('_gt_labelTrainIds.png'):
                    values = [int(x) for x in np.unique(np.asarray(img))]
                    record['unique_label_values'] = values
                    record['label_range_valid'] = set(values).issubset(set(range(19)) | {255})
                decoded_samples.append(record)
    (ROOT / 'decoded_sample_checks.json').write_text(json.dumps(decoded_samples, indent=2), encoding='utf-8')
    assert len(rgb_keys) == 2500 == len(rows) == sum(rgb_counts.values())
    assert len(sem_keys) == 1750 == sum(sem_counts.values())
    assert not sem_keys - rgb_keys
    assert not {k for k in rgb_keys if k[0] in {'train','val'}} - sem_keys
    assert meta_keys == rgb_keys
    assert len(label_mapping) == 19 and {r['trainId'] for r in label_mapping} == set(range(19))
    for record in decoded_samples:
        assert record['size'] == [1920, 1080]
        if 'label_range_valid' in record:
            assert record['label_range_valid']
    result = {
        'audit_date': '2026-11-16 Asia/Shanghai',
        'inventory_basis': 'Official HTTP ZIP central-directory entries cross-checked against meta.json; four train/val RGB-label pairs separately decoded',
        'rgb_total': len(rgb_keys), 'labelTrainIds_total': len(sem_keys), 'label_without_rgb_count': len(sem_keys-rgb_keys),
        'rgb_trainval_without_label_count': len({k for k in rgb_keys if k[0] in {'train','val'}}-sem_keys),
        'metadata_total': len(metadata), 'metadata_without_rgb_count': len(meta_keys-rgb_keys),
        'rgb_without_metadata_count': len(rgb_keys-meta_keys),
        'duplicate_scene_ids_across_splits': {f'{a}:{b}': sorted(keys_by_split[a] & keys_by_split[b]) for a,b in pairs},
        'shared_recording_sequence_ids_across_splits': {f'{a}:{b}': sorted(sequences_by_split[a] & sequences_by_split[b]) for a,b in pairs},
        'counts': counts,
        'decoded_samples': len(decoded_samples),
        'limitations': ['Full ZIP-directory presence does not verify all decoded pixels, CRC payload, or label value range; sample verification is separate',
                        'Recording ID overlap alone does not establish geographical leakage; no GPS-distance validation performed']}
    (ROOT / 'audit_summary.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    hashes = [{'file': str(p.relative_to(ROOT)).replace('\\', '/'), 'bytes': p.stat().st_size,
               'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(SRC.iterdir()) if p.is_file()]
    (ROOT / 'SOURCE_HASHES.json').write_text(json.dumps(hashes, indent=2), encoding='utf-8')
    print(json.dumps({'rgb_total':len(rgb_keys), 'labelTrainIds_total':len(sem_keys),
                      'metadata_total':len(metadata), 'decoded_samples':len(decoded_samples),
                      'night_rain_snow':[r for r in counts if r['time_of_day']=='night' and r['weather'] in {'rain','snow'}]}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--fetch', action='store_true')
    parser.add_argument('--fetch-samples', action='store_true')
    args = parser.parse_args()
    if args.fetch:
        fetch()
    if args.fetch_samples:
        fetch_samples()
    audit()
