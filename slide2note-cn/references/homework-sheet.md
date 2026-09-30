# 配套课后作业卷模板

仅在用户要求"配一份作业/练习卷"时使用。独立 tex → 独立 PDF：`AI Notes/tex/homework-tN.tex` → `AI Notes/pdf/第N讲-课后作业.pdf`。

## 结构（顺序固定）

1. **作业头**：居中标题（第N讲课后作业：主题）+ 课程名 + 姓名/学号/班级/得分下划线填写栏。
2. **作答要求盒**（tipbox）：覆盖的考点范围、作答规范（如"计算与证明题必须写出每一步及所依据的定理/公式/定义名称，只写结果不得分"）、总分与附加题说明。
3. **题型分节**：按难度递进分节，每节标分值，如 `\section{概念辨析与直接应用（每题 2 分，共 20 分）}`。典型结构：
   - 概念辨析 / 直接套用（低难度，覆盖面广）
   - 多步计算 / 方法应用（中难度）
   - 证明题（写全步骤）
   - 综合应用（真值表 ↔ 标准形式 ↔ 电路）
   - 附加题（选做，另加分，不计入满分）
4. **参考答案**：每大题后面紧跟一个 ansbox，按题号给完整解答（含每步依据）。
5. **考点覆盖对照表**（tipbox）：末尾列出每个考点分别由哪些题覆盖，用于自检"没有漏考点"。

## 导言区差异（相对讲义模板）

- 讲义模板导言区基础上：删去 graphicx、tikz/circuitikz 与 yuanbox（作业卷一般无插图）；彩盒里没有 tipbox，需自带颜色与定义，新增：

```latex
\definecolor{primary}{HTML}{33459B}
\definecolor{primarylight}{HTML}{EEF1FB}
\newtcolorbox{tipbox}[1][提示]{colback=primarylight, colframe=primary, boxrule=0.6pt,
  arc=2pt, left=8pt, right=8pt, top=6pt, bottom=6pt,
  title={\small\bfseries #1}, fonttitle={\color{white}},
  colbacktitle=primary, before skip=10pt, after skip=10pt}
\definecolor{anslight}{HTML}{F2F7F2}
\definecolor{anscolor}{HTML}{2F6B3C}
\newtcolorbox{ansbox}[1][参考答案]{colback=anslight, colframe=anscolor, boxrule=0.6pt,
  arc=2pt, left=8pt, right=8pt, top=6pt, bottom=6pt, breakable,
  title={\small\bfseries #1}, fonttitle={\color{white}},
  colbacktitle=anscolor, before skip=10pt, after skip=10pt}
\newcommand{\blank}{\underline{\hspace{1.9cm}}}   % 填空
```

- 页眉右侧改为"第N讲课后作业 · 主题"。

## 命题规则

- **覆盖优先**：题目合起来必须覆盖讲义/课件的全部定理、公式或方法，不遗漏（这是作业卷存在的意义）。
- 每步给分的可验证性：解答里写明每一步的依据名称。
- 难度梯度：低难度题占约 1/3 分值，保证基础题拿分；附加题考综合/进阶，与正题不重复。
- 题目风格与课件/讲义例题一致（同样的记号、同样的术语），不要引入课件没讲过的记号。
- 满分设计成整数（如 100 分），附加题单独标分（如另加 10 分）。
