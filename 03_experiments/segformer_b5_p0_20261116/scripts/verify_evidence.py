"""Offline checks of returned P0 receipts, matrices, data and source snapshots."""
import hashlib
import json
import math
from pathlib import Path
import numpy as np

root = Path(__file__).resolve().parents[1]
remote = root/'remote'
checks = []
def check(name, condition):
    assert condition, name
    checks.append(name)
def read(path):
    return json.loads(path.read_text(encoding='utf-8'))
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

manifest = read(remote/'EVIDENCE_MANIFEST.json')
for name, record in manifest.items():
    path = remote/name
    check('bytes:'+name, path.stat().st_size == record['bytes'])
    check('sha256:'+name, sha(path) == record['sha256'])
logged_source_sha = (root/'logs/execution_scale256.txt').read_text(encoding='utf-8').splitlines()[0].split()[0]
check('executed_source_matches_original_run_log',sha(remote/'run_b5_p0.py') == logged_source_sha)
prep = read(remote/'prepare.json')
check('source_strict_load',prep['strict_load'] is True)
check('source_published_hash_prefix',prep['checkpoint_sha256'].startswith('87a052ec'))
check('expected_model_parameters',prep['parameters'] == 81974739)
train = read(remote/'train_amp_scale256/result.json')
steps = [json.loads(x) for x in (remote/'train_amp_scale256/steps.jsonl').read_text().splitlines()]
check('200_actual_updates',len(steps)==train['optimizer_steps']==200 and
      [x['step'] for x in steps] == list(range(1,201)))
check('finite_training',all(math.isfinite(x['loss']) and math.isfinite(x['grad_norm']) for x in steps))
check('no_AMP_skips',train['all_optimizer_steps_applied'] and all(x['scale']==256 for x in steps))
check('training_modified_model',train['fingerprint_after'] != train['fingerprint_before'])
check('save_reload_exact',train['reload_strict_equal'])
check('source_same_as_training_initial',read(remote/'source_state_check.json')['before']==train['fingerprint_before'])
check('source_state_fixed',read(remote/'source_state_check.json')['unchanged'])
check('training_mean_seconds',abs(np.mean([x['seconds'] for x in steps[20:]])-train['mean_step_seconds'])<1e-10)
check('training_throughput',abs(180/sum(x['seconds'] for x in steps[20:])-train['images_per_second'])<1e-10)
check('under_20GiB',train['peak_reserved_MiB']<20480)
data = read(remote/'data_audit.json')
summary = read(remote/'source_results.json')
rows = []
for d, count in zip('ABCDE',[500,100,100,100,106]):
    check('val_count_'+d,data[d+'_val.jsonl']['count']==summary[d]['count']==count)
    check('trainval_same_image_disjoint_'+d,data[d+'_isolation']['exact_image_overlap']==0)
    cm = np.loadtxt(remote/('source_'+d+'_confusion.csv'),delimiter=',',dtype=np.int64)
    check('cm_shape_'+d,cm.shape==(19,19) and (cm>=0).all())
    check('cm_binary_csv_'+d,np.array_equal(cm,np.load(remote/('source_'+d+'_confusion.npy'))))
    valid_hist = np.zeros(19,dtype=np.int64)
    for line in (remote/'manifests'/(d+'_val.jsonl')).read_text().splitlines():
        rec = json.loads(line)
        # These historical manifest histograms are already trainIds, including CS.
        for k,v in rec['label_histogram'].items():
            if k!='255': valid_hist[int(k)]+=v
    check('GT_marginal_independent_'+d,np.array_equal(cm.sum(1),valid_hist))
    ious = []
    for cls in range(19):
        tp = int(cm[cls,cls]); denom = int(cm[cls,:].sum()+cm[:,cls].sum()-tp)
        check('class_union_'+d+str(cls),denom>0)
        ious.append(100*tp/denom)
    check('mIoU_recomputed_'+d,abs(sum(ious)/19-summary[d]['mIoU_percent'])<1e-10)
    check('classIoU_recomputed_'+d,np.allclose(ious,summary[d]['per_class_IoU_percent'],atol=1e-10,rtol=0))
    rows.append(dict(domain=d,count=count,mIoU_percent=sum(ious)/19))
# Record the discrepancy; the source recipe did not prescribe a numeric tolerance.
# A nonzero difference must not be silently rounded into an exact reproduction.
for entry in read(root/'recipe/SOURCE_MANIFEST.json')['sources']:
    path = root/'recipe'/entry['file']
    check('recipe_sha:'+entry['file'],sha(path)==entry['sha256'])
if (root/'MIGRATION_VERIFICATION.json').is_file():
    migration = read(root/'MIGRATION_VERIFICATION.json')
    current = read(root/'CURRENT_MANIFEST.json')
    check('independent_project_root',migration['current_project_root']=='/home/ysheng4/research/segformer_b5_p0_20261116')
    check('migration_verified',migration['passed'] and migration['old_experiment_path_absent'])
    check('migrated_source_unchanged',migration['source_weight_sha256']==prep['checkpoint_sha256'])
    check('migrated_smoke_unchanged',migration['smoke_weight_sha256']==train['checkpoint_sha256'])
    check('current_remote_entry_matches_local',current['run_b5_p0.py']['sha256']==sha(root/'scripts/run_b5_p0.py'))
result = dict(passed=True,checks=len(checks),source=rows,
    source_equal_domain_mean=sum(x['mIoU_percent'] for x in rows)/5,
    source_worst_domain=min(x['mIoU_percent'] for x in rows),
    source_CS_delta_to_published_pp=rows[0]['mIoU_percent']-82.25,
    train_peak_allocated_GiB=train['peak_allocated_MiB']/1024,
    train_peak_reserved_GiB=train['peak_reserved_MiB']/1024,
    checked_items=checks)
(root/'VERIFICATION.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='checked_items'},indent=2))
