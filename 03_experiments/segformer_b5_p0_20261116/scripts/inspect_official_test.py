from pathlib import Path
import json, subprocess, zipfile
root=Path('/home/ysheng4/research/segformer_b5_p0_20261116')
print('ROOT',root)
print('GPU',subprocess.check_output(['/usr/lib/wsl/lib/nvidia-smi','--query-gpu=name,memory.total,memory.used,utilization.gpu','--format=csv,noheader']).decode())
print('PROCESSES',subprocess.run(['pgrep','-af','python'],capture_output=True,text=True).stdout)
print('DISK',subprocess.check_output(['df','-h',str(root)]).decode())
for p in sorted(root.glob('data/*')):
    print('DATA_LINK',p,p.resolve())
    for q in p.glob('rgb_anon/*/test'):
        print('EXTRACTED_TEST',q,len(list(q.rglob('*_rgb_anon.png'))))
raw=Path('/home/ysheng4/research/GSMF-RS-DIL/data/road_raw')
print('RAW',[(p.name,p.stat().st_size) for p in raw.iterdir()])
for p in raw.rglob('*.zip'):
    if 'rgb' in p.name.lower() or 'acdc' in p.name.lower():
        print('ARCHIVE',p,p.stat().st_size)
        with zipfile.ZipFile(p) as z:
            tests=[x for x in z.infolist() if '/test/' in x.filename and x.filename.endswith('_rgb_anon.png')]
            print('TEST_IMAGES',len(tests),'EXTRACTED_BYTES',sum(x.file_size for x in tests))
            print('EXAMPLES',[x.filename for x in tests[:2]])
