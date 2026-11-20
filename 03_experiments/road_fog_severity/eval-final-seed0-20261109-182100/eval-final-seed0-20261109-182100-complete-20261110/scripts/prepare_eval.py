#!/usr/bin/env python3
"""Prepare immutable equal-scene manifests for the existing road evaluator.
This is preparation only; precheck all four conditions before full evaluation.
"""
import argparse,csv,hashlib,json,random
from pathlib import Path
BETAS=('0','0.005','0.01','0.02')
def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''): h.update(b)
    return h.hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument('--audit',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    audit=json.loads((a.audit/'audit.json').read_text()); src=a.audit/'available_manifest.csv'
    if sha(src)!=audit['manifest_sha256'] or audit['errors'] or audit['source_id_or_acdc_file_hash_overlap'] or audit['acdc_decoded_rgb_hash_overlap']: raise ValueError('audit failed or manifest changed')
    common=sorted(audit['common_scene_ids'])
    if len(common)<6: raise ValueError('need at least six four-condition common scenes; found %d' % len(common))
    rows=list(csv.DictReader(src.open())); mapping={(r['base_scene_id'],r['beta']):r for r in rows}
    if len(mapping)!=len(rows): raise ValueError('duplicate scene and beta')
    for s in common:
        for b in BETAS:
            r=mapping[(s,b)]
            if sha(r['image'])!=r['image_sha256'] or sha(r['gt'])!=r['gt_sha256']: raise ValueError('data changed since audit: '+s+' '+b)
    a.out.mkdir(parents=True,exist_ok=False)
    samples=sorted(random.Random(20261109).sample(common,6))
    (a.out/'sample_ids.json').write_text(json.dumps(dict(seed=20261109,algorithm='python random.Random.sample from sorted common scene ids, then sort',ids=samples),indent=2)+'\n')
    (a.out/'scene_ids.json').write_text(json.dumps(common,indent=2)+'\n')
    for kind,ids in [('precheck',common[:2]),('full',common)]:
        for beta in BETAS:
            d=a.out/kind/beta; d.mkdir(parents=True)
            records=[]
            for s in ids:
                r=mapping[(s,beta)]
                records.append(dict(id=s,domain='A',split='val',image=r['image'],label=r['gt'],encoding='labelIds'))
            f=d/'A_val_debug.jsonl';f.write_text(''.join(json.dumps(r)+'\n' for r in records))
            (d/'audit.json').write_text(json.dumps(dict(status='PASS',full_official_counts=False,manifest_sha256={f.name:sha(f)},actual_n=len(ids),source_manifest_sha256=audit['manifest_sha256'],note='Existing evaluator debug flag selects this explicitly named manifest; native sliding inference is unchanged.'),indent=2)+'\n')
    print('prepared common scenes:',len(common),'sample ids:',samples)
if __name__=='__main__':main()
