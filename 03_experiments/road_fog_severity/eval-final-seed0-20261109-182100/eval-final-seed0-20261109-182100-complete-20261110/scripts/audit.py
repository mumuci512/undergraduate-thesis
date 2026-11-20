#!/usr/bin/env python3
"""Audit Cityscapes val pairing. Does not extract archives or infer missing fog."""
import argparse, csv, hashlib, json, sys
from pathlib import Path
from PIL import Image

ROOT = Path('/home/ysheng4/research/GSMF-RS-DIL')
DATA = ROOT/'experiments/road_clear_to_fog/data'
BETAS = ('0.005','0.01','0.02')
def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''): h.update(b)
    return h.hexdigest()
def load(p):
    return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]
def scene(r):
    name=Path(r['image']).name; suffix='_leftImg8bit.png'
    if not name.endswith(suffix): raise ValueError('unexpected Cityscapes image name: '+name)
    return name[:-len(suffix)]
def main():
    a=argparse.ArgumentParser(); a.add_argument('--fog-root', type=Path, required=True); a.add_argument('--out',type=Path,required=True); args=a.parse_args()
    args.out.mkdir(parents=True,exist_ok=False)
    audit=json.loads((DATA/'audit.json').read_text())
    for n in ('A_train.jsonl','B_train.jsonl','A_val.jsonl'):
        if sha(DATA/n)!=audit['manifest_sha256'][n]: raise ValueError('training/val manifest changed: '+n)
    va,at,bt=(load(DATA/n) for n in ('A_val.jsonl','A_train.jsonl','B_train.jsonl'))
    assert len(va)==500 and len(at)==2975 and len(bt)==400
    train_scenes={scene(x) for x in at}; train_seq={x['sequence'] for x in at}
    b_hashes={x['image_sha256'] for x in bt}; b_pixels={x['rgb_pixels_sha256'] for x in bt}
    rows=[]; missing=[]; failures=[]; common=[]; seq_overlap=set(); training_overlap=[]; pixel_overlap=[]
    for r in va:
        s=scene(r); city=s.split('_')[0]; im=Path(r['image']); gt=Path(r['label'])
        if r['sequence'] in train_seq: seq_overlap.add(r['sequence'])
        if s in train_scenes or r['image_sha256'] in b_hashes: training_overlap.append(s)
        if r['rgb_pixels_sha256'] in b_pixels: pixel_overlap.append(s)
        if r['encoding']!='labelIds': failures.append([s,'unexpected label encoding'])
        try:
            if sha(im)!=r['image_sha256'] or sha(gt)!=r['label_sha256']: raise ValueError('image or GT hash changed')
            with Image.open(im) as f: size=f.size; f.verify()
            with Image.open(gt) as f: gt_size=f.size; f.verify()
            if size != gt_size: raise ValueError('GT dimensions differ')
        except Exception as e:
            failures.append([s,str(e)]); continue
        paths={'0':im}
        for beta in BETAS:
            p=args.fog_root/'val'/city/(s+'_leftImg8bit_foggy_beta_'+beta+'.png')
            if p.is_file(): paths[beta]=p
            else: missing.append({'base_scene_id':s,'beta':beta,'expected_path':str(p)})
        ok=True
        for beta,p in paths.items():
            try:
                with Image.open(p) as f:
                    if f.size!=size: raise ValueError('dimensions differ')
                    f.verify()
                h=sha(p)
                rows.append(dict(base_scene_id=s,condition='clear' if beta=='0' else 'synthetic_fog',beta=beta,image=str(p),image_sha256=h,gt=str(gt),gt_sha256=r['label_sha256'],gt_encoding='labelIds',official_split='Cityscapes fine val',width=size[0],height=size[1]))
            except Exception as e: failures.append([s,beta,str(e)]);ok=False
        if len(paths)==4 and ok: common.append(s)
    with (args.out/'available_manifest.csv').open('w',newline='') as f:
        fields=['base_scene_id','condition','beta','image','image_sha256','gt','gt_sha256','gt_encoding','official_split','width','height']; w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
    (args.out/'missing.json').write_text(json.dumps(missing,indent=2)+'\n')
    status=dict(clear_count=len(va),training_city_count=len(at),training_acdc_fog_count=len(bt),available_conditions=len(rows),common_complete_count=len(common),common_scene_ids=common,missing_counts={b:sum(x['beta']==b for x in missing) for b in BETAS},errors=failures,source_id_or_acdc_file_hash_overlap=training_overlap,acdc_decoded_rgb_hash_overlap=pixel_overlap,source_sequence_overlap=sorted(seq_overlap),notes=['GT labelIds to trainIds once; 255 ignored', 'Train manifest hashes match prior audit; training file bytes not rehashed by this script', 'ACDC and Cityscapes naming differs; frame identity/geographical separation across datasets not established', 'No claim about uninspected neighboring frames or geography', 'Pairing by official base identifiers and image size; content alignment depends on official files'], manifest_sha256=sha(args.out/'available_manifest.csv'))
    (args.out/'audit.json').write_text(json.dumps(status,indent=2,ensure_ascii=False)+'\n'); print(json.dumps({k:v for k,v in status.items() if k not in ('common_scene_ids',)},ensure_ascii=False))
    if failures or training_overlap or pixel_overlap: sys.exit(1)
if __name__=='__main__': main()
