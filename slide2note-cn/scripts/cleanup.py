#!/usr/bin/env python3
"""
cleanup.py — workspace hygiene for slide2note-cn. One entry point, four
modes, all dry-run by default; pass --apply to execute.

  (default)  Tidy the per-course workspace (<vault>/_slide2note/<课程名>/)
             before delivery: delete LaTeX build artifacts (scanned across
             the whole workspace), review renders (render/), courseware page
             renders (pages/), leftover scaffolding (main/secN tex), and
             orphan figure PNGs the delivery tex no longer references.
             Deliverables and everything outside the workspace (especially
             the delivery root AI Notes/) are never touched.
  --aux      Timely post-compile cleanup: delete build artifacts anywhere in
             the workspace and nothing else. Run right after a successful
             compile; keep the log untouched while a compile is failing.
  --organize Naming hygiene for the workspace: mechanically normalize messy
             image filenames (case, spaces/underscores, full-width chars,
             missing zero padding, -v2/-final draft suffixes) and rewrite
             \includegraphics references in the delivery tex accordingly;
             delete known probe/temp garbage and empty image directories.
             Violations that need the picture ledger (Chinese slugs, missing
             page numbers, loose images outside chNN/, off-convention tex
             names) are reported only, never auto-renamed.
  --check    Delivery purity check (takes the course folder instead of the
             workspace root): AI Notes/ must hold flat PDFs only and the
             course folder must hold no scattered AI intermediates.

Examples:
    python3 cleanup.py "_slide2note/Intro to Circuits"                # dry run
    python3 cleanup.py "_slide2note/Intro to Circuits" --apply        # clean + tree
    python3 cleanup.py "_slide2note/Intro to Circuits" --aux --apply  # post-compile
    python3 cleanup.py "_slide2note/Intro to Circuits" --organize --apply
    python3 cleanup.py --check "Intro to Circuits(2026-2027 Fall)"    # purity check
"""

from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import re
import shutil
import sys
import unicodedata

BUILD_SUFFIXES = (".aux", ".log", ".toc", ".out", ".synctex.gz", ".fls", ".fdb_latexmk")
SCAFFOLD_RE = re.compile(r"^(main\.tex|sec\d+-.*\.tex)$")

INCLUDE_RE = re.compile(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}")
INPUT_RE = re.compile(r"\\(?:input|include)\{([^}]+)\}")
GRAPHICSPATH_RE = re.compile(r"\\graphicspath\s*\{((?:\s*\{[^{}]*\}\s*)+)\}")

# ---- 交付纯净检查（--check）用的 AI 残留特征 ----
RESIDUE_DIR_NAMES = {"render", "_render", "latex_build", ".zcode", ".trash"}
RESIDUE_DIR_PREFIXES = ("_courseware_pages",)
RESIDUE_FILE_RES = [
    re.compile(p)
    for p in (
        r"^ledger-.*\.md$",
        r"^图片台账-.*\.md$",
        r"^_probe_.*\.png$",
        r"^fig-\d+-.*\.png$",
        r"^pg\d+\.png$",
        r"^page-?\d+\.png$",
    )
]

# ---- 命名整理（--organize）----
# 已知垃圾文件：工作区内 render/、pages/ 之外的探查渲染、临时文件、错位编译产物
GARBAGE_FILE_RES = [
    re.compile(p)
    for p in (
        r"^_probe_.*",
        r"^_tmp_.*",
        r"^pg\d+\.(?:png|jpe?g)$",
        r"^page-?\d+\.(?:png|jpe?g)$",
    )
]
GARBAGE_EXACT = {".zcodeignore"}

IMAGE_EXTS = {".png", ".jpg", ".jpeg"}
FIG_STEM_RE = re.compile(r"^fig-\d+-\d+-[a-z0-9-]+$")          # fig-图序-页-slug
FIG_PARTS_RE = re.compile(r"^fig-(\d+)-(\d+)-(.+)$")
DRAFT_TAIL_RE = re.compile(r"-(?:v\d+|final|copy|new|old|draft|副本|\(\d+\))$")
DELIVERY_TEX_RE = re.compile(r"^第\d+讲-")


def parse_graphicspaths(text: str) -> list[str]:
    """Extract base dirs from \\graphicspath{{a}{b}} declarations."""
    bases: list[str] = []
    for outer in GRAPHICSPATH_RE.findall(text):
        bases += re.findall(r"\{([^{}]+)\}", outer)
    return bases


def scan_references(tex_files: list[Path]) -> tuple[set[Path], set[str], set[str]]:
    """Scan tex files; return (image paths to keep, referenced stems, input names)."""
    keep_images: set[Path] = set()
    stems: set[str] = set()
    inputs: set[str] = set()
    for tex in tex_files:
        text = tex.read_text(encoding="utf-8", errors="replace")
        bases = parse_graphicspaths(text)
        for name in INCLUDE_RE.findall(text):
            name = name.strip()
            if not name:
                continue
            stems.add(Path(name).stem)
            candidates = [tex.parent / name] + [tex.parent / b / name for b in bases]
            for cand in candidates:
                if cand.suffix == "":
                    cand = cand.with_suffix(".png")
                keep_images.add(cand.resolve())
        for name in INPUT_RE.findall(text):
            if name.strip():
                inputs.add(Path(name.strip()).with_suffix(".tex").name)
    return keep_images, stems, inputs


def rewrite_include_stems(tex: Path, stem_map: dict[str, str]) -> bool:
    """Rewrite \\includegraphics arguments whose stem is renamed. Returns changed."""
    text = tex.read_text(encoding="utf-8", errors="replace")
    changed = False

    def sub(m: re.Match) -> str:
        nonlocal changed
        arg = m.group(1)
        base = re.split(r"[/\\]", arg)[-1]
        if "." in base:
            stem, dot, ext = base.rpartition(".")
        else:
            stem, dot, ext = base, "", ""
        new_stem = stem_map.get(stem)
        if not new_stem:
            return m.group(0)
        new_arg = arg[: len(arg) - len(base)] + new_stem + dot + ext
        changed = True
        return m.group(0).replace("{" + arg + "}", "{" + new_arg + "}")

    new_text = INCLUDE_RE.sub(sub, text)
    if changed:
        tex.write_text(new_text, encoding="utf-8")
    return changed


def fmt_size(n: int) -> str:
    return f"{n / 1048576:.2f} MB" if n >= 1048576 else f"{n / 1024:.1f} KB"


def report(title: str, paths: list[Path], root: Path) -> None:
    if not paths:
        print(f"delete {title}: none")
        return
    size = sum(p.stat().st_size for p in paths if p.is_file())
    print(f"delete {title}: {len(paths)} item(s), {fmt_size(size)}")
    for p in paths[:50]:
        print(f"  {p.relative_to(root)}")
    if len(paths) > 50:
        print(f"  ... and {len(paths) - 50} more")


def print_tree(root: Path) -> None:
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root)
        if path.is_dir():
            print(f"  {rel}/")
        else:
            print(f"  {rel}  ({fmt_size(path.stat().st_size)})")


def sha256_of(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def resolve_tex(root: Path, tex_args) -> tuple[list[Path], list[Path], list[Path]] | None:
    """Return (scan_tex, scaffolds_to_delete) plus the delivery list, or None on error.

    scan_tex = delivery tex + scaffolds still \\input (kept), i.e. everything
    whose \\includegraphics references matter.
    """
    texdir = root / "tex"
    if not texdir.is_dir():
        print(f"error: no tex/ directory under {root}", file=sys.stderr)
        return None
    all_tex = sorted(texdir.glob("*.tex"))
    if tex_args:
        delivery = sorted({root / t if not t.is_absolute() else t for t in tex_args})
        for t in delivery:
            if not t.is_file():
                print(f"error: tex not found: {t}", file=sys.stderr)
                return None
    else:
        delivery = [t for t in all_tex if not SCAFFOLD_RE.match(t.name)]
        if not delivery:
            print("error: no delivery tex found (only main/secN scaffolding?); "
                  "pass --tex explicitly", file=sys.stderr)
            return None
    scaffolds = [t for t in all_tex if t not in delivery and SCAFFOLD_RE.match(t.name)]
    scan_tex = list(delivery)
    if scaffolds:
        _, _, inputs = scan_references(delivery)
        if any(s.name in inputs for s in scaffolds):
            print("note: delivery tex still \\inputs scaffolding -> scaffolding kept")
            scan_tex += scaffolds
            scaffolds = []
    return delivery, scan_tex, scaffolds


# ---------------------------------------------------------------- --check ---

def check_course_folder(course: Path) -> int:
    """交付纯净检查：AI Notes 只有平铺 PDF；课程文件夹无散落 AI 残留。"""
    problems: list[str] = []

    ai = course / "AI Notes"
    if not ai.is_dir():
        problems.append(f"AI Notes/ 不存在: {ai}")
    else:
        for p in sorted(ai.iterdir()):
            if p.is_dir():
                problems.append(f"AI Notes/ 内有子目录: {p.name}/")
            elif p.suffix.lower() != ".pdf":
                problems.append(f"AI Notes/ 内非 PDF 文件: {p.name}")

    for dirpath, dirnames, filenames in os.walk(course):
        rel = Path(dirpath).relative_to(course)
        if rel.parts and rel.parts[0] == "AI Notes":
            dirnames[:] = []  # AI Notes 已单独检查
            continue
        for d in sorted(dirnames):
            if d in RESIDUE_DIR_NAMES or d.startswith(RESIDUE_DIR_PREFIXES):
                problems.append(f"残留目录: {rel / d}/")
        for f in sorted(filenames):
            suffix = Path(f).suffix.lower()
            if f == ".zcodeignore":
                problems.append(f"残留工作区文件: {rel / f}")
            elif suffix in BUILD_SUFFIXES or suffix == ".tex" or suffix == ".py":
                problems.append(f"残留中间文件: {rel / f}")
            elif any(rx.match(f) for rx in RESIDUE_FILE_RES):
                problems.append(f"残留渲染/切片: {rel / f}")

    if problems:
        print(f"FAIL: {len(problems)} 处不满足交付纯净要求（{course}）:")
        for p in problems:
            print(f"  {p}")
        return 1
    print(f"OK: 交付纯净检查通过（{course}）: AI Notes/ 只有平铺 PDF，无散落 AI 产物。")
    return 0


# ---------------------------------------------------------------- --aux -----

def find_build_artifacts(root: Path) -> list[Path]:
    return [p for p in sorted(root.rglob("*"))
            if p.is_file() and p.name.endswith(BUILD_SUFFIXES)]


def clean_aux(root: Path, apply: bool) -> int:
    """及时清理：只删全工作区的编译产物，别的不动。"""
    artifacts = find_build_artifacts(root)
    print(f"workspace root: {root}")
    report("build artifacts", artifacts, root)
    if not artifacts:
        print("nothing to clean.")
        return 0
    if not apply:
        print("dry run: pass --apply to delete.")
        return 0
    for p in artifacts:
        p.unlink()
    print(f"applied: {len(artifacts)} build artifact(s) deleted.")
    return 0


# ---------------------------------------------------------------- --organize -

def normalize_stem(stem: str) -> str:
    """机械级文件名规范化：全角转半角、小写、空格/下划线转连字符、剥废稿后缀。"""
    s = unicodedata.normalize("NFKC", stem).lower()
    s = re.sub(r"[\s_]+", "-", s)
    s = re.sub(r"-{2,}", "-", s).strip("-")
    while True:
        stripped = DRAFT_TAIL_RE.sub("", s).rstrip("-")
        if stripped == s:
            return s
        s = stripped


def pad_fig_parts(stem: str) -> str:
    """fig-3-7-cell -> fig-03-07-cell（图序与页码补零到两位，>=两位不动）。"""
    m = FIG_PARTS_RE.match(stem)
    if not m:
        return stem
    nn, page, slug = m.groups()
    return f"fig-{int(nn):02d}-{int(page):02d}-{slug}"


def organize_workspace(root: Path, tex_args, apply: bool) -> int:
    """命名整理：机械级自动修 + 改写 tex 引用；语义级只报告。"""
    imgdir = root / "images"
    resolved = resolve_tex(root, tex_args)
    if resolved is None:
        return 2
    delivery, scan_tex, _scaffolds = resolved

    def exempt(p: Path) -> bool:
        rel = p.relative_to(root)
        return bool(rel.parts) and rel.parts[0] in ("render", "pages")

    # --- 游离垃圾：探查渲染、临时文件、错位编译产物（render/、pages/ 除外）---
    garbage = [
        p for p in sorted(root.rglob("*"))
        if p.is_file() and not exempt(p)
        and (p.name.endswith(BUILD_SUFFIXES)
             or p.name in GARBAGE_EXACT
             or any(rx.match(p.name) for rx in GARBAGE_FILE_RES))
    ]

    # --- 图片改名计划（同目录改名；跨目录归位需台账语义，只报告）---
    renames: list[tuple[Path, Path]] = []
    dup_delete: list[tuple[Path, Path]] = []
    conflicts: list[str] = []
    stem_map: dict[str, str] = {}
    manual: list[str] = []
    imgs = ([p for p in sorted(imgdir.rglob("*"))
             if p.is_file() and p.suffix.lower() in IMAGE_EXTS]
            if imgdir.is_dir() else [])
    by_stem: dict[str, list[Path]] = {}
    for p in imgs:
        by_stem.setdefault(p.stem, []).append(p)
    claimed: set[Path] = set()

    if scan_tex:
        _keep_imgs, keep_stems, _inputs = scan_references(scan_tex)
        garbage_set = set(garbage)
        for p in imgs:
            if p in garbage_set:
                continue  # 探查/临时渲染属垃圾，进删除清单，不做改名
            rel = p.relative_to(root)
            if len(by_stem[p.stem]) > 1:
                conflicts.append(f"{rel}（同名 stem 多个文件，自动改名会使引用歧义，请人工裁决）")
                continue
            referenced = p.stem in keep_stems
            if not referenced:
                manual.append(f"{rel}  （未被交付 tex 引用：刚抠未接线的新图按台账核对命名并接线；"
                              f"废稿孤儿交第 6 步清理）")
                continue
            target_stem = pad_fig_parts(normalize_stem(p.stem))
            will_rename = target_stem != p.stem
            if will_rename:
                target = p.with_name(target_stem + p.suffix.lower())
                if target.exists():
                    if sha256_of(p) == sha256_of(target):
                        dup_delete.append((p, target))
                        stem_map.setdefault(p.stem, target.stem)
                    else:
                        conflicts.append(f"{rel} -> {target.name}"
                                         f"（目标已存在且内容不同，保留原样，请人工裁决）")
                    continue
                if target in claimed:
                    conflicts.append(f"{rel} -> {target.name}（改名目标撞车，请人工裁决）")
                    continue
                claimed.add(target)
                renames.append((p, target))
                if stem_map.setdefault(p.stem, target_stem) != target_stem:
                    conflicts.append(f"{rel}（stem 映射冲突）")
            # 语义/位置报告基于改名后的路径
            final_rel = (renames[-1][1] if will_rename else p).relative_to(root)
            if len(final_rel.parts) < 2 or not re.match(r"^ch\d+$", final_rel.parts[1]):
                manual.append(f"{final_rel}  （游离在 images/ 根下：移入 chNN/，按台账改名+改写引用）")
            elif not FIG_STEM_RE.match(pad_fig_parts(normalize_stem(
                    (renames[-1][1] if will_rename else p).stem))):
                manual.append(f"{final_rel}  （不符合 fig-NN-页-slug：按台账改名+改写引用）")
        for t in delivery:
            if not DELIVERY_TEX_RE.match(t.name):
                manual.append(f"tex/{t.name}  （交付 tex 未按“第N讲-标题.tex”命名）")

    print(f"workspace root: {root}")
    print(f"delivery tex: {', '.join(t.name for t in delivery)}")

    if renames:
        print(f"rename {len(renames)} image(s):")
        for src, dst in renames:
            print(f"  {src.relative_to(root)} -> {dst.name}")
    if dup_delete:
        print(f"delete duplicate {len(dup_delete)} image(s)（与保留文件内容相同）:")
        for src, kept in dup_delete:
            print(f"  {src.relative_to(root)}  (== {kept.name})")
    report("garbage", garbage, root)
    empty_dirs = ([d for d in sorted(imgdir.rglob("*"))
                   if d.is_dir() and not any(d.iterdir())]
                  if imgdir.is_dir() else [])
    if empty_dirs:
        print(f"remove empty dir {len(empty_dirs)}:")
        for d in empty_dirs:
            print(f"  {d.relative_to(root)}/")
    if manual:
        print(f"manual（语义级，按图片台账改名并改写引用，脚本不动）{len(manual)}:")
        for m in manual:
            print(f"  {m}")
    if conflicts:
        print(f"conflict {len(conflicts)}（请人工裁决）:")
        for c in conflicts:
            print(f"  {c}")

    if not (renames or dup_delete or garbage or empty_dirs or manual or conflicts):
        print("naming already tidy.")
        return 0
    if renames or dup_delete:
        print("note: 若 notes/ 台账等笔记引用了旧图名，请同步更新。")

    if not apply:
        print("dry run: pass --apply to execute renames/deletes.")
        return 0

    for p in garbage:
        p.unlink()
    for src, _kept in dup_delete:
        src.unlink()
    for src, dst in renames:
        src.replace(dst)
    if stem_map:
        for tex in scan_tex:
            rewrite_include_stems(tex, stem_map)
    for d in sorted((p for p in imgdir.rglob("*") if p.is_dir()),
                    key=lambda d: len(d.parts), reverse=True):
        try:
            d.rmdir()  # 仅空目录可删，级联清掉父目录
        except OSError:
            pass
    print(f"applied: {len(renames)} rename(s), {len(dup_delete)} duplicate(s), "
          f"{len(garbage)} garbage, refs rewritten in {len(scan_tex)} tex file(s). "
          f"final workspace tree:")
    print_tree(root)
    return 0


# ---------------------------------------------------------------- cleanup ---

def clean_workspace(root: Path, tex_args, apply: bool) -> int:
    imgdir = root / "images"

    resolved = resolve_tex(root, tex_args)
    if resolved is None:
        return 2
    delivery, scan_tex, scaffolds = resolved

    keep_images, stems, _inputs = scan_references(scan_tex)

    build_artifacts = find_build_artifacts(root)
    render_files: list[Path] = []
    render_dir = root / "render"           # 审查渲染（工作区顶层）
    tex_render_dir = root / "tex" / "render"  # 旧布局兼容：tex/ 下的渲染
    for rd in (render_dir, tex_render_dir):
        if rd.is_dir():
            render_files += sorted(rd.rglob("*"))
    pages_files: list[Path] = []
    pages_dir = root / "pages"             # 课件整页渲染（可再生成）
    if pages_dir.is_dir():
        pages_files = sorted(pages_dir.rglob("*"))

    pngs = set(imgdir.rglob("*.png")) if imgdir.is_dir() else set()
    referenced = {p for p in pngs if p.resolve() in keep_images or p.stem in stems}
    orphans = sorted(pngs - referenced)

    print(f"workspace root: {root}")
    print(f"delivery tex: {', '.join(t.name for t in delivery)}")
    print(f"keep: {len(referenced)} referenced figure(s)")

    report("build artifacts", build_artifacts, root)
    report("review renders", render_files, root)
    report("courseware page renders", pages_files, root)
    report("scaffolding", scaffolds, root)
    report("orphan figures", orphans, root)

    total = (len(build_artifacts) + len(render_files) + len(pages_files)
             + len(scaffolds) + len(orphans))
    if total == 0:
        print("nothing to clean, already tidy.")
        return 0

    if not apply:
        print("dry run: pass --apply to delete.")
        return 0

    for p in build_artifacts + scaffolds + orphans:
        p.unlink()
    for rd in (render_dir, tex_render_dir, pages_dir):
        if rd.is_dir():
            shutil.rmtree(rd)

    print(f"applied: {total} item(s) deleted. final workspace tree:")
    print_tree(root)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Workspace hygiene: clean (default), timely aux cleanup (--aux), "
                    "naming organize (--organize), or delivery purity check (--check). "
                    "All dry-run by default."
    )
    parser.add_argument("root", type=Path, nargs="?", default=None,
                        help="workspace root, e.g. _slide2note/<课程名> (omit with --check)")
    parser.add_argument("--tex", type=Path, action="append", default=None,
                        metavar="TEX",
                        help="delivery tex path(s) under root (default: auto-detect)")
    parser.add_argument("--apply", action="store_true",
                        help="actually execute (default: dry run)")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--aux", action="store_true",
                      help="timely cleanup: delete build artifacts only")
    mode.add_argument("--organize", action="store_true",
                      help="naming hygiene: normalize image names + rewrite refs, "
                           "report semantic violations")
    parser.add_argument("--check", type=Path, metavar="COURSE",
                        help="delivery-purity check mode: verify COURSE folder has "
                             "flat-PDF-only AI Notes and no scattered AI residue")
    args = parser.parse_args()

    if args.check:
        if args.root is not None:
            print("error: --check 与位置参数 root 互斥，二选一", file=sys.stderr)
            return 2
        course = args.check.resolve()
        if not course.is_dir():
            print(f"error: course folder not found: {course}", file=sys.stderr)
            return 2
        return check_course_folder(course)

    if args.root is None:
        parser.error("需要工作区根目录参数（或改用 --check <课程文件夹>）")
    root = args.root.resolve()
    if args.aux:
        return clean_aux(root, args.apply)
    if args.organize:
        return organize_workspace(root, args.tex, args.apply)
    return clean_workspace(root, args.tex, args.apply)


if __name__ == "__main__":
    raise SystemExit(main())
