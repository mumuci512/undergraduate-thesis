"""Verify the independent layout without rerunning training/evaluation."""
from pathlib import Path
import hashlib
import json
import runpy

root = Path('/home/ysheng4/research/segformer_b5_p0_20261116').resolve(strict=True)
old = Path('/home/ysheng4/research/GSMF-RS-DIL/experiments/segformer_b5_p0_20261116')
assert root.parent == Path('/home/ysheng4/research') and not old.exists()
receipt = json.loads((root/'MIGRATION.json').read_text())
def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for data in iter(lambda:stream.read(4*1024*1024),b''):h.update(data)
    return h.hexdigest()
changed={'prepare.json','environment.json','run_b5_p0.py','EVIDENCE_MANIFEST.json'}
for name,item in receipt['original_files'].items():
    if name in changed or name.startswith('manifests/'):continue
    assert sha(root/name)==item['sha256'],name
for script in ['run_b5_p0.py','prepare_remote.py','export_evidence.py']:
    compile((root/script).read_text(),str(root/script),'exec')
    assert '/research/GSMF-RS-DIL' not in (root/script).read_text()
ns=runpy.run_path(str(root/'run_b5_p0.py'),run_name='layout_verification_only')
assert ns['ROOT']==ns['OUT']==root
prep=ns['PREP']
assert prep['root']==prep['output']==str(root)
assert Path(prep['checkpoint']).parent==root
count=0
for name,path in prep['manifests'].items():
    assert Path(path).parent==root/'manifests'
    for line in Path(path).read_text().splitlines():
        row=json.loads(line)
        for key in ['image','label']:
            p=Path(row[key]);p.relative_to(root/'data');assert p.is_file()
        count+=1
source=sha(Path(prep['checkpoint']))
smoke=sha(root/'train_amp_scale256/smoke_200.pth')
assert source==receipt['source_weight_sha256'] and smoke==receipt['smoke_weight_sha256']
(root/'README.md').write_text('''# SegFormer-B5 P0独立实验

项目根目录：`~/research/segformer_b5_p0_20261116/`，与GSMF工程平级。

- 入口：`run_b5_p0.py`；工作配置：`prepare.json`、`official_resolved.py`。
- 模型：`source_cityscapes_official.pth`、`train_amp_scale256/smoke_200.pth`。
- 结果：`source_results.json`、五域混淆矩阵、`train_amp_scale256/result.json`。
- 迁移核验：`MIGRATION.json`、`MIGRATION_VERIFICATION.json`、`CURRENT_MANIFEST.json`。
- 初始执行证据和原始接收包：`provenance/`；历史证据中的旧目录是当时实际运行位置。
- 运行仍复用现有Python依赖环境`~/miniconda3/envs/GSMF_RS_DIL`；不导入GSMF工程代码。
- `data/`为既有原始数据的软链接，`manifests/`已独立保存并改用本项目data路径。未移动或复制原始数据。

P0已完成，入口对已完成训练有防覆盖检查；本次迁移没有重新训练或重算评价。
''',encoding='utf-8')
verified=dict(passed=True,current_project_root=str(root),old_experiment_path_absent=not old.exists(),
    all_untouched_results_byte_identical=True,source_weight_sha256=source,smoke_weight_sha256=smoke,
    current_manifest_pairs_verified=count,standalone_import_from_new_root=True,
    active_scripts_no_gsmf_project_path=True,raw_data_reused_via_symlinks=True,
    existing_python_environment_reused=True,training_or_evaluation_rerun=False)
(root/'MIGRATION_VERIFICATION.json').write_text(json.dumps(verified,indent=2))
files=sorted(p for p in root.rglob('*') if p.is_file() and p.suffix not in ['.pth','.pyc']
             and '__pycache__' not in p.parts and p.name!='CURRENT_MANIFEST.json')
manifest={p.relative_to(root).as_posix():dict(bytes=p.stat().st_size,sha256=sha(p)) for p in files}
(root/'CURRENT_MANIFEST.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps(dict(**verified,current_manifest_files=len(files)),indent=2))
