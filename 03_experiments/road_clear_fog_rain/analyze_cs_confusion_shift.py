"""Cityscapes晴天遗忘的混淆去向分解（第3项seed0矩阵，零训练、只读）。

用法：python -I analyze_cs_confusion_shift.py
输入：本目录下第3项正式结果包的42份19×19混淆矩阵（GT行／预测列，ignore255已排除）。
输出：同目录 CS_CONFUSION_SHIFT_2026-11-11.json。
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
MAT = HERE / 'formal-seed0-plan-20261110-180543' / 'formal-seed0-plan-20261110-180543' / 'results' / 'matrices'
OUT = HERE / 'CS_CONFUSION_SHIFT_2026-11-11.json'
MODELS = ['source', 'ft_fog', 'gsmf_fog', 'lwf_fog', 'ft_rain', 'gsmf_rain', 'lwf_rain']
TRACKED = ['terrain', 'truck', 'train', 'sky', 'building', 'fence', 'bicycle']


def load(name):
    return json.loads((MAT / f'{name}.json').read_text(encoding='utf8'))


def main():
    src = load('source-clear')
    classes = src['classes']
    n = len(classes)
    result = dict(scope='Cityscapes val500晴天；seed0；仅描述，不作显著性检验',
                  matrices=str(MAT.relative_to(HERE)), gt_share_percent={}, clear={})
    for cond in ['clear', 'fog', 'rain']:
        h = load(f'source-{cond}')['GT_histogram']
        h = h if isinstance(h, dict) else dict(zip(classes, h))
        tot = sum(h.values())
        result['gt_share_percent'][cond] = {c: 100 * h[c] / tot for c in classes}
    src_iou = src['IoU']
    for m in MODELS:
        d = load(f'{m}-clear')
        M = d['confusion_matrix']
        road = classes.index('road')
        road_row = M[road]
        road_tot = sum(road_row)
        tracked = {}
        for c in TRACKED:
            j = classes.index(c)
            col = [M[i][j] for i in range(n)]
            pred, gt = sum(col), sum(M[j])
            tracked[c] = dict(
                IoU=d['IoU'][c],
                pred_over_gt_area=pred / gt,
                recall_percent=100 * M[j][j] / gt,
                false_positive_sources_percent={classes[i]: 100 * col[i] / pred
                                                for i in sorted(range(n), key=lambda i: -col[i])[:3]})
        drop = {c: (src_iou[c] - d['IoU'][c]) / n for c in classes}
        result['clear'][m] = dict(
            mIoU=d['mIoU'],
            road_gt_predicted_as_percent={classes[j]: 100 * road_row[j] / road_tot
                                          for j in sorted(range(n), key=lambda j: -road_row[j])[:5]},
            tracked=tracked,
            miou_drop_vs_source_pp=sum(drop.values()),
            per_class_drop_contribution_pp=dict(sorted(drop.items(), key=lambda kv: -kv[1])))
    for stage in ['fog', 'rain']:
        g, f = load(f'gsmf_{stage}-clear')['IoU'], load(f'ft_{stage}-clear')['IoU']
        contrib = {c: (g[c] - f[c]) / n for c in classes}
        result[f'gsmf_minus_ft_{stage}_contribution_pp'] = dict(
            total=sum(contrib.values()), per_class=dict(sorted(contrib.items(), key=lambda kv: kv[1])))
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding='utf8')
    c = result['clear']
    print('road->terrain %:', {m: round(c[m]['road_gt_predicted_as_percent'].get('terrain', 0), 2) for m in MODELS})
    print('terrain pred/GT:', {m: round(c[m]['tracked']['terrain']['pred_over_gt_area'], 2) for m in MODELS})
    fog = result['gsmf_minus_ft_fog_contribution_pp']
    print('GSMF-FT fog total %.4f, train %.4f' % (fog['total'], fog['per_class']['train']))
    print('written', OUT.name)


if __name__ == '__main__':
    main()
