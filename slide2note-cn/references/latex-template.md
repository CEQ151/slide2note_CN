# LaTeX 讲义模板（复制后填充）

导言区取自实际交付中迭代出的"完全体"版本。标记【电路课件】的块只有画门级电路/数据通路时才需要，纯文字/代数类讲义可整块删去。

## 完整导言区

```latex
\documentclass[11pt,a4paper,fontset=mac]{ctexart}   % 非 macOS 去掉 fontset=mac

% ============================================================
%  第N讲 标题 课堂讲义
%  课程名 2026-2027 Fall
% ============================================================
\usepackage[margin=2.1cm,top=2.2cm,bottom=2.4cm,headheight=13.5pt]{geometry}
\usepackage{amsmath,amssymb}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{tabularx}   % 内容地图等通栏表格用 X 列
\usepackage{longtable}  % 名词对照等跨页长表
\usepackage{float}      % [H] 严格定位
\usepackage{array}
\usepackage{xcolor}
\usepackage{colortbl}
% 【电路课件】TikZ / CircuiTikZ（画门级电路、数据通路、知识地图）
\usepackage{tikz}
\usetikzlibrary{arrows.meta,calc,positioning,decorations.pathreplacing}
\usepackage[american]{circuitikz}
\usepackage[most]{tcolorbox}
\usepackage{titlesec}
\usepackage{enumitem}
\usepackage{caption}
\usepackage{fancyhdr}
\usepackage{hyperref}   % 永远最后加载

\hypersetup{colorlinks=true,linkcolor=zhulv,urlcolor=zhulv,unicode=true,
  bookmarks=true,bookmarksnumbered=true}
\captionsetup{font=small,labelfont={bf,color=zhuse}}
\captionsetup[figure]{name=图}

% ---------- 图像搜索路径（插图在 AI Notes/images/） ----------
\graphicspath{{../images/}}

% ---------- 配色（语义固定，勿混用） ----------
\definecolor{zhuse}{HTML}{2B3A8F}   % 主深蓝：标题、表头文字
\definecolor{zhulv}{HTML}{3E63DD}   % 亮蓝：链接、装饰线
\definecolor{luv}{HTML}{EEF1FC}     % 更浅蓝：盒底色
\definecolor{hui}{HTML}{5A6472}     % 灰：辅助文字、原图框
\definecolor{dingyi}{HTML}{2B5FA3}  % 定义框
\definecolor{yaodian}{HTML}{0E7C66} % 要点绿
\definecolor{liti}{HTML}{217A3C}    % 例题绿
\definecolor{sikao}{HTML}{B4530A}   % 思考橙
\definecolor{jinggao}{HTML}{B02418} % 警示红
\definecolor{xianlu}{HTML}{1F2937}  % 【电路课件】电路线条色

% ---------- 节标题样式 ----------
\titleformat{\section}[block]
  {\color{white}\Large\bfseries}{}{0pt}{\SectionBox}
\titleformat{\subsection}
  {\large\bfseries\color{zhuse}}{\thesubsection}{0.6em}{}
  [\vspace{0.35em}\noindent{\color{zhulv!30}\rule{\linewidth}{0.7pt}}\kern-\linewidth{\color{zhuse}\rule{2.6em}{2.2pt}}]
\titleformat{\subsubsection}
  {\normalsize\bfseries\color{zhulv!80!black}}{\thesubsubsection}{0.6em}{}
\newcommand{\SectionBox}[1]{%
  \colorbox{zhuse}{\parbox{\dimexpr\textwidth-2\fboxsep\relax}{\vspace{3pt}\hspace{0.6em}#1\vspace{3pt}}}}
\newcommand{\secnote}[1]{\noindent{\small\color{hui}\kaishu #1}\par\vspace{2pt}}

% ---------- 语义彩盒 ----------
\newtcolorbox{dinglibox}[1][定义]{enhanced,before skip=8pt,after skip=8pt,
  colback=luv,colframe=dingyi,boxrule=0.9pt,arc=2.5pt,
  fonttitle=\bfseries\small,coltitle=white,colbacktitle=dingyi,
  title={#1},left=7pt,right=7pt,top=5pt,bottom=5pt}
\newtcolorbox{yaodbox}[1][核心要点]{enhanced,breakable,before skip=8pt,after skip=8pt,
  colback=yaodian!6!white,colframe=yaodian,boxrule=0.9pt,arc=2.5pt,
  fonttitle=\bfseries\small,coltitle=white,colbacktitle=yaodian,
  title={#1},left=7pt,right=7pt,top=5pt,bottom=5pt}
\newtcolorbox{litibox}[1][例题]{enhanced,breakable,before skip=8pt,after skip=8pt,
  colback=liti!5!white,colframe=liti!80!black,boxrule=0.9pt,arc=2.5pt,
  fonttitle=\bfseries\small,coltitle=white,colbacktitle=liti!80!black,
  title={#1},left=7pt,right=7pt,top=5pt,bottom=5pt}
\newtcolorbox{sikaobox}[1][思考与讨论]{enhanced,breakable,before skip=8pt,after skip=8pt,
  colback=sikao!6!white,colframe=sikao,boxrule=0.9pt,arc=2.5pt,
  fonttitle=\bfseries\small,coltitle=white,colbacktitle=sikao,
  title={#1},left=7pt,right=7pt,top=5pt,bottom=5pt}
% 课件原图专用：白底灰框，与重绘图/正文区分
\newtcolorbox{yuanbox}[1][课件原图]{enhanced,before skip=8pt,after skip=8pt,
  colback=white,colframe=hui!60,boxrule=0.8pt,arc=2.5pt,
  fonttitle=\bfseries\small,coltitle=white,colbacktitle=hui,
  title={#1},left=5pt,right=5pt,top=4pt,bottom=4pt}

% ---------- 页眉页脚 ----------
\pagestyle{fancy}
\fancyhf{}
\fancyhead[L]{\small\color{hui}\kaishu 第N讲 标题 · 课堂讲义}
\fancyhead[R]{\small\color{hui}\kaishu 课程名}
\fancyfoot[C]{\small\color{hui}\thepage}
\renewcommand{\headrulewidth}{0.5pt}
\renewcommand{\headrule}{\color{zhulv!50}\hrule width\headwidth height\headrulewidth}

% ---------- 【电路课件】通用设置与常用宏 ----------
\ctikzset{logic ports/scale=0.72}
\ctikzset{logic ports=ieee}
\tikzset{
  wire/.style={line width=0.75pt,xianlu},
  busw/.style={line width=1.5pt,xianlu},
  hl/.style={line width=1.6pt,zhulv},          % 高亮当前路径
  hlr/.style={line width=1.6pt,jinggao!85},    % 红色高亮
  blk/.style={draw=xianlu,line width=0.9pt,fill=white,minimum height=9mm},
  blkf/.style={draw=zhuse,line width=1.0pt,fill=luv,minimum height=9mm},
  lab/.style={font=\small},
  slab/.style={font=\footnotesize\color{hui}},
}
% 总线斜杠标记：\slashn[偏移]{坐标}{位宽标注}
\newcommand{\slashn}[3][0]{%
  \draw[wire] ($(#2)!0.5!($(#2)+(0.13,0.13)$)+(#1,0)$) -- ++(-0.26,0.26);
  \node[font=\scriptsize,above right,inner sep=1pt] at ($(#2)+(0.05,0.10)+(#1,0)$) {#3};}

% ---------- 排版微调 ----------
\setlist{itemsep=1.5pt,topsep=3pt,parsep=0pt}
\linespread{1.16}\selectfont
\widowpenalty=10000
\clubpenalty=10000
\newcommand{\inv}[1]{#1'}   % 取反记号，按课程习惯可改 \overline{#1}
```

## 文档骨架

```latex
\begin{document}

% ======================= 封面 =======================
\begin{titlepage}
\centering
\vspace*{2.0cm}
{\color{zhuse}\rule{\textwidth}{2.5pt}}\\[6pt]
{\color{zhuse!15}\rule{\textwidth}{9pt}}\\[1.4cm]
{\Huge\bfseries 第 N 讲\quad 标题}\\[0.55cm]
{\LARGE English Title}\\[1.5cm]
{\color{zhuse!15}\rule{\textwidth}{9pt}}\\[4pt]
{\color{zhuse}\rule{\textwidth}{2.5pt}}\\[1.8cm]

\begin{tcolorbox}[enhanced,width=0.86\textwidth,colback=luv,colframe=zhuse,
  arc=3pt,boxrule=1pt,left=14pt,right=14pt,top=12pt,bottom=12pt]
\large
\begin{itemize}[leftmargin=1.6em]
  \item 课程:课程名(中文译名)
  \item 学期:2026 -- 2027 学年 秋季学期(Fall)
  \item 主讲:教师名 \quad 文档类型:课堂讲义(Lecture Notes)
  \item 依据:课件《XN Title》全 NN 页逐图精讲
  \item 绘图:电路图以 TikZ / CircuiTikZ 重新绘制(标准 IEEE 逻辑符号)  % 按实际改
\end{itemize}
\end{tcolorbox}

\vspace{1.3cm}
{\large 本讲知识地图}\\[10pt]
% TikZ 知识地图:一排主线节点 + 必要的支线,箭头表达先后/依赖
\begin{tikzpicture}[font=\footnotesize,
  box/.style={draw=zhuse,fill=luv,rounded corners=2pt,minimum height=8.5mm,
              inner sep=5pt,align=center,text=zhuse!80!black},
  ar/.style={-{Stealth},zhulv,line width=1.1pt}]
  \node[box] (a) at (0,0)   {模块一\\两行以内};
  \node[box] (b) at (2.9,0) {模块二};
  \node[box] (c) at (5.8,0) {模块三};
  \draw[ar] (a) -- (b); \draw[ar] (b) -- (c);
\end{tikzpicture}

\vfill
{\small\color{hui}一句话说明绘图与来源约定。}
\vspace*{0.8cm}
\end{titlepage}

% ======================= 目录 =======================
\tableofcontents
\newpage

% ======================= 一、内容地图 =======================
\section{本讲内容地图}

配套课件为 \emph{XN Title.pdf}（共 NN 页）。用两三句话概括本讲主线,再给出模块对照表:

\begin{table}[H]
\centering
\small
\caption{本讲模块与课件页码对照}
\begin{tabularx}{\textwidth}{l c X}
\toprule
\textbf{模块} & \textbf{课件页} & \textbf{核心问题} \\
\midrule
% ↓ 示例行,逐模块替换(课件每个模块一行,不遗漏)
模块名 & P2 & 这一节回答什么问题? \\
模块名 & P4--P5 & 用"读者视角"的疑问句写 \\
% ...逐模块列出,不遗漏
\bottomrule
\end{tabularx}
\end{table}

% ======================= 二、名词对照 =======================
\section{专有名词中英文对照表}

\begin{longtable}{p{4.6cm} p{2.6cm} p{7.0cm}}
\caption{专有名词中英文对照}\label{tab:glossary}\\
\toprule
\textbf{英文专有名词} & \textbf{中文翻译} & \textbf{大白话解释} \\
\midrule
\endfirsthead
\multicolumn{3}{l}{\small 表~\ref{tab:glossary}（续）}\\
\toprule
\textbf{英文专有名词} & \textbf{中文翻译} & \textbf{大白话解释} \\
\midrule
\endhead
\bottomrule
\endfoot
% ↓ 示例行,覆盖本讲全部新术语
Term & 中文 & 用生活类比解释,不抄课件定义。 \\
\end{longtable}

% ======================= 三、正文 =======================
\section{第一大模块标题}

\subsection{小节标题（P2）}   % 标题必须标课件页码

开篇一两句交代这页课件在讲什么、为什么重要,然后直接讲解:

\begin{dinglibox}[定义:组合电路]
正式定义写在盒子里,术语加 \textbf{加粗}。
\end{dinglibox}

讲解正文\ldots

% 课件原图:抠图放灰框白底的 yuanbox,文件名与 images/chNN/ 中的实际文件一致
\begin{yuanbox}[课件原图:MUX 的"道岔"类比]
\includegraphics[width=0.86\linewidth]{ch06/fig-06-01-mux-railyard.png}
\end{yuanbox}

重绘版/讲解图与原图成对出现:

\begin{figure}[htbp]
\centering
\includegraphics[width=0.5\linewidth]{ch06/fig-06-07-mux-2x1-internal.png}
\caption{内部电路(课件第 7 页原图):一个反相器 + 两个与门 + 一个或门,实现的正是
化简式 $d=s_0'i_0+s_0 i_1$。}
\label{fig:NN-internal}
% 图注写法:解释这张图的原理和读法 + 注明课件页码,不逐个罗列画面元素
\end{figure}

\begin{litibox}[例题:某某]
题目\ldots

\textbf{解:} 分步写,每步给依据:
\begin{align*}
F &= \inv{a}b + a\inv{b} && \text{最小项之和} \\
  &= a \oplus b && \text{XOR 定义}
\end{align*}
\end{litibox}

课件上留白的表,补全时标注来源:
% 表格最后一列用 \textcolor{hui}{（解答）} 或"按方程求得"标注

课件之外的扩展必须标"补充":
\begin{itemize}
  \item \textbf{补充}:课件没有、但对理解有帮助的内容,一句话带过即可,不喧宾夺主。
\end{itemize}

% ======================= 末节:小结 =======================
\clearpage
\section{本讲小结}   % 顶层成节;若想挂在最后模块下作 \subsection 也可,全文统一即可

\begin{yaodbox}[本讲知识清单]
\begin{center}
\renewcommand{\arraystretch}{1.25}
\small
\begin{tabular}{@{}p{2.9cm} p{5.6cm} p{6.6cm}@{}}
\toprule
\textbf{\color{zhuse}构件} & \textbf{\color{zhuse}功能} & \textbf{\color{zhuse}要点} \\
\midrule
构件 & 输出只取决于当前输入 & 关键公式或一句话要点 \\
% ...一张表收拢全讲
\bottomrule
\end{tabular}
\end{center}
\end{yaodbox}

\begin{sikaobox}[课后自测]
% 写 5 道左右具体的题,覆盖本讲全部考点、不重复正文原题,可 \ref{} 引用正文图表:
% (1)基本定义复述;(2)核心推导;(3)改条件变式;(4)易错点辨析;(5)综合应用
(1)用设计三步法独立推导 2x1 MUX 的电路;(2)若把进位输入 $C_0$ 误接为 1,加法结果会怎样?
\end{sikaobox}

\vfill
\begin{center}
{\color{zhuse}\rule{0.5\textwidth}{1.2pt}}\\[6pt]
{\small\color{hui}\kaishu 本讲义依据课件《XN Title》（NN 页）编写;插图自课件原页 350\,dpi 高清截取,并逐图视觉校验。}
\end{center}

\end{document}
```

## 高频片段

并列双图（内部电路 + 符号、错/对对比）：

```latex
\begin{figure}[htbp]
\centering
\begin{minipage}[t]{0.52\linewidth}
\centering
\includegraphics[width=0.95\linewidth]{ch06/fig-06-09-mux-4x1-internal.png}
\end{minipage}\hfill
\begin{minipage}[t]{0.40\linewidth}
\centering
\includegraphics[width=0.8\linewidth]{ch06/fig-06-10-mux-4x1-symbol.png}
\end{minipage}
\caption{左:内部电路;右:封装符号(课件第 9 页原图)。}
\label{fig:NN-pair}
\end{figure}
```

【电路课件】门级电路重绘骨架（反相输入线头放右上角统一生成，避免线交叉）：

```latex
\begin{figure}[htbp]
\centering
\begin{tikzpicture}
  % 输入线头(正变量 x=0/0.6/1.2,反变量 x=6.9/6.3/5.7,反相器集中在右上角)
  % \invheader 类宏按需定义;数据流从左到右,高亮当前分析路径用 hl/hlr
  \node[and port,number inputs=3] (g1) at (4,1) {};
  \draw[wire] (0,1.4) node[left,lab]{$s_1'$} -- (g1.in 1);
  \draw[hl]   (g1.out) -- ++(1.2,0) node[right,lab]{$d$};  % 高亮输出
\end{tikzpicture}
\caption{……}
\end{figure}
```

## 编译与交付

```bash
cd "AI Notes/tex"
xelatex -interaction=nonstopmode -halt-on-error "第N讲-标题.tex"
xelatex -interaction=nonstopmode -halt-on-error "第N讲-标题.tex"   # 第二遍出目录/交叉引用
cp "第N讲-标题.pdf" "../pdf/"
```

渲染逐页 PNG 供视觉审查（pymupdf，跨平台最稳）：

```python
import pymupdf
from pathlib import Path
doc = pymupdf.open("第N讲-标题.pdf")
out = Path("render"); out.mkdir(exist_ok=True)
for i, page in enumerate(doc, 1):
    page.get_pixmap(dpi=110).save(out / f"pg{i:02d}.png")
```
