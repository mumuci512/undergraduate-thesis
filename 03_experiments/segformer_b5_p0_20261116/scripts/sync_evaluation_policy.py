"""Persist the user's evaluation rule in the independent remote project only."""
from pathlib import Path
import hashlib
import json

root=Path('/home/ysheng4/research/segformer_b5_p0_20261116').resolve(strict=True)
assert root == Path('/home/ysheng4/research/segformer_b5_p0_20261116')
path=root/'AGENTS.md'
begin='<!-- undergraduate-thesis-official-evaluation-policy:begin -->'
end='<!-- undergraduate-thesis-official-evaluation-policy:end -->'
policy='''## 数据划分与正式评测（2026-11-17，用户长期要求）

本规则跨会话持续生效。来源为本论文项目C:/undergraduate_thesis/AGENTS.md及00_management/DECISIONS.md的D-012。

1. 训练用官方train，调参／早停／模型选择用官方val，正式最终测试用官方test。已有官方val/test时，保留完整train，不从train另扣一份验证集或自建测试集替代官方划分；不将val/test样本混入训练。官方缺少相应划分时，另行设计并明确记录依据。
2. 官方test标签隐藏、需要服务器评测时，必须按官方协议提交预测，以官网回执作为正式测试成绩。val本地成绩单列，不冒充或替代test，不与官方test混为同表可比结果；不得根据test／排行榜反馈反复调参。
3. 保存模型及提交包SHA、测试划分、推理配置、官方提交ID、时间及结果回执。
4. 账号待审核／无法登录／服务不可用时登记“待官方评测”；允许继续训练／验证，但不能宣称已取得官方test分数。
5. 历史Source五域62.7820%来自CS500＋ACDC406的val，不改写为官方test成绩；后续正式测试须补官网结果。具体任务状态由对应实验文档记录。
'''
block=begin+'\n'+policy+'\n'+end
old=path.read_text(encoding='utf-8') if path.exists() else '# B5独立实验工作规范\n'
if begin in old:
    assert end in old
    updated=old[:old.index(begin)]+block+old[old.index(end)+len(end):]
else:
    updated=old.rstrip()+'\n\n'+block+'\n'
path.write_text(updated,encoding='utf-8')
actual=path.read_text(encoding='utf-8')
assert block in actual
print(json.dumps(dict(path=str(path),bytes=path.stat().st_size,
    sha256=hashlib.sha256(path.read_bytes()).hexdigest(),policy_present=True,
    p1_executed=False),ensure_ascii=False))
