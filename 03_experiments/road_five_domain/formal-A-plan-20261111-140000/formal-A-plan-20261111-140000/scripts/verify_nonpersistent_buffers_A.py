#!/usr/bin/env python
"""No optimization or network inference: audit every nonpersistent buffer and all native val preprocessing."""
import argparse,gc,hashlib,inspect,json,sys,time
from pathlib import Path
import numpy as np
from PIL import Image
import torch
ROOT=Path('/home/ysheng4/research/GSMF-RS-DIL');sys.path.insert(0,str(ROOT))
from road_dil.protocol import sha256,write_json
from road_dil.checkpoints import build
from tools.road.run import cfg_for
from tools.road.five_common import CONDITIONS
from mmseg.structures import SegDataSample

def records(p):return [json.loads(x) for x in Path(p).read_text().splitlines() if x.strip()]
def main(prep,run):
 prep=Path(prep).resolve();run=Path(run).resolve();start=time.perf_counter();types={};preprocessor=None
 for method in ('source','ft','gsmf','lwf'):
  model=build(method);state=set(model.state_dict());extra={k:v for k,v in model.named_buffers() if k not in state};assert set(extra)=={'data_preprocessor.mean','data_preprocessor.std'}
  cfg=cfg_for(method,prep/'data');values={k:v.flatten().tolist() for k,v in extra.items()}
  for k,v in extra.items():assert torch.equal(v,torch.tensor(cfg.model.data_preprocessor[k.split('.')[-1]],dtype=v.dtype).view(3,1,1))
  types[method]=dict(nonpersistent_keys=sorted(extra),values=values)
  if preprocessor is None:preprocessor=model.data_preprocessor
  del model;gc.collect()
 source=inspect.getsource(type(preprocessor).forward);assert '(_input - self.mean) / self.std' in source and 'self.mean =' not in source and 'self.std =' not in source
 sourcefile=Path(inspect.getfile(type(preprocessor)));(run/'installed-preprocessor-forward-source.txt').write_text(source)
 before={k:v.clone() for k,v in preprocessor.named_buffers()};rows=[]
 for cond,(domain,n) in CONDITIONS.items():
  manifest=prep/'eval-manifests'/cond/'A_val.jsonl' if domain=='A' else prep/('data/'+domain+'_val.jsonl');rs=records(manifest);assert len(rs)==n;ids=[];t=time.perf_counter()
  for r in rs:
   rgb=np.array(Image.open(r['image']).convert('RGB'));bgr=rgb[:,:,::-1].copy();x=torch.from_numpy(bgr).permute(2,0,1);h,w=rgb.shape[:2];sample=SegDataSample();sample.set_metainfo(dict(ori_shape=(h,w),img_shape=(h,w),img_path=r['image']))
   with torch.no_grad():result=preprocessor(dict(inputs=[x],data_samples=[sample]),training=False)
   assert all(torch.equal(v,before[k]) for k,v in preprocessor.named_buffers());assert result['inputs'].shape[1]==3;ids.append(r['id']);del rgb,bgr,x,sample,result
  rows.append(dict(condition=cond,manifest=str(manifest),manifest_sha256=sha256(manifest),images=len(ids),IDs=ids,all_preprocessor_buffers_bit_unchanged=True,seconds=time.perf_counter()-t))
 assert sum(r['images'] for r in rows)==2406
 write_json(run/'nonpersistent-buffer-audit.json',dict(status='PASS',optimization_steps=0,network_forwards=0,model_types=types,processed_images=2406,conditions=rows,installed_preprocessor_source=str(sourcefile),installed_source_sha256=sha256(sourcefile),forward_source_copy_sha256=sha256(run/'installed-preprocessor-forward-source.txt'),seconds=time.perf_counter()-start,scope='All trainable parameters and persistent buffers were compared before/after each full formal evaluation by state_dict hashes. The only nonpersistent buffers for all four model types are fixed mean/std; actual installed forward reads them via non-inplace arithmetic and does not write them. Their equality is additionally checked after preprocessing every native image in all eight validation conditions. This is preprocessing-only evidence, not additional full network evaluation.'))
 print('PASS nonpersistent buffers: only mean/std, read-only implementation, all 2406 native preprocessing calls unchanged')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--prepare',required=True);p.add_argument('--run',required=True);a=p.parse_args();main(a.prepare,a.run)
