import sys,json,itertools,subprocess
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
import torch
from mmengine.dataset import InfiniteSampler
from road_dil.protocol import write_json,sha256
from road_dil.checkpoints import convert_incremental,convert
p=Path('experiments/road_five_domain/prepare-20261111-140000').resolve();rows={}
for m in ('ft','gsmf'):
 a=torch.load(str(p/'conversion/source-seed1-B'/(m+'_init.pth')),map_location='cpu');b=torch.load(str(p/'conversion/source-seed2-B'/(m+'_init.pth')),map_location='cpu');assert a['state_dict'].keys()==b['state_dict'].keys() and all(torch.equal(a['state_dict'][k],b['state_dict'][k]) for k in a['state_dict']);assert a['meta']['parent_sha256']==b['meta']['parent_sha256'];rows[m]=dict(tensors=len(a['state_dict']),seed1_seed2_weights_all_exact=True,same_Source_sha256=a['meta']['parent_sha256']);del a,b
sequences={str(s):list(itertools.islice(iter(InfiniteSampler(list(range(400)),shuffle=True,seed=s)),8)) for s in (0,1,2)};assert len({tuple(v) for v in sequences.values()})==3
rejected=[]
for label,call in [('nonconsecutive incremental order',lambda:convert_incremental('unused',p/'must-not-create','ft','unused','B','E',1,'ABCDE')),('Source wrong first domain',lambda:convert('unused',p/'must-not-create',('ft',),'B',0,'AEDCB'))]:
 try:call()
 except ValueError:rejected.append(label)
 else:raise AssertionError(label)
args=[sys.executable,'tools/road/run.py','train','--stage','ft','--manifests',str(p/'data'),'--work-dir',str(p/'must-not-create'),'--train-domain','D','--debug','--steps','4','--cpu']
r=subprocess.run(args,capture_output=True,text=True);assert r.returncode and 'D/E require an explicit --order' in r.stderr and not (p/'must-not-create').exists()
write_json(p/'extra-seed-stage-contracts.json',dict(status='PASS',weight_initializations=rows,sampler_first8=sequences,rejected=rejected+['D/E without explicit order'],negative_cli=dict(command=args,exit_code=r.returncode,stderr=r.stderr),optimization_steps=0))
print('PASS extra seed and stage contracts')
