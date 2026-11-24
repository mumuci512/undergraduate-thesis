# 开题报告工作副本

课题：视觉条件变化下道路场景语义分割的持续学习方法研究。

本目录保存已填写的开题报告工程。后续正文、封面及排版修改均在本目录进行；`../TongjiThesis/` 保留为空白模板。

- 编译入口：[proposal.tex](proposal.tex)。
- 当前成稿：[proposal_格式修订.pdf](proposal_格式修订.pdf)，21页。
- 封面信息：[chapters/proposal_metadata.tex](chapters/proposal_metadata.tex)。
- 正文：[chapters/proposal_body.tex](chapters/proposal_body.tex)。
- 样式与图片位于本目录的 `style/`、`figures/`，编译不读取原模板目录。

在项目根目录 `C:\undergraduate_thesis` 的 PowerShell 中复用已保留的编译环境：

```powershell
wsl -e bash /mnt/c/undergraduate_thesis/05_writing/开题报告_LaTeX/scripts/build-proposal-wsl.sh
```

脚本不联网下载，输出保存在本目录。也可在本目录使用已安装的 XeLaTeX，运行 `scripts/build-proposal.ps1`，或使用 `latexmk -xelatex proposal.tex`。

正文沿用原 Markdown 的文字、数字、公式、表格及40篇参考文献；项目内超链接已转为普通文字，参考文献外部链接保留。原 Markdown 文件未修改。

正文引文使用右上角角标，取消正文显式加粗；表格连同上方的表题整体分页。图表与公式沿用 TongjiThesis 的按章编号形式，如“表 2.1”和“(2.1)”；表题使用五号宋体，正文中的表号通过交叉引用与实际表格保持一致。

本次修订时原 `proposal.pdf` 被其他程序占用，成稿另存为上述文件。关闭原 PDF 后，正常编译仍会更新 `proposal.pdf`。
