"""Adapt stage A's accepted verification, without changing fingerprinted training code."""
from pathlib import Path
base=Path('experiments/road_five_domain/formal-A-plan-20261111-140000/scripts')
dest=Path('experiments/road_five_domain/prepare-20261111-140000/postprocessing-B')
s=(base/'verify_report_A.py').read_text()
s=s[:s.index(' matrices=read(out/\'stage-matrices.json\');deltas=')]
s=s.replace('stage-A','stage-B').replace("['A'];assert", "['B'];assert")
s=s.replace('verify_conversion_logits_A','verify_conversion_logits_B').replace('verify_nonpersistent_buffers_A','verify_nonpersistent_buffers_B')
s=s.replace("key,m,d=row['key'],row['method'],row['domain'];", "key,m,d,seed=row['key'],row['method'],row['domain'],row['seed'];")
s=s.replace("inv['seed']==0", "inv['seed']==seed").replace('False,d,0,', 'False,d,seed,').replace('True,d,0,', 'True,d,seed,')
s=s.replace('scheduler_end=4000,seed=0', 'scheduler_end=4000,seed=seed').replace('cfg.randomness.seed==0', 'cfg.randomness.seed==seed').replace("ck['meta']['seed']==0", "ck['meta']['seed']==seed").replace('domain=d,seed=0,iterations', 'domain=d,seed=seed,iterations')
s=s.replace('assert len(cells)==104', 'assert len(cells)==112')
s=s.replace("==62 and sum(c['images'] for c in checks if c['provenance']=='new')==15878", "==104 and sum(c['images'] for c in checks if c['provenance']=='new')==26496")
s+='''
 from analysis_B import report
 report(prep,run,out,training,cells)
 print('PASS phase B: 16 training/64 checkpoints; 104 new/8 Source reused; independent verification/report')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--prepare',required=True);p.add_argument('--run',required=True);a=p.parse_args();main(a.prepare,a.run)
'''
(dest/'verify_report_B.py').write_text(s)
s=(base/'verify_conversion_logits_A.py').read_text().replace("['A']['runs']", "['B']['runs']")
s=s.replace("parent=torch.load(row['parent'],map_location='cpu');model=build(m).cuda();", "parent=torch.load(row['parent'],map_location='cpu');parent_method='source' if row['parent_domain']=='A' else m;model=build(parent_method).cuda();")
s=s.replace("expected=output();assert expected.shape", "expected=output(parent_method=='source');assert expected.shape")
s=s.replace('all six formal','all sixteen formal')
(dest/'verify_conversion_logits_B.py').write_text(s)
(dest/'verify_nonpersistent_buffers_B.py').write_text((base/'verify_nonpersistent_buffers_A.py').read_text().replace("('source','ft','gsmf','lwf')", "('source','ft','gsmf')"))
print('Generated B verification using accepted A checks; no training code modified')
