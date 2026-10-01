# LaTeX 讲义模板（复制后填充）

导言区取自实际交付中迭代出的"完全体"版本。标记【可选:领域绘图】的块只在课件含专业图形（电路、化工流程、力学示意等）时才需要，纯文字/代数类讲义可整块删去。

## 完整导言区

```latex
\documentclass[11pt,a4paper,fontset=mac]{ctexart}   % Windows 用 fontset=windows；非 macOS 记得调整此项

% ============================================================
%  第N讲 标题 课堂讲义
%  <课程名> <学年学期>
% ============================================================
\usepackage[margin=2.1cm,top=2.2cm,bottom=2.4cm,headheight=13.5pt]{geometry}
\usepackage{amsmath,amssymb}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{tabularx}   % 内容地图等通栏表格用 X 列
\usepackage{longtable}  % 名词对照等跨页长表
\usepackage{float}      % [H] 严格定位
\usepackage{multicol}   % 局部双栏（multicols 环境）
\usepackage{wrapfig}    % 文字环绕小图（wrapfigure 环境）
\usepackage{array}
\usepackage{xcolor}
\usepackage{colortbl}
% 【可选:领域绘图】电路类课件用 CircuiTikZ；其他领域按需换 chemfig / mhchem / 自绘 TikZ
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
\definecolor{xianlu}{HTML}{1F2937}  % 【可选:领域绘图】电路线条色

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

% ---------- 【可选:领域绘图】电路类通用设置与常用宏 ----------
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
  \item 学期:XXXX -- XXXX 学年 第X学期(按实际填写)
  \item 主讲:教师名 \quad 文档类型:课堂讲义(Lecture Notes)
  \item 依据:课件《XN Title》全 NN 页逐图精讲
  \item 绘图:示意图按课件重绘(TikZ,风格统一)  % 按实际改;无重绘图可删此行
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

\begin{dinglibox}[定义:动态规划]
正式定义写在盒子里,术语加 \textbf{加粗}。
\end{dinglibox}

讲解正文\ldots

% 课件原图:抠图放灰框白底的 yuanbox,文件名与 images/chNN/ 中的实际文件一致
\begin{yuanbox}[课件原图:工厂流水线类比]
\includegraphics[width=0.86\linewidth]{ch03/fig-03-01-assembly-line-analogy.png}
\end{yuanbox}

重绘版/讲解图与原图成对出现:

\begin{figure}[htbp]
\centering
\includegraphics[width=0.5\linewidth]{ch03/fig-03-07-pipeline-internal.png}
\caption{三级流水线结构(课件第 7 页原图):取指、译码、执行逐级传递,与正文推导的式 (3.1) 对应。}
\label{fig:NN-internal}
% 图注写法:解释这张图的原理和读法 + 注明课件页码,不逐个罗列画面元素
\end{figure}

\begin{litibox}[例题:递归复杂度分析]
题目\ldots

\textbf{解:} 分步写,每步给依据:
\begin{align*}
T(n) &= 2\,T(n/2) + cn && \text{分治递推式} \\
     &= O(n\lg n) && \text{主定理,情形 2}
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
(1)用自己的话解释流水线为什么能提升吞吐率;(2)证明正文中的式 (3.2);(3)若第二级耗时变为原来的两倍,瓶颈如何转移?
\end{sikaobox}

\vfill
\begin{center}
{\color{zhuse}\rule{0.5\textwidth}{1.2pt}}\\[6pt]
{\small\color{hui}\kaishu 本讲义依据课件《XN Title》（NN 页）编写;插图自课件原页 350\,dpi 高清截取,并逐图视觉校验。}
\end{center}

\end{document}
```

## 高频片段

**插图缩放参考**（每张 `\includegraphics` 都必须显式给宽度，按信息密度定档；禁止不缩放直接塞入造成"整页只有一张图没文字"；350 dpi 抠图缩小不糊，放心缩）：

```latex
% 小图(单符号/简单小电路/图标)   → 0.3--0.5\linewidth,优先 wrapfig 环绕或 minipage 并排
% 中图(结构图/流程图/单张电路图) → 0.5--0.75\linewidth
% 大图(多子图/密集标注复杂图表)  → 0.85--\linewidth
% 仅当原图极复杂、缩小后不可读时才可接近满页,且同页/次页必须紧跟讲解文字
```

并列双图（结构详图 + 简化符号、错/对对比）：

```latex
\begin{figure}[htbp]
\centering
\begin{minipage}[t]{0.52\linewidth}
\centering
\includegraphics[width=0.95\linewidth]{ch03/fig-03-09-pipeline-detail.png}
\end{minipage}\hfill
\begin{minipage}[t]{0.40\linewidth}
\centering
\includegraphics[width=0.8\linewidth]{ch03/fig-03-10-pipeline-symbol.png}
\end{minipage}
\caption{左:结构详图;右:简化符号(课件第 9 页原图)。}
\label{fig:NN-pair}
\end{figure}
```

文字环绕小图（`wrapfig`）：宽度 ≤ 半栏的小图配长段文字时用，打破"图占一整行"的单调——

```latex
% 纪律:环境放在"要环绕它的那段文字"之前;不要紧贴 \section/\subsection 标题
% (标题后先写一两行正文再插);不要放在页面最后几行(会伸进页边或整体被推走);
% multicols 内不要使用;宽度一般 0.35--0.5\linewidth
\begin{wrapfigure}{r}{0.42\linewidth}   % {r|l}{宽度}
\centering
\includegraphics[width=\linewidth]{ch03/fig-03-07-pipeline-internal.png}
\caption{三级流水线(课件第 7 页原图)。}
\label{fig:NN-wrap}
\end{wrapfigure}
被环绕的正文紧跟在环境之后书写\ldots 段落文字会自动沿图侧排布。
```

局部双栏（`multicols`）：适合并列要点、名词短释、习题列表等"密集短行"内容——

```latex
\begin{multicols}{2}
\textbf{要点一}\quad 短行内容\ldots

\textbf{要点二}\quad 短行内容\ldots
\end{multicols}
% 禁忌:multicols 内不能用 figure/table 浮动体与 longtable;
% 插图改用 \begin{center}\includegraphics...\end{center} + \captionof{figure}{...}\label{...}
% (caption 包提供 \captionof);宽表(tabularx{\textwidth}、longtable)不要包进 multicols
```

整册双栏：documentclass 保持单栏，封面与目录照常，在正文开始处用 `\twocolumn` 命令切换；此后跨栏大图/宽表用 `figure*` / `table*`（浮动到页顶），普通图按栏宽 `\columnwidth` 控制宽度。图表多且窄的讲义才用整册双栏，否则公式断行与宽表都会难看。

长讲拆分写作（`main.tex` + `secN-*.tex`，subagent 分节并行时用，交付前合并回单文件）——

```latex
% main.tex：导言区 + 封面/目录之后
\begin{document}
% ...封面 titlepage、\tableofcontents...
\input{sec1-intro}
\input{sec2-mux}
% ...
\end{document}

% secN-xxx.tex：只含正文，从 \section 开始，文件名=序号-模块短名
% 硬纪律:禁止出现任何导言区指令(\usepackage/\definecolor/\newtcolorbox/
% \newcommand 一律不许);只用主模板已定义的环境与宏
\section{模块标题}
\subsection{小节标题（P12--P13）}
```

给写作 subagent 的 brief 四要素：① 本节页码范围与节间边界（上一节已讲的不得重复）；② 本节台账条目（图已抠好、含最终文件名）；③ 定稿名词对照表；④ 上面的输出纪律。汇编后、编译前，编排者必须通读全册做衔接 pass（过渡、去重、口吻一致）。

【可选:领域绘图】门级电路重绘骨架（反相输入线头放右上角统一生成，避免线交叉；仅电路类课件需要）：

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
