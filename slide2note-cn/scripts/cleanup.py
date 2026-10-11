#!/usr/bin/env python3
"""
cleanup.py

Tidy the output root (AI Notes/) before delivery: delete LaTeX build
artifacts, visual-review renders, leftover section scaffolding, and orphan
figure PNGs the final .tex no longer references. Deliverables (tex sources,
pdf outputs, referenced figures) are never touched.

Default is a dry run listing what would be deleted; pass --apply to execute.

Example:
    python3 cleanup.py "AI Notes"              # dry run, print the plan
    python3 cleanup.py "AI Notes" --apply      # delete, then print final tree
"""

from __future__ import annotations

import argparse
from pathlib import Path
import re
import shutil
import sys

BUILD_SUFFIXES = (".aux", ".log", ".toc", ".out", ".synctex.gz", ".fls", ".fdb_latexmk")
SCAFFOLD_RE = re.compile(r"^(main\.tex|sec\d+-.*\.tex)$")

INCLUDE_RE = re.compile(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}")
INPUT_RE = re.compile(r"\\(?:input|include)\{([^}]+)\}")
GRAPHICSPATH_RE = re.compile(r"\\graphicspath\s*\{((?:\s*\{[^{}]*\}\s*)+)\}")


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


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Tidy the output root before delivery (dry run by default)."
    )
    parser.add_argument("root", type=Path, help="output root, e.g. AI Notes")
    parser.add_argument("--tex", type=Path, action="append", default=None,
                        metavar="TEX",
                        help="delivery tex path(s) under root (default: auto-detect)")
    parser.add_argument("--apply", action="store_true",
                        help="actually delete (default: dry run)")
    args = parser.parse_args()

    root = args.root.resolve()
    texdir = root / "tex"
    imgdir = root / "images"

    if not texdir.is_dir():
        print(f"error: no tex/ directory under {root}", file=sys.stderr)
        return 2

    all_tex = sorted(texdir.glob("*.tex"))
    if args.tex:
        delivery = sorted({root / t if not t.is_absolute() else t for t in args.tex})
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
    render_dir = texdir / "render"
    render_files = sorted(render_dir.rglob("*")) if render_dir.is_dir() else []

    pngs = set(imgdir.rglob("*.png")) if imgdir.is_dir() else set()
    referenced = {p for p in pngs if p.resolve() in keep_images or p.stem in stems}
    orphans = sorted(pngs - referenced)

    pdfs = sorted((root / "pdf").glob("*.pdf")) if (root / "pdf").is_dir() else []

    print(f"output root: {root}")
    print(f"delivery tex: {', '.join(t.name for t in delivery)}")
    print(f"keep: {len(referenced)} referenced figure(s), {len(pdfs)} pdf(s)")

    report("build artifacts", build_artifacts, root)
    report("review renders", render_files, root)
    report("scaffolding", scaffolds, root)
    report("orphan figures", orphans, root)

    total = len(build_artifacts) + len(render_files) + len(scaffolds) + len(orphans)
    if total == 0:
        print("nothing to clean, already tidy.")
        return 0

    if not args.apply:
        print("dry run: pass --apply to delete.")
        return 0

    for p in build_artifacts + scaffolds + orphans:
        p.unlink()
    if render_dir.is_dir():
        shutil.rmtree(render_dir)

    print(f"applied: {total} item(s) deleted. final tree:")
    print_tree(root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
