#!/usr/bin/env python3
"""
cleanup.py

Tidy the per-course workspace (<vault>/_slide2note/<课程名>/) before
delivery: delete LaTeX build artifacts, visual-review renders, courseware
page renders, leftover section scaffolding, and orphan figure PNGs the
final .tex no longer references. Deliverables (tex sources, referenced
figures) and everything outside the workspace (especially the delivery
root AI Notes/) are never touched.

Default is a dry run listing what would be deleted; pass --apply to execute.

Use --check <course-folder> instead of cleaning to verify delivery purity:
AI Notes/ must contain flat PDFs only, and the course folder must hold no
scattered AI intermediates (tex files, build artifacts, render dirs,
ledgers, .zcode residue, ...).

Examples:
    python3 cleanup.py "_slide2note/Intro to Circuits"             # dry run
    python3 cleanup.py "_slide2note/Intro to Circuits" --apply     # clean + tree
    python3 cleanup.py --check "Intro to Circuits(2026-2027 Fall)" # purity check
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import shutil
import sys

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


# ---------------------------------------------------------------- cleanup ---

def clean_workspace(root: Path, tex_args, apply: bool) -> int:
    texdir = root / "tex"
    imgdir = root / "images"

    if not texdir.is_dir():
        print(f"error: no tex/ directory under {root}", file=sys.stderr)
        return 2

    all_tex = sorted(texdir.glob("*.tex"))
    if tex_args:
        delivery = sorted({root / t if not t.is_absolute() else t for t in tex_args})
        for t in delivery:
            if not t.is_file():
                print(f"error: tex not found: {t}", file=sys.stderr)
                return 2
    else:
        delivery = [t for t in all_tex if not SCAFFOLD_RE.match(t.name)]
        if not delivery:
            print("error: no delivery tex found (only main/secN scaffolding?); "
                  "pass --tex explicitly", file=sys.stderr)
            return 2
    scaffolds = [t for t in all_tex if t not in delivery and SCAFFOLD_RE.match(t.name)]

    keep_images, stems, inputs = scan_references(delivery)

    # 未合并的分册结构：交付 tex 仍 \input 脚手架 → 脚手架与其引用一并保留
    if scaffolds and any(s.name in inputs for s in scaffolds):
        print("note: delivery tex still \\inputs scaffolding -> scaffolding kept")
        img2, stem2, _ = scan_references(scaffolds)
        keep_images |= img2
        stems |= stem2
        scaffolds = []

    build_artifacts = [
        p for p in sorted(texdir.iterdir())
        if p.is_file() and p.name.endswith(BUILD_SUFFIXES)
    ]
    render_files: list[Path] = []
    render_dir = root / "render"           # 审查渲染（工作区顶层）
    tex_render_dir = texdir / "render"     # 旧布局兼容：tex/ 下的渲染
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
        description="Tidy the per-course workspace before delivery (dry run by default), "
                    "or verify delivery purity with --check."
    )
    parser.add_argument("root", type=Path, nargs="?", default=None,
                        help="workspace root, e.g. _slide2note/<课程名> (omit with --check)")
    parser.add_argument("--tex", type=Path, action="append", default=None,
                        metavar="TEX",
                        help="delivery tex path(s) under root (default: auto-detect)")
    parser.add_argument("--apply", action="store_true",
                        help="actually delete (default: dry run)")
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
    return clean_workspace(args.root.resolve(), args.tex, args.apply)


if __name__ == "__main__":
    raise SystemExit(main())
