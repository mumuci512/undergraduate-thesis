% 本地开题报告适配，依据学校提供的 2毕业设计(论文)开题报告.doc。
% Word 原生参数及原生 PDF 的测量依据见 PROPOSAL_WORD.md。
\NeedsTeXFormat{LaTeX2e}[2022-06-01]
\ProvidesClass{tongji-proposal-word}[2026/11/17 Local Word proposal layout]
\LoadClass[12pt,oneside]{article}
\RequirePackage{iftex}
\ifXeTeX\else
  \ClassError{tongji-proposal-word}{Use XeLaTeX}{Select XeLaTeX as the compiler.}
\fi
\RequirePackage{fontspec}
\RequirePackage{xeCJK}
\RequirePackage[paperwidth=595.32bp,paperheight=842.04bp,
  top=65.16bp,bottom=28.35bp,left=89.904bp,right=89.904bp,
  headheight=0bp,headsep=0bp,footskip=0bp]{geometry}
\RequirePackage{graphicx}
\RequirePackage{xcolor}
\RequirePackage{eso-pic}
\RequirePackage{framed}
\RequirePackage{needspace}
\RequirePackage{xparse}
\RequirePackage{etoolbox}
% 禁止静默替代字体；跨系统使用时须自行提供这些有授权的字体。
\IfFontExistsTF{SimSun}{}{\ClassError{tongji-proposal-word}{SimSun is required}{Install the Windows fonts.}}
\IfFontExistsTF{SimHei}{}{\ClassError{tongji-proposal-word}{SimHei is required}{Install the Windows fonts.}}
\IfFontExistsTF{Times New Roman}{}{\ClassError{tongji-proposal-word}{Times New Roman is required}{Install the Windows fonts.}}
\setmainfont{Times New Roman}[Ligatures=NoCommon]
\setCJKmainfont{SimSun}[BoldFont=SimHei,ItalicFont=KaiTi]
\setCJKfamilyfont{tjwordsong}{SimSun}
\setCJKfamilyfont{tjwordhei}{SimHei}
\newfontfamily\TJWordLatinSong{SimSun}
\newfontfamily\TJWordLatinHei{SimHei}
\newcommand{\TJWordSong}{\normalfont\CJKfamily{tjwordsong}\color{black}}
\newcommand{\TJWordHei}{\normalfont\CJKfamily{tjwordhei}\TJWordLatinHei\color{black}}
\newcommand{\TJWordHeiRoman}{\normalfont\CJKfamily{tjwordhei}\color{black}}
\xeCJKsetup{PunctStyle=plain}
\definecolor{tjwordnote}{HTML}{ADADAD}
\pagestyle{empty}
\setlength{\parindent}{24bp}
\setlength{\parskip}{0bp}
\setlength{\topskip}{0bp}
\raggedbottom
\clubpenalty=0\widowpenalty=0\displaywidowpenalty=0
\AtBeginDocument{\TJWordSong\fontsize{12bp}{23.4bp}\selectfont}
\def\tjword@school{}\def\tjword@major{}
\def\tjword@number{}\def\tjword@author{}
\def\tjword@title{}\def\tjword@subtitle{}
\def\tjword@year{}\def\tjword@month{}\def\tjword@day{}
\newcommand{\school}[1]{\def\tjword@school{#1}}
\newcommand{\major}[1]{\def\tjword@major{#1}}
\newcommand{\student}[2]{\def\tjword@number{#1}\def\tjword@author{#2}}
\newcommand{\thesistitle}[2]{\def\tjword@title{#1}\def\tjword@subtitle{#2}}
\newcommand{\proposaldate}[3]{\def\tjword@year{#1}\def\tjword@month{#2}\def\tjword@day{#3}}
% 兼容上游 metadata 中仅供论文正文使用的字段。
\newcommand{\thesistitleeng}[2]{}\newcommand{\thesisadvisor}[1]{}
\newcommand{\thesisdate}[3]{}\newcommand{\taskbookperiod}[6]{}
\newcommand{\infotype}[1]{}\newcommand{\infoabstract}[1]{}
\newcommand{\infodrawings}[1]{}\newcommand{\infowordcount}[1]{}
\newcommand{\infothesiswords}[1]{}\newcommand{\infomaterials}[1]{}
\newcommand{\abstracttitle}[2]{}\newcommand{\abstracttitleeng}[2]{}
\newcommand{\midtermdecision}[1]{}
\providecommand{\TongjiThesis}{TongjiThesis}

% 封面坐标来自 Word 原生输出。长字段按 Word 的最小行高扩展并顺延后续行。
\newdimen\tjword@coveroffset
\newdimen\tjword@coverextra
\newdimen\tjword@covertotal
\newdimen\tjword@coverstudent
\newbox\tjword@covermeasure
\newcommand{\tjword@measurefield}[2]{%
  \setbox\tjword@covermeasure=\vbox{\hsize=#2bp
    \TJWordSong\TJWordLatinSong\fontsize{14.04bp}{18.2bp}\selectfont
    \parindent=0bp\strut #1\strut\par}%
  \tjword@coverextra=\dimexpr\ht\tjword@covermeasure+\dp\tjword@covermeasure-42.4bp\relax
  \ifdim\tjword@coverextra<0bp\tjword@coverextra=0bp\fi
}
\newcommand{\tjword@preparecover}{%
  \tjword@covertotal=0bp
  \tjword@measurefield{\tjword@title}{269.55}\advance\tjword@covertotal\tjword@coverextra
  \edef\tjword@coveroffsetone{\the\tjword@covertotal}%
  \tjword@measurefield{\tjword@subtitle}{269.55}\advance\tjword@covertotal\tjword@coverextra
  \edef\tjword@coveroffsettwo{\the\tjword@covertotal}%
  \tjword@measurefield{\tjword@school}{269.55}\advance\tjword@covertotal\tjword@coverextra
  \edef\tjword@coveroffsetthree{\the\tjword@covertotal}%
  \tjword@measurefield{\tjword@major}{269.55}\advance\tjword@covertotal\tjword@coverextra
  \edef\tjword@coveroffsetfour{\the\tjword@covertotal}%
  \tjword@measurefield{\tjword@author}{71.28}\tjword@coverstudent=\tjword@coverextra
  \tjword@measurefield{\tjword@number}{122.55}%
  \ifdim\tjword@coverextra<\tjword@coverstudent\tjword@coverextra=\tjword@coverstudent\fi
  \advance\tjword@covertotal\tjword@coverextra
  \edef\tjword@coveroffsetfive{\the\tjword@covertotal}%
}
\newcommand{\tjword@at}[3]{%
  \tjword@coveroffset=0bp
  \ifdim#2bp>300bp
    \ifdim#2bp<370bp\tjword@coveroffset=\tjword@coveroffsetone
    \else\ifdim#2bp<410bp\tjword@coveroffset=\tjword@coveroffsettwo
    \else\ifdim#2bp<455bp\tjword@coveroffset=\tjword@coveroffsetthree
    \else\ifdim#2bp<495bp\tjword@coveroffset=\tjword@coveroffsetfour
    \else\tjword@coveroffset=\tjword@coveroffsetfive\fi\fi\fi\fi
  \fi
  \put(#1bp,-\dimexpr#2bp+\tjword@coveroffset\relax){#3}%
}
\newcommand{\tjword@glyph}[6]{%
  \rlap{\hspace{#1bp}\raisebox{#2bp}[0bp][0bp]{%
    \ifstrequal{#3}{hei}{\TJWordHei}{\TJWordSong\ifstrequal{#3}{song}{\TJWordLatinSong}{}}%
    \fontsize{#4bp}{#4bp}\selectfont\color[gray]{#5}#6}}}
\newcommand{\tjword@inlinerule}[4]{%
  \rlap{\hspace{#1bp}\raisebox{#2bp}[0bp][0bp]{\color{black}\rule{#3bp}{#4bp}}}}
% 固定文字不参与 TeX 的二次字距拉伸。
\newcommand{\TJWordStatic}[1]{\csname tjword@static@#1\endcsname}
\input{tongji-proposal-word-text.def}
\newcommand{\tjword@covertext}[3]{%
  \tjword@at{#1}{#2}{{\TJWordSong\fontsize{14.04bp}{18.2bp}\selectfont #3}}}
\newcommand{\tjword@coverfield}[4]{%
  \tjword@at{#1}{#2}{\parbox[b]{#3bp}{\TJWordSong\TJWordLatinSong\fontsize{14.04bp}{18.2bp}\selectfont\parindent=0bp\strut #4\strut\par}}}
\newcommand{\tjword@datefield}[4]{%
  \tjword@at{#1}{#2}{\parbox[b]{#3bp}{\TJWordSong\TJWordLatinSong\fontsize{14.04bp}{18.2bp}\selectfont\centering\strut #4\strut\par}}}
\newcommand{\tjword@coverrule}[3]{\tjword@at{#1}{#2}{\rule{#3bp}{0.48bp}}}
\newcommand{\MakeProposal}{%
  \tjword@preparecover
  \AddToShipoutPictureFG*{\AtPageUpperLeft{%
    \setlength{\unitlength}{1bp}%
    \begin{picture}(0,0)
      \tjword@at{194.85}{176.75}{\includegraphics[width=200bp,height=49.2bp]{figures/tongji-word-logo.png}}
      \tjword@at{101.9}{226.94}{{\TJWordHei\fontsize{36bp}{36bp}\selectfont 毕业设计}}
      \tjword@at{245.93}{226.94}{{\TJWordLatinSong\fontsize{36bp}{36bp}\selectfont (}}
      \tjword@at{263.93}{226.94}{{\TJWordHei\fontsize{36bp}{36bp}\selectfont 论文}}
      \tjword@at{335.95}{226.94}{{\TJWordLatinSong\fontsize{36bp}{36bp}\selectfont )}}
      \tjword@at{353.95}{226.94}{{\TJWordHei\fontsize{36bp}{36bp}\selectfont 开题报告}}
      \tjword@covertext{116.3}{391.73}{\TJWordStatic{cover_subtitle}}
      \tjword@covertext{116.3}{434.71}{\TJWordStatic{cover_school}}
      \tjword@covertext{116.3}{477.55}{\TJWordStatic{cover_major}}
      \tjword@covertext{116.3}{520.51}{\TJWordStatic{cover_student}}
      \tjword@coverrules
      \ifdefempty{\tjword@title}{%
        \tjword@at{116.3}{348.89}{\TJWordStatic{cover_topic}}%
      }{\tjword@covertext{116.3}{348.89}{课题名称}\tjword@coverfield{209.57}{348.89}{269.55}{\tjword@title}}
      \tjword@coverfield{209.57}{391.73}{269.55}{\tjword@subtitle}
      \tjword@coverfield{209.57}{434.71}{269.55}{\tjword@school}
      \tjword@coverfield{209.57}{477.55}{269.55}{\tjword@major}
      \tjword@coverfield{209.57}{520.51}{71.28}{\tjword@author}
      \tjword@coverfield{356.59}{520.51}{122.55}{\tjword@number}
      \tjword@covertext{262.01}{702.94}{\TJWordStatic{cover_date}}
      \tjword@datefield{191.33}{702.94}{56.3}{\tjword@year}
      \tjword@datefield{289.97}{702.94}{36.35}{\tjword@month}
      \tjword@datefield{348.67}{702.94}{31.45}{\tjword@day}
    \end{picture}%
  }}%
  \null\clearpage
}

% Word 的中文 1.5 倍行框为 23.4bp；空西文段落的行框为 20.4bp。
% 字体、字号、行框高、首基线、段前、段后、首行缩进、左缩进、内容。
\newbox\tjword@paragraph
\long\def\tjword@para#1#2#3#4#5#6#7#8#9{%
  \par\vskip#5\relax\nointerlineskip
  \setbox\tjword@paragraph=\vbox{%
    \hsize=\linewidth
    % Word 的字框有小于 0.25bp 的取整越界；字形坐标保持原样。
    \hfuzz=0.25bp\hbadness=10000
    #1\fontsize{#2}{#3}\selectfont
    \baselineskip=#3\relax\lineskiplimit=-1000bp
    \leftskip=#8\relax\rightskip=0bp\parfillskip=0bp plus 1fil
    \parindent=#7\relax\parskip=0bp
    \def\tjword@strut{\vrule width0bp height#4 depth\dimexpr#3-#4\relax}%
    \everypar{\tjword@strut}%
    \indent \TJWordKnown{#9}\tjword@strut\par
  }%
  \unvbox\tjword@paragraph\nointerlineskip\vskip#6\relax
}
\NewDocumentCommand{\TJProposalSection}{O{normal} m}{%
  \ifstrequal{#1}{fixedfirst}{%
    \vspace*{6.04bp}\nointerlineskip
    \tjword@para{\TJWordHei}{14.04bp}{18bp}{14.38bp}{0bp}{6bp}{27.956bp}{0bp}{#2}%
  }{\ifstrequal{#1}{fixedlast}{%
    \tjword@para{\TJWordHei}{14.04bp}{18bp}{14.56bp}{5.82bp}{6bp}{27.956bp}{0bp}{#2}%
  }{\def\tjword@before{6bp}\ifstrequal{#1}{references}{\def\tjword@before{6.06bp}}{}%
    \tjword@para{\TJWordHei}{14.04bp}{27.3bp}{14.17bp}{\tjword@before}{6bp}{27.956bp}{0bp}{#2}}}%
}
\NewDocumentCommand{\TJProposalSubsection}{O{hei} m}{%
  \ifstrequal{#1}{roman}{%
    \tjword@para{\TJWordHeiRoman}{12bp}{23.4bp}{12.1bp}{6bp}{6bp}{23.996bp}{0bp}{#2}%
  }{\ifstrequal{#1}{romansecond}{%
    \tjword@para{\TJWordHeiRoman}{12bp}{23.4bp}{12.1bp}{6.03bp}{5.97bp}{23.996bp}{0bp}{#2}%
  }{\def\tjword@before{6bp}%
    \ifstrequal{#1}{research}{\def\tjword@before{6.26bp}}{}%
    \ifstrequal{#1}{schedule}{\def\tjword@before{6.36bp}}{}%
    \tjword@para{\TJWordHei}{12bp}{23.4bp}{12.19bp}{\tjword@before}{6bp}{23.996bp}{0bp}{#2}}}%
}
\NewDocumentCommand{\TJProposalBody}{O{songblank} +m}{%
  \ifstrempty{#2}{%
    \ifstrequal{#1}{latinblank}{%
      \tjword@para{\TJWordSong}{12bp}{20.4bp}{12.1bp}{0bp}{0bp}{24bp}{0bp}{}%
    }{\tjword@para{\TJWordSong}{12bp}{23.4bp}{12.1bp}{0bp}{0bp}{24bp}{0bp}{}}%
  }{\tjword@para{\TJWordSong}{12bp}{23.4bp}{12.1bp}{0bp}{0bp}{24bp}{0bp}{#2}}%
}
\newcommand{\TJProposalInstructions}{%
  \tjword@para{\TJWordSong\color{tjwordnote}}{12bp}{23.4bp}{12.1bp}{0bp}{0bp}{17.996bp}{0bp}{%
    \TJWordStatic{guide1}\linebreak
    \TJWordStatic{guide2}\linebreak
    \TJWordStatic{guide3}}%
}
\newcommand{\TJProposalNote}[1]{%
  \tjword@para{\TJWordSong\color{tjwordnote}}{12bp}{23.4bp}{12.1bp}{0bp}{0bp}{17.996bp}{0bp}{#1}}
\newenvironment{TJProposalReferences}{}{}
\NewDocumentCommand{\TJProposalReference}{+m}{%
  \tjword@para{\TJWordSong}{12bp}{23.4bp}{12.1bp}{0bp}{0bp}{-21bp}{21bp}{#1}}

% 使用可拆页的文字框；两行在同页时共用中间边线。
\newbox\tjword@opinion
\newdimen\tjword@reviewfill
\newbox\tjword@framebox
\newif\iftjword@joint
\newif\iftjword@lastrow
\newif\iftjword@doublecorners
\newdimen\tjword@borderwidth
\newcommand{\tjword@border}{%
  \hbox{%
    \iftjword@doublecorners\rlap{\rule{0.48bp}{0.48bp}}\fi
    \rule{0.48bp}{0.48bp}\rule{\tjword@borderwidth}{0.48bp}\kern0.006bp
    \iftjword@doublecorners\rlap{\rule{0.48bp}{0.48bp}}\fi
    \rule{0.48bp}{0.48bp}}}
\long\def\tjword@drawframe#1{%
  \setbox\tjword@framebox=\hbox{\hspace{5.16bp}#1\hspace{5.16bp}}%
  \tjword@borderwidth=\dimexpr\wd\tjword@framebox-0.006bp\relax
  \vbox{\offinterlineskip\color{black}%
    \iftjword@joint\vskip0.48bp\else\tjword@doublecornerstrue\tjword@border\fi
    \hbox{\vrule width0.48bp\box\tjword@framebox\vrule width0.48bp}%
    \iftjword@lastrow\tjword@doublecornerstrue\else\tjword@doublecornersfalse\fi
    \tjword@border}%
}
\newcommand{\tjword@reviewframebegin}{%
  \par\nointerlineskip\begingroup\color{black}
  \setlength{\OuterFrameSep}{0bp}\setlength{\FrameSep}{0bp}\setlength{\FrameRule}{0.48bp}%
  \def\FrameHeightAdjust{0bp}%
  \def\FrameCommand##1{\hspace*{-0.24bp}\tjword@drawframe{##1}}%
  \def\MidFrameCommand##1{\begingroup\tjword@jointfalse\FrameCommand{\vbox{\vskip1bp\nointerlineskip ##1}}\endgroup}%
  \let\LastFrameCommand\MidFrameCommand
  \hsize=425.356bp\linewidth=\hsize
  \MakeFramed{\advance\hsize-\width\FrameRestore}%
  \linewidth=\hsize
}
\newcommand{\tjword@reviewframeend}{\endMakeFramed\endgroup}
\long\def\tjword@reviewrow#1#2#3#4#5#6{%
  \vskip#1\relax
  \tjword@para{\TJWordHei}{12bp}{#2}{\ifdim#2=18bp 14.44bp\else12.19bp\fi}{0bp}{0bp}{23.996bp}{0bp}{#4}%
  \tjword@para{\TJWordSong\color{tjwordnote}}{12bp}{\ifdim#2=18bp18bp\else23.4bp\fi}{\ifdim#2=18bp14.44bp\else12.19bp\fi}{0bp}{0bp}{23.996bp}{0bp}{\ifdim#2=18bp\TJWordStatic{teacher_hint1}\linebreak\TJWordStatic{teacher_hint2}\else\TJWordStatic{department_hint}\fi}%
  \setbox\tjword@opinion=\vbox{\linewidth=\hsize\ifstrempty{#6}{}{\TJProposalBody{#6}}}%
  \tjword@reviewfill=\dimexpr#3-#1-#2\relax
  \ifdim#2=18bp\advance\tjword@reviewfill-36bp\else\advance\tjword@reviewfill-23.4bp\fi
  \advance\tjword@reviewfill-\ht\tjword@opinion\advance\tjword@reviewfill-\dp\tjword@opinion
  \unvbox\tjword@opinion\nointerlineskip
  \ifdim\tjword@reviewfill>0bp\vskip\tjword@reviewfill\fi
}
\NewDocumentCommand{\TJProposalReviews}{+m +m}{%
  \par\tjword@jointfalse\tjword@lastrowfalse\Needspace{254.45bp}%
  \tjword@reviewframebegin
  \tjword@reviewrow{5.26bp}{18bp}{204.10bp}{指导教师意见：}{（课题难度是否适中、工作量是否饱满、进度安排是否合理、工作条件是否具备、是否同意开题等）}{#1}%
  \tjword@para{\TJWordHei}{12bp}{15.48bp}{12.19bp}{0bp}{0bp}{276.046bp}{0bp}{\TJWordStatic{teacher_sign}}%
  \tjword@para{\TJWordHei}{12bp}{15.6bp}{12.19bp}{0bp}{0bp}{312.166bp}{0bp}{\TJWordStatic{teacher_date}}%
  \vskip18.31bp
  \tjword@reviewframeend
  \edef\tjword@teacherpage{\the\c@page}%
  \Needspace{199.34bp}%
  \ifnum\c@page=\tjword@teacherpage\relax
    \tjword@jointtrue\vskip-0.48bp
  \else\tjword@jointfalse\fi
  \tjword@lastrowtrue
  \tjword@reviewframebegin
  \tjword@reviewrow{9.05bp}{15.6bp}{151.39bp}{专业审核意见：}{（适当对各项内容给与意见和评价，字数不限。）}{#2}%
  \tjword@para{\TJWordHei}{12bp}{15.6bp}{12.19bp}{0bp}{0bp}{288.046bp}{0bp}{\TJWordStatic{department_sign}}%
  \tjword@para{\TJWordHei}{12bp}{15.6bp}{12.19bp}{0bp}{0bp}{318.166bp}{0bp}{\TJWordStatic{department_date}}%
  \vskip15.79bp
  \tjword@reviewframeend
}
\endinput
