# slide2note_CN

把课程课件 PDF（英文幻灯片）制作成排版精良的**中文 LaTeX 讲义 PDF** 的 ZCode skill。

- 输入：一份课件幻灯片 PDF（如 `T6 Logic Optimization.pdf`）
- 输出：一份可复习、可打印的中文讲义 PDF（xelatex / ctexart / tcolorbox），可选配套课后作业卷 PDF

## 核心原则

1. **忠实课件** — 逐页覆盖、不遗漏模块；补全与课外扩展显式标注。
2. **直接讲解** — 不逐字复述幻灯片；讲解消化内容，而非翻译幻灯片。
3. **排版精良** — 公式全部 LaTeX 化、语义化彩盒、统一主题色；成品经逐页视觉审查。

## 安装

把 `slide2note-cn/` 目录复制（或软链）到 ZCode 的技能目录：

```bash
git clone https://github.com/CEQ151/slide2note_CN.git
mkdir -p ~/.agents/skills
cp -R slide2note_CN/slide2note-cn ~/.agents/skills/
```

重启 ZCode 会话后即可自动触发，或用 `/slide2note-cn` 显式调用。

## 依赖

- TeX 发行版（xelatex + ctex + tcolorbox + circuitikz 等，推荐 MacTeX/TeX Live full）
- Python：pymupdf（渲染审查页 + 抠图坐标查询）、Pillow（残字白化）
- 抠图依赖 `pdf-figure-extractor` 技能（内含 safe_crop.py）

## 目录结构

```
slide2note-cn/
├── SKILL.md                      # 工作流程 + 硬性排版规则 + 彩盒体系
└── references/
    ├── latex-template.md         # 完整导言区与文档骨架（复制后填充）
    ├── figure-extraction.md      # 抠图实操守则（坐标精确查询、padding 补偿、残字白化）
    └── homework-sheet.md         # 配套课后作业卷模板（可选）
```

## 触发方式

对 ZCode 说：

- "把 T6.pdf 转成中文讲解 PDF / 讲义"
- "为第 7 讲做一份讲义"
- "给这一讲配一份课后作业卷"

## License

MIT
