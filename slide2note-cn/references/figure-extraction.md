# 抠图实操守则（配合 pdf-figure-extractor 技能）

在幻灯片型课件 PDF（典型为 720x540 pt）上用 safe_crop.py 抠图时，第一轮约一半会返工。以下守则全部来自实测踩坑，裁剪前通读一遍能省掉整个返工轮。

## 核心：坐标永远精确查询，不要目测

目测 150 DPI 渲染图估算 bbox 非常不可靠——经常混入标题色带/相邻正文，或裁掉图内标签。做法：

```python
import fitz  # pymupdf
page = doc[page_no]
words = page.get_text('words')          # 每个词的精确 bbox
drawings = page.get_drawings()          # 色带、线条、矩形等矢量元素
```

用两者查到目标元素的精确坐标后再定 bbox，最终裁剪用 **350 DPI**。

## safe_crop.py 的 expand_rect 反向补偿

safe_crop.py 的 padding 会把框向四周各扩 `max(4pt, 尺寸的 1%)`。估算边界时必须把这 ~4pt 算进去反向补偿，否则扩完就蹭到相邻元素。

例：标题色带底边在 y=90，图顶元素在 y=93——93 扩完变 89，仍然蹭到色带，必须先上移 bbox。

## 文字反锯齿溢出（descender）

word bbox 不含反锯齿溢出：

- 字形下伸部（g/y/p/q）可比 words 报告的 y1 再低 2–4 pt；
- 同一行上方文字的 descender 会伸进下一行区域——定顶边时要么再压 4–6 pt，要么裁完后用 PIL 白化残留；
- 底边一律多留 ≥8 pt。

## 标题色带：逐页查，别用统一值

多数页的标题色带是 fill=(0.8,0.8,1.0) 的矩形、底边到 y=90，但存在个别页到 y=98.9。每页用 `page.get_drawings()` 查色带矩形实际底边，不要套统一值。

## 页脚页码

页码固定在约 (663,497)-(677,513)。裁剪区碰到 y≥490 且 x>640 时，裁完用 PIL 把该角白化，否则成品图右下角带着页码。

## 残字清理：优先 PIL 白化，别反复调 bbox

课件自带的孤立字符（项目符号、上一行 descender、 stray 字母）会混进裁剪区。先查 word 坐标确认残字与正文内容错开，然后按精确 bbox 用 PIL 白化——比反复调裁剪框快得多：

```python
from PIL import Image, ImageDraw
im = Image.open(path); d = ImageDraw.Draw(im)
s = 350/72  # dpi 缩放
d.rectangle([x0*s, y0*s, x1*s, y1*s], fill='white')
im.save(path)
```

## 标签压在色带上：颜色键清除

图内标签压在标题色带上时（如 "1▼"），把色带一起裁进来，再用 PIL 按颜色键清除：把接近 RGB(204,204,255) 的像素整批置白（色距 <60），可完整保留深色线条和文字。

## 校验流程

1. 批量裁剪用**清单循环**（bbox + 每图的白化坐标写在清单里），不要逐图手跑。
2. 裁完逐张 Read 目检：四边有无截断、有无混入色带/相邻正文/页脚、残字。
3. safe_crop 报的**边缘接触 warning 一律当真**——查了多半真有截断。
4. 交付前子 agent 视觉审查还会再抓一轮（红框裁断、底部问句 descender、箭头残影、省略号残点都抓到过），不要跳过。
