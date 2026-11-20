#!/usr/bin/env python
"""No optimization: each formal parent -> initialization logits and independent disk reload."""
import argparse,gc,json,sys,time
from pathlib import Path
import numpy as np
import torch
from PIL import Image
ROOT=Path('/home/ysheng4/research/GSMF-RS-DIL');sys.path.insert(0,str(ROOT))
from road_dil.protocol import write_json,sha256
from road_dil.checkpoints import build,assert_state
from road_dil.hooks import tensor_hash

def main(prep,run):
 prep=Path(prep).resolve();run=Path(run).resolve();rows=[]
 for row in json.loads((prep/'formal-plans.json').read_text())['C']['runs']:
  t=time.perf_counter();m,d=row['method'],row['domain'];r=json.loads((prep/('data/'+d+'_val_debug.jsonl')).read_text().splitlines()[0]);rgb=np.array(Image.open(r['image']))[:512,:512].astype(np.float32);x=torch.from_numpy(((rgb-[123.675,116.28,103.53])/[58.395,57.12,57.375]).astype(np.float32)).permute(2,0,1)[None].cuda()
  parent=torch.load(row['parent'],map_location='cpu');parent_hash=sha256(row['parent']);parent_method='source' if row['parent_domain']=='A' else m;model=build(parent_method).cuda();assert_state(parent['state_dict'],model);model.eval()
  def output(teacher=False):
   with torch.no_grad():return (model.decode_head(model.backbone(x)) if m=='ft' or teacher else model.decode_head_1(model.backbone_1(x))).cpu()
  init=run/'initialization'/row['key']/(m+'_init.pth');initial=torch.load(str(init),map_location='cpu');assert set(initial)=={'state_dict','meta'};mapping=json.loads((init.parent/'conversion.json').read_text());report=mapping['stages'][m] if row['parent_domain']=='A' else mapping;keys=report['keys'];assert {v['target'] for v in keys}==set(initial['state_dict']) and len(keys)==len(initial['state_dict'])
  for v in keys:
   target=initial['state_dict'][v['target']];source=parent['state_dict'][v['source']];assert torch.equal(target,source) and list(target.shape)==v['shape'] and tensor_hash(target)==v['sha256'] and v['parent_checkpoint_sha256']==parent_hash
   if m=='gsmf' and v['target'].startswith(('backbone.','decode_head.')):
    sk=v['target'].replace('backbone.','backbone_1.',1).replace('decode_head.','decode_head_1.',1);assert target.data_ptr()!=initial['state_dict'][sk].data_ptr()
  del initial
  expected=output(parent_method=='source');assert expected.shape[1]==19;del model,parent;gc.collect();torch.cuda.empty_cache();init=run/'initialization'/row['key']/(m+'_init.pth');model=build(m).cuda();assert_state(torch.load(str(init),map_location='cpu')['state_dict'],model);model.eval();student=output();teacher=output(True) if m!='ft' else student;assert torch.equal(expected,student) and torch.equal(expected,teacher);del model;gc.collect();torch.cuda.empty_cache()
  model=build(m).cuda();assert_state(torch.load(str(init),map_location='cpu')['state_dict'],model);model.eval();assert torch.equal(expected,output());rows.append(dict(run=row['key'],parent_sha256=sha256(row['parent']),initialization_sha256=sha256(init),image_sha256=r['image_sha256'],input='normalized top-left 512x512 real RGB',target_tensors=len(keys),all_tensor_values_shapes_hashes_and_key_sets_exact=True,independent_teacher_student_storage=True,student_and_teacher_max_abs_error=0,independent_reload_equal=True,seconds=time.perf_counter()-t));del model;gc.collect();torch.cuda.empty_cache()
 write_json(run/'formal-conversion-logits-check.json',dict(status='PASS',optimization_steps=0,rows=rows));print('PASS all eight formal parent/student/teacher real logits and independent reload')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--prepare',required=True);p.add_argument('--run',required=True);a=p.parse_args();main(a.prepare,a.run)
