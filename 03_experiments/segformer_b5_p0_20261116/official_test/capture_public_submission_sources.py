"""Capture only public ACDC HTML/JS and guides; no login, POST or credentials."""
import concurrent.futures
import datetime
import hashlib
import json
import pathlib
import re
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent
PUBLIC = ROOT / 'public_sources'
PUBLIC.mkdir(exist_ok=True)
BASE = 'https://acdc.vision.ee.ethz.ch/'
records = []

def get(pair):
    name, url = pair
    req = urllib.request.Request(url, headers={'User-Agent': 'ACDC-protocol-audit/1.0'})
    with urllib.request.urlopen(req, timeout=40) as response:
        data = response.read(3_000_000)
        resolved = response.url
    (PUBLIC / name).write_bytes(data)
    result = {'file': 'public_sources/' + name, 'url': url, 'resolved_url': resolved,
              'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
              'retrieved_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}
    print(json.dumps(result), flush=True)
    return result

if __name__ == '__main__':
    records.append(get(('submit.html', BASE + 'submit')))
    html = (PUBLIC / 'submit.html').read_text(encoding='utf-8')
    paths = sorted(set(re.findall(r'(?:href|src)=(?:"|\x27)?(/js/(?:app\.|chunk-)[^\s"\x27<>]+\.js)', html)))
    paths = [path for path in paths if 'vendors' not in path and 'legacy' not in path]
    assets = [(path.rsplit('/', 1)[-1], urllib.parse.urljoin(BASE, path)) for path in paths]
    assets.append(('ACDC_Challenge_2023-guidelines.pdf', BASE + 'other/ACDC_Challenge_2023-guidelines.pdf'))
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        for future in [pool.submit(get, item) for item in assets]:
            try:
                records.append(future.result())
            except Exception as exc:
                records.append({'error': str(exc)})
    (ROOT / 'PROTOCOL_SOURCE_MANIFEST.json').write_text(json.dumps({'sources': records}, indent=2), encoding='utf-8')
