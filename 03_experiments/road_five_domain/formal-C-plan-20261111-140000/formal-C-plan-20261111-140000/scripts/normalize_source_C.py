import csv,json
from pathlib import Path
from road_dil.protocol import sha256,write_json
def read(p):return json.loads(Path(p).read_text())
def normalize_source(prep,run):
 """Make inherited Source provenance explicit; preserve all original driver results."""
 idx=read(run/'results-index.json');out=Path(idx['directory']);cells=read(out/'cells.json')
 assert sha256(out/'cells.json')==idx['cells_sha256']
 a=Path(read(prep/'formal-plans.json')['A']['formal_output']);comp=read(a/'completion.json');ai=read(a/'results-index.json');ao=Path(ai['directory'])
 assert comp['status']=='complete' and comp['handoff']['status']=='PASS'
 assert sha256(ao/'cells.json')==ai['cells_sha256'] and sha256(ao/'training-independent-check.json')==comp['training_check_sha256'] and sha256(ao/'protocol-independent-check.json')==comp['protocol_check_sha256']
 acells=read(ao/'cells.json');ref={c['condition']:c for c in acells if c['model']=='source'}
 write_json(run/'driver-original-results-index.json',idx)
 write_json(out/'driver-original-cells.json',cells)
 inherited=[]
 for c in cells:
  if c['model']!='source':continue
  assert c==ref[c['condition']]
  c['inherited_provenance']=c['provenance'];c['provenance']='reused'
  c['reuse_origin']=dict(phase='A',cells=str(ao/'cells.json'),cells_sha256=ai['cells_sha256'],completion=str(a/'completion.json'),completion_sha256=sha256(a/'completion.json'))
  inherited.append(dict(condition=c['condition'],checkpoint_sha256=c['checkpoint_sha256'],evidence=c['evidence'],original_provenance=c['inherited_provenance']))
 assert len(inherited)==8
 # The original writer is exclusive; atomic replacement is an explicit postprocessing derivation.
 tmp=out/'normalized-cells.tmp';tmp.write_text(json.dumps(cells,indent=2)+'\n');tmp.replace(out/'cells.json')
 with (out/'cells.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=['model','condition','provenance','images','mIoU','checkpoint_sha256','evidence']);w.writeheader();w.writerows({k:c.get(k) for k in w.fieldnames} for c in cells)
 idx.update(cells_sha256=sha256(out/'cells.json'),source_provenance_normalized=True,original_index=str(run/'driver-original-results-index.json'))
 tmp=run/'normalized-index.tmp';tmp.write_text(json.dumps(idx,indent=2)+'\n');tmp.replace(run/'results-index.json')
 write_json(out/'Source-reuse-check.json',dict(status='PASS',Source_cells=8,origin=str(a),origin_completion_sha256=sha256(a/'completion.json'),rows=inherited,note='Inherited A cells carry their original new/reused flags; explicitly marked reused in phase C. Original driver output preserved.'))

