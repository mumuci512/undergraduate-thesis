"""Wait for the training lock, collect evidence and finish local verification."""
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
REMOTE = '/home/ysheng4/research/segformer_b5_p1_20261117'
SSH = ['ssh', '-F', 'C:/Users/sissi/.ssh/config', '-o', 'BatchMode=yes',
       '-o', 'ConnectTimeout=15', '-o', 'ServerAliveInterval=30',
       '-o', 'ServerAliveCountMax=3', 'home-wsl']


def save_status(status, **details):
    value = dict(status=status, updated_unix=time.time(), **details)
    temporary = ROOT / 'AUTO_FINISH.tmp'
    temporary.write_text(json.dumps(value, indent=2), encoding='utf-8')
    temporary.replace(ROOT / 'AUTO_FINISH.json')


def complete_report():
    evidence = ROOT / 'evidence'
    summary = json.loads((evidence / 'summary.json').read_text())
    verified = json.loads((ROOT / 'VERIFICATION.json').read_text())
    assert verified['failed'] == 0
    rows = []
    for method in ('ft', 'er'):
        result = summary[method]
        choice = json.loads((evidence / (method + '_selection.json')).read_text())['selected']
        values = [method.upper(), format(choice['lr'], '.2g'), str(choice['steps'])]
        values.extend(format(result['final_by_domain'][d], '.4f') for d in 'ABCDE')
        values.extend(format(result[key], '.4f') for key in ('final_mean_percent',
            'worst_domain_percent', 'mean_old_domain_forgetting_pp'))
        rows.append('| ' + ' | '.join(values) + ' |')
    joint = summary['joint']
    values = ['Joint', format(joint['lr'], '.2g'), str(joint['steps'])]
    values.extend(format(joint['metrics'][d]['mIoU_percent'], '.4f') for d in 'ABCDE')
    values.extend([format(joint['score'], '.4f'),
        format(min(joint['metrics'][d]['mIoU_percent'] for d in 'ABCDE'), '.4f'), '—'])
    rows.append('| ' + ' | '.join(values) + ' |')
    report = (
        '# P1 执行结果\n\n'
        'FT／真实 ER／Joint 的有限搜索和训练已完成，轻量证据已接收并通过独立核算。'
        '以下均为官方 val 开发结果。官方 test 待账号审核后提交官网评测。\n\n'
        '| 方法 | 学习率 | 步数／阶段 | CS | Fog | Rain | Snow | Night | 五域均值 | 最差域 | 旧域平均遗忘 pp |\n'
        '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|\n'
        + '\n'.join(rows) + '\n\n'
        '全部官方 train 参与对应训练池，官方 val 用于配置选择。'
        'FT／ER 的学习率与预算分别由首个增量阶段 CS＋Fog 的 val 均值选择，随后锁定到 Rain／Snow／Night。'
        'Joint 使用全部五域 train 并按五域 val 均值选配置。\n\n'
        '具体学习率范围、候选检查点、200 张 ER 缓存和每四次更新一次历史回放由 Agent 为本轮执行确定。'
        '这些值、单 seed、微批 BN、首阶段调参的覆盖范围及 P0 的 CS 发布值 −0.1658pp 差异须纳入结论边界。'
        'MILE 配方仍有缺项，工程路线核查见 [MILE 审计](MILE_AUDIT.md)。\n\n'
        '配置与历史权限见 [执行协议](PROTOCOL.md)，逐作业训练／评价成本见 [成本回执](evidence/costs.json)，'
        'ER 文件字节预算见 [缓存成本](evidence/replay_cost.json)。'
        '模型路径和 SHA 见 [最终权重记录](evidence/final_models.json)。\n\n'
        '独立核验共通过 ' + str(verified['passed']) + ' 项，失败 0 项，详见 [核验回执](VERIFICATION.json)。'
        '阶段矩阵见 [FT](evidence/ft_matrix.json) 与 [ER](evidence/er_matrix.json)，'
        '候选分数见 [FT 选择](evidence/ft_selection.json)、[ER 选择](evidence/er_selection.json) 与 '
        '[Joint 选择](evidence/joint_selection.json)。\n\n'
        '远程目录为 `/home/ysheng4/research/segformer_b5_p1_20261117/`，'
        '训练权重保存在家中 GPU，轻量证据保存在本目录。\n')
    (ROOT / 'README.md').write_text(report, encoding='utf-8')
    state = ROOT.parents[1] / '00_management' / 'PROJECT_STATE.md'
    text = state.read_text(encoding='utf-8')
    text = text.replace('完整结果待核验。', 'P1训练与本地核验已完成，结果见其执行报告，官网test待评测。')
    text = text.replace('P1搜索预算及ER容量已锁定，已启动训练队列，',
        'P1有限搜索、FT／ER主序及Joint训练与本地核验已完成，')
    state.write_text(text, encoding='utf-8')


def main():
    # The independent remote finalizer holds this lock until its work ends.
    command = 'cd ' + REMOTE + ' && flock -x finish.lock test -f finalized.json'
    save_status('waiting_for_remote_finalizer')
    while True:
        result = subprocess.run(SSH + [command], capture_output=True)
        if result.returncode == 255:
            save_status('connection_retry', error=result.stderr.decode(errors='replace'))
            time.sleep(60)
            continue
        if result.returncode:
            save_status('requires_diagnosis', exit_code=result.returncode,
                error=result.stderr.decode(errors='replace'))
            raise SystemExit(result.returncode)
        break
    save_status('receiving_evidence')
    while True:
        result = subprocess.run([sys.executable, str(ROOT / 'scripts/remote.py'), 'collect'])
        if result.returncode == 0:
            break
        save_status('receive_retry', exit_code=result.returncode)
        time.sleep(60)
    save_status('verifying')
    result = subprocess.run([sys.executable, str(ROOT / 'scripts/verify_results.py'), '--extract'])
    if result.returncode:
        save_status('verification_failed', exit_code=result.returncode)
        raise SystemExit(result.returncode)
    complete_report()
    save_status('completed_train_val_official_test_pending')


if __name__ == '__main__':
    main()
