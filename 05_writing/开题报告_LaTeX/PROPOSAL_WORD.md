# 开题报告 Word 对齐版

此本地副本基于 TJ-CSCCG/TongjiThesis v1.5.1，提交 `96185a724e8719a7cc506bf321c8060b188d8bca`。2026-11-17 已成功从 GitHub fetch 核验。修改目标是学校提供的 `../Templates/2毕业设计(论文)开题报告.doc` 的实际印刷版式。它是本地适配，未提交或推送到上游。

## 填写和编译

1. 编辑 `chapters/proposal_metadata.tex` 填写封面。课题留空时显示原 Word 的字号字体提示；填写后提示自动消失。学生姓名与学号共用一行。可选填表日期命令为 `\proposaldate{年}{月}{日}`。
2. 编辑 `chapters/proposal_body.tex`，将 `\TJProposalBody{}` 中填入正文。宏参数支持多个段落，正文可以自动跨页。参考文献使用 `\TJProposalReference{[1] ...}`，第二行实际悬挂 21bp（约 0.74cm）。审核意见由 `\TJProposalReviews{指导教师意见}{专业审核意见}` 填写，签名处保留手写空白。
3. 使用 **XeLaTeX** 和本机宋体 SimSun、黑体 SimHei、Times New Roman。字体不满足时直接报错，避免静默切换成 Fandol。字体文件未随源码分发。
4. 在仓库目录运行 `powershell -ExecutionPolicy Bypass -File scripts/build-proposal.ps1`，或使用上游原有的 `make proposal` / `.\make.bat proposal`。生成 `proposal.pdf`。前者只要求 XeLaTeX 在 PATH 中，后两者要求 latexmk。

开题报告使用 `style/tongji-proposal-word.cls`，封面默认信息独立于论文示例信息。若要共用论文元数据，将开题报告的 metadata 输入改为 `chapters/metadata` 即可。论文正文、任务书、中期报告的类文件与入口未修改。

### 本机可复用的 WSL 编译环境（2026-11-19）

TinyTeX 工具包及补充包保存在项目内 `../../.codex-tmp/proposal_latex_20261119/`。编译脚本将运行环境保存在 WSL 用户目录 `~/.local/share/tongji-proposal-20261119/`（设置 `XDG_DATA_HOME` 时使用该目录），避免跨 Windows 磁盘读取工具文件导致编译缓慢。两处均不依赖系统 `/tmp`，不会随会话结束自动清除，可跨会话反复使用。

在项目根目录 `C:\undergraduate_thesis` 的 PowerShell 中运行：

```powershell
wsl -e bash /mnt/c/undergraduate_thesis/05_writing/开题报告_LaTeX/scripts/build-proposal-wsl.sh
```

该脚本连续编译两遍并更新 `proposal.pdf`，不联网下载。仅在运行环境缺失时，从项目内工具包离线解包；已存在时直接复用。请保留项目内 `tools/TinyTeX-1-complete.tar.xz`、`extra_packages/`、WSL 运行环境及本机 Windows 字体。迁移项目时一并保留上述工具包即可离线恢复环境，并按新位置调整调用路径。

## 对齐方式

- 使用原 Word 内嵌的同济大学位图字标，保留纸张、无页眉页脚页码、封面字段、日期、线宽和位置。
- 按原件实际设置处理字体、字距、灰度、字号、首行缩进、局部行距和空段落；原件说明文字与实际样式有矛盾时保留实际样式。
- 固定栏名、提示和标题是 **可选择的 LaTeX 文字**，由 `tongji-proposal-word-text.def` 保存原件字形位置。没有将 Word 页面或截图嵌入为 PDF 背景。填写内容由正常 LaTeX 文字排版；审核区支持跨页。
- 封面的默认英文字体按各字段的原始直接格式处理，不能只根据提示中出现“Times New Roman”就认定该提示本身也用了该字体。
- Word 的编辑权限范围边界属于屏幕辅助标记，验证参考副本只移除这些标记，原始 DOC 未修改。其余文字、样式和页面坐标均保留。

## 验证记录

默认空白模板的三页均已渲染并逐页检查。文字、字体、字号、颜色、页面尺寸、每个可见字形的位置均与 Word 原生输出比较；机器记录保存在 `validation/proposal_word/checks.json`。图像比较与几何检查另见该目录的记录。

最终 22 项自动核验全部通过；最大字形横坐标误差为 0.00044bp。以 1500px 页高比较，三页不同像素数分别为 7、0、5。长正文和长审核意见测试生成 8 页，三行封面课题测试生成 2 页，均无 Overfull 警告。完整结果见[验证报告](validation/proposal_word/RESULTS.md)。这些实测结果不应扩展为所有未来填写内容的逐像素一致保证。

`validation/proposal_word/flow_test.tex` 是独立的压力测试，含实际封面填写、两行课题、长正文、多行参考文献及长审核意见，不含实际研究结论。

验证的范围是所给空白 Word 模板及测试填写场景。任意正文在 Word 和 XeLaTeX 中的自动断行、字距压缩和分页算法仍可能不同；本地对齐不构成对所有未来填写内容逐像素相等的保证。封面长字段按 42.4bp 最小行高扩展，后续行及日期随之顺延；大幅增加内容后仍需检查最终输出。

原件 SHA-256：`c56bf4e1f866d66bf7de8383d1fc68306f5069c1ca154bacdecb214135afd0d0`。

固定文字可从 Word 原生 PDF 重新导入：`python scripts/import_proposal_word_layout.py reference.pdf`。核对命令为 `python scripts/validate_proposal_word.py reference.pdf proposal.pdf --out validation/proposal_word/checks.json`，需安装 pdfplumber。重新导入前须保持与原模板相同的三页内容结构。
