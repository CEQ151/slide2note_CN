# slide2note_CN

把课程课件 PDF（幻灯片）制作成排版精良的**中文 LaTeX 讲义 PDF** 的 ZCode skill。**自包含**：内置抠图脚本与方法论，安装这一个技能即可跑通全流程。

- 输入：一份课件幻灯片 PDF（任何学科，如 `Lecture 6 - Distributed Systems.pdf`）
- 输出：一份可复习、可打印的中文讲义 PDF（xelatex / ctexart / tcolorbox），可选配套课后作业卷 PDF

## 核心原则

1. **忠实课件 + 零漏图** — 逐页覆盖、不遗漏模块；全册图片台账保证课件里每张图都收录并讲解到位（纯装饰性整活图除外，但豁免留痕）。
2. **直接讲解** — 不逐字复述幻灯片；讲解消化内容，而非翻译幻灯片。
3. **排版精良** — 公式全部 LaTeX 化、语义化彩盒、统一主题色；单栏/双栏/文字环绕多种版式；长讲按模块派 subagent 分节并行写作（固定术语表 + 输出纪律 + 衔接通读），杜绝尾部板块缩水；成品经逐页视觉审查。

## 安装

```bash
git clone https://github.com/CEQ151/slide2note_CN.git
mkdir -p ~/.agents/skills
cp -R slide2note_CN/slide2note-cn ~/.agents/skills/
```

重启 ZCode 会话后即可自动触发，或用 `/slide2note-cn` 显式调用。

## 依赖

- TeX 发行版：xelatex + ctex + tcolorbox（推荐 MacTeX / TeX Live full）
- Python 3：`pip install -r ~/.agents/skills/slide2note-cn/requirements.txt`（pymupdf / Pillow / numpy，用于抠图与审查渲染）

## 输出布局（双根制）

构建与交付严格分离，课程文件夹内不再出现任何中间产物：

```
<Obsidian vault>\
├── _slide2note\                        ← 构建根（加入 Obsidian 同步排除与索引排除）
│   ├── <课程名>\
│   │   ├── tex\                        ← 讲义/作业卷 tex 源 + 编译现场
│   │   ├── images\chNN\                ← 课件抠图切片
│   │   ├── render\                     ← 逐页视觉审查渲染（可再生）
│   │   ├── pages\                      ← 课件整页渲染（可再生）
│   │   └── notes\                      ← 图片台账、md 草稿
│   └── _legacy\<课程名>\               ← 存量迁移时的灰色文件归档
└── <课程文件夹>\
    ├── AI Notes\                       ← 交付根：只平铺最终讲义/作业卷 PDF
    └── （课件 PDF、教材等原始资料原地不动）
```

课件不在 Obsidian vault 内时回退为本地布局：`<课件目录>/_slide2note/` + `<课件目录>/AI Notes/`。旧库一次性整理用 `scripts/migrate_vault.py`（默认 dry-run）。

## 目录结构

```
slide2note-cn/
├── SKILL.md                      # 工作流程 + 硬性排版规则 + 彩盒体系
├── requirements.txt              # Python 依赖
├── scripts/
│   ├── safe_crop.py              # 高分辨率渲染裁剪（边缘接触检测）
│   ├── shrink_images.py          # PNG 批量压图（5MB 体积红线降载阶梯）
│   ├── cleanup.py                # 工作区收尾清理（dry-run 默认）+ 交付纯净检查（--check）
│   └── migrate_vault.py          # 旧库一次性整理：产物出库、AI Notes 纯净化
└── references/
    ├── latex-template.md         # 完整导言区与文档骨架（复制后填充）
    ├── figure-extraction.md      # 抠图方法论与踩坑守则
    └── homework-sheet.md         # 配套课后作业卷模板（可选）
```

## 触发方式

对 ZCode 说：

- "把 Lecture6.pdf 转成中文讲解 PDF / 讲义"
- "为第 7 讲做一份讲义"
- "给这一讲配一份课后作业卷"

## License

MIT
