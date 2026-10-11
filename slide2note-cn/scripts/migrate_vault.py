#!/usr/bin/env python3
"""
migrate_vault.py

One-time reorganization of an Obsidian vault that still holds pre-workspace
slide2note output scattered inside course folders. Moves everything into the
dual-root layout:

  deliver   final PDFs (from any AI Notes*/pdf, AI Notes*/tex, latex_build)
                -> <course>/AI Notes/<name>.pdf   (flat, deduped by sha256)
  workspace tex sources -> <vault>/_slide2note/<course>/tex/
            figure slices (AI Notes*/images/**)  -> .../images/<subpath>
            ledgers / md drafts                  -> .../notes/
  legacy    gray-zone files & orphan build dirs  -> <vault>/_slide2note/_legacy/<course>/<relpath>
  delete    regenerable junk only: LaTeX build artifacts, review/page/probe
            renders, .zcode workspace residue
  leave     course materials (courseware PDFs, textbooks, user PDFs) untouched

Also rewrites stale "AI Notes/pdf/" links in vault .md files to the new flat
"AI Notes/" layout. Default is a dry run; pass --apply to execute.

Examples:
    python3 migrate_vault.py "D:/FALL_26_Preview"                     # dry run all
    python3 migrate_vault.py "D:/FALL_26_Preview" --course "Circuits" # dry run one course
    python3 migrate_vault.py "D:/FALL_26_Preview" --apply             # execute
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import shutil
import sys
from pathlib import Path

WS_NAME = "_slide2note"
LEGACY_NAME = "_legacy"
DELIVERY_NAME = "AI Notes"

SKIP_TOPLEVEL = {"Inbox", "Last year", "Icon"}      # vault 级非课程目录
NEVER_PRUNE = {".git", ".obsidian", ".trash", ".workbuddy"}

BUILD_SUFFIXES = (".aux", ".log", ".toc", ".out", ".synctex.gz", ".fls", ".fdb_latexmk")
IMG_SUFFIXES = {".png", ".jpg", ".jpeg"}

RENDER_FILE_RE = re.compile(r"^(pg\d+|page[-_]?\d+)\.(png|jpe?g)$", re.IGNORECASE)
COURSEWARE_PAGES_RE = re.compile(r"^_courseware_pages", re.IGNORECASE)
TLECTURE_DIR_RE = re.compile(r"^T\d+讲义$")
PROBE_FILE_RE = re.compile(r"^_probe_.*\.(png|jpe?g)$", re.IGNORECASE)
FIG_FILE_RE = re.compile(r"^fig-\d+-", re.IGNORECASE)
CH_DIR_RE = re.compile(r"^ch\d+$", re.IGNORECASE)
GRAY_DIR_NAMES = {"workbook_work", "_extract", "build"}

LINK_PATTERNS = [
    ("AI Notes/pdf/", "AI Notes/"),
    ("AI%20Notes/pdf/", "AI%20Notes/"),
]


def file_sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fmt_size(n: int) -> str:
    return f"{n / 1048576:.2f} MB" if n >= 1048576 else f"{n / 1024:.1f} KB"


def dir_files(d: Path) -> list[Path]:
    return [p for p in d.rglob("*") if p.is_file()]


def is_ai_tree(parts) -> bool:
    return any(p.lower().startswith("ai notes") for p in parts) or ("latex_build" in parts)


# ------------------------------------------------------------------ plan ----

class Plan:
    def __init__(self) -> None:
        self.deliver: list[tuple[Path, Path]] = []          # src -> course/AI Notes/x.pdf
        self.workspace: list[tuple[Path, str, Path]] = []   # src, kind, dst
        self.legacy_files: list[tuple[Path, Path]] = []     # src -> _legacy/... (files)
        self.legacy_dirs: list[tuple[Path, Path]] = []      # src -> _legacy/... (dirs)
        self.delete: list[Path] = []                        # files or dirs
        self.dedup_skipped: list[tuple[Path, Path]] = []    # identical to dst already there
        self.conflicts: list[tuple[Path, Path, Path]] = []  # src, wanted, renamed-to
        self.unclassified: list[tuple[str, Path]] = []      # course, path (report only)
        self.skipped: list[str] = []                        # untouched dir notes
        self._claimed: dict[Path, str] = {}                 # dst -> sha ("" for dir)

    def _claim(self, src: Path, dst: Path) -> Path | None:
        """Register src->dst with sha dedup + conflict rename. None = skip."""
        sha = file_sha(src)
        existing = self._claimed.get(dst)
        if existing is None and dst.is_file():
            existing = file_sha(dst)
        if existing is not None:
            if existing == sha:
                # 内容与目标位完全相同：标准副本已在（或将在）目标位，源文件清掉即可
                self.dedup_skipped.append((src, dst))
                return None
            stem, suf = dst.stem, dst.suffix
            for i in range(2, 100):
                cand = dst.with_name(f"{stem}-{i}{suf}")
                if cand not in self._claimed and not cand.exists():
                    self.conflicts.append((src, dst, cand))
                    self._claimed[cand] = sha
                    return cand
            return None
        self._claimed[dst] = sha
        return dst

    def add_deliver(self, src: Path, dst: Path) -> None:
        got = self._claim(src, dst)
        if got:
            self.deliver.append((src, got))

    def add_ws(self, src: Path, kind: str, dst: Path) -> None:
        got = self._claim(src, dst)
        if got:
            self.workspace.append((src, kind, got))

    def add_legacy_file(self, src: Path, dst: Path) -> None:
        got = self._claim(src, dst)
        if got:
            self.legacy_files.append((src, got))

    def add_legacy_dir(self, src: Path, dst: Path) -> None:
        if dst in self._claimed or dst.exists():
            # 目标侧已有同名目录：逐文件合并（apply 时处理），这里只登记
            self.legacy_dirs.append((src, dst))
            return
        self._claimed[dst] = ""
        self.legacy_dirs.append((src, dst))

    def add_delete(self, p: Path) -> None:
        self.delete.append(p)


# ------------------------------------------------------------ classifiers ---

def classify_dir(child: Path) -> str:
    """'descend' | 'delete' | 'legacy' | 'skip'（skip = 完全不动、不下钻）"""
    name = child.name
    if name in {".git", ".obsidian"}:
        return "skip"
    if name == ".zcode":
        return "delete"
    if name in {"render", "_render"}:
        files = dir_files(child)
        if files and all(RENDER_FILE_RE.match(p.name) for p in files):
            return "delete"
        return "legacy"
    if COURSEWARE_PAGES_RE.match(name):
        return "delete"
    if name == "tmp":
        files = dir_files(child)
        if files and all(p.suffix.lower() in IMG_SUFFIXES for p in files):
            return "delete"
        return "legacy"
    if name in GRAY_DIR_NAMES:
        return "legacy"
    if TLECTURE_DIR_RE.match(name):
        return "legacy"
    if name == "Notes":
        # 仅当带 AI 产物签名（images/chNN 或 fig-*.png）才当旧输出归档，真笔记不动
        for p in child.rglob("*"):
            if p.is_dir() and CH_DIR_RE.match(p.name):
                return "legacy"
            if p.is_file() and FIG_FILE_RE.match(p.name):
                return "legacy"
        return "descend"
    return "descend"


def classify_file(fp: Path, rel_dir_parts, course_dir: Path,
                  ws_course: Path, legacy_course: Path, plan: Plan) -> None:
    name = fp.name
    suffix = fp.suffix.lower()
    rel = Path(*rel_dir_parts) / name if rel_dir_parts else Path(name)
    ai = is_ai_tree(rel_dir_parts)

    if name == ".zcodeignore" or name.endswith(BUILD_SUFFIXES) or PROBE_FILE_RE.match(name):
        plan.add_delete(fp)
        return
    if suffix == ".py":  # 一次性脚本（crop_final.py / rebuild_vault.py 之类）
        plan.add_legacy_file(fp, legacy_course / rel)
        return

    if ai:
        if suffix == ".pdf":
            plan.add_deliver(fp, course_dir / DELIVERY_NAME / name)
        elif suffix == ".tex":
            plan.add_ws(fp, "tex", ws_course / "tex" / name)
        elif suffix in IMG_SUFFIXES and "images" in rel_dir_parts:
            idx = rel_dir_parts.index("images")
            sub = rel_dir_parts[idx + 1:]
            dst = ws_course / "images" / name if not sub else ws_course / "images" / Path(*sub) / name
            plan.add_ws(fp, "images", dst)
        elif suffix == ".md":
            plan.add_ws(fp, "notes", ws_course / "notes" / name)
        else:
            plan.unclassified.append((course_dir.name, fp))
        return

    # AI 树之外的课程文件夹
    if suffix == ".tex":  # 用户/历史的散落 tex 源 -> 灰色归档（成品 PDF 原地保留）
        plan.add_legacy_file(fp, legacy_course / rel)
    elif suffix in IMG_SUFFIXES:
        plan.unclassified.append((course_dir.name, fp))
    # 其余（课件 PDF、教材、用户资料）不动


def scan_course(course_dir: Path, ws_root: Path, plan: Plan) -> None:
    ws_course = ws_root / course_dir.name
    legacy_course = ws_root / LEGACY_NAME / course_dir.name
    for dirpath, dirnames, filenames in os.walk(course_dir):
        rel_dir = Path(dirpath).relative_to(course_dir)
        keep: list[str] = []
        for d in sorted(dirnames):
            child = Path(dirpath) / d
            act = classify_dir(child)
            if act == "descend":
                keep.append(d)
            elif act == "delete":
                plan.add_delete(child)
            elif act == "legacy":
                plan.add_legacy_dir(child, legacy_course / (rel_dir / d))
            else:  # skip
                plan.skipped.append(f"跳过不动: {child}")
        dirnames[:] = keep
        for f in sorted(filenames):
            classify_file(Path(dirpath) / f, rel_dir.parts, course_dir,
                          ws_course, legacy_course, plan)


# ----------------------------------------------------------------- apply ---

def merge_move_dir(src: Path, dst: Path) -> None:
    """移动目录；目标已存在时逐项合入（重名自动加 -N 后缀）。"""
    if not dst.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
        return
    for child in list(src.iterdir()):
        target = dst / child.name
        if target.exists():
            stem = target.stem if child.is_file() else child.name
            suf = child.suffix if child.is_file() else ""
            i = 2
            while (dst / f"{stem}-{i}{suf}").exists():
                i += 1
            target = dst / f"{stem}-{i}{suf}"
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(child), str(target))
    src.rmdir()


def prune_empty(course_dir: Path) -> list[Path]:
    removed: list[Path] = []
    for _ in range(4):
        found = False
        for dirpath, _dirnames, _files in os.walk(course_dir, topdown=False):
            d = Path(dirpath)
            if d == course_dir or d.name in NEVER_PRUNE:
                continue
            try:
                next(d.iterdir())
            except StopIteration:
                try:
                    d.rmdir()
                    removed.append(d)
                    found = True
                except OSError:
                    pass
            except OSError:
                pass
        if not found:
            break
    return removed


def rewrite_links(vault: Path, apply: bool) -> list[tuple[Path, int]]:
    changed: list[tuple[Path, int]] = []
    for dirpath, dirnames, filenames in os.walk(vault):
        dirnames[:] = [d for d in dirnames
                       if d not in {WS_NAME, ".obsidian", ".trash", ".workbuddy", ".git"}]
        for f in filenames:
            if not f.lower().endswith(".md"):
                continue
            p = Path(dirpath) / f
            try:
                text = p.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            new = text
            n = 0
            for a, b in LINK_PATTERNS:
                n += new.count(a)
                new = new.replace(a, b)
            if n:
                changed.append((p, n))
                if apply:
                    p.write_text(new, encoding="utf-8")
    return changed


# ---------------------------------------------------------------- report ---

def build_report(plan: Plan, vault: Path, ws_root: Path, links,
                 pruned: list[Path], apply: bool) -> str:
    lines: list[str] = []
    a = "**APPLIED**" if apply else "DRY RUN（加 --apply 执行）"
    lines.append(f"# slide2note 存量迁移报告（{a}）\n")
    lines.append(f"vault: `{vault}`\n")

    lines.append(f"\n## 1. 成品 PDF 平铺进各课 AI Notes/（{len(plan.deliver)} 个）")
    for src, dst in plan.deliver:
        lines.append(f"- {src} -> {dst}")

    if plan.dedup_skipped:
        lines.append(f"\n### 同内容重复：留目标位、清源文件（{len(plan.dedup_skipped)} 个）")
        for src, dst in plan.dedup_skipped:
            lines.append(f"- {src}（= {dst}）")
    if plan.conflicts:
        lines.append(f"\n### 同名不同内容，改名保留（{len(plan.conflicts)} 个）⚠️ 人工过目")
        for src, wanted, got in plan.conflicts:
            lines.append(f"- {src} -> {got.name}（{wanted} 已被占用）")

    by_kind: dict[str, list] = {}
    for src, kind, dst in plan.workspace:
        by_kind.setdefault(kind, []).append((src, dst))
    lines.append(f"\n## 2. 管线产物迁入工作区（共 {len(plan.workspace)} 个）")
    for kind, label in (("tex", "tex 源"), ("images", "图片切片"), ("notes", "台账/草稿")):
        items = by_kind.get(kind, [])
        lines.append(f"\n### {label}（{len(items)} 个）")
        for src, dst in items[:200]:
            lines.append(f"- {src} -> {dst.relative_to(ws_root)}")
        if len(items) > 200:
            lines.append(f"- ... 及另外 {len(items) - 200} 个")

    lines.append(f"\n## 3. 灰色地带归档 _legacy/（目录 {len(plan.legacy_dirs)} 个，文件 {len(plan.legacy_files)} 个）")
    for src, dst in plan.legacy_dirs:
        lines.append(f"- {src}/ -> {dst.relative_to(ws_root)}/")
    for src, dst in plan.legacy_files:
        lines.append(f"- {src} -> {dst.relative_to(ws_root)}")

    total_del_bytes = 0
    for p in plan.delete:
        try:
            if p.is_file():
                total_del_bytes += p.stat().st_size
            else:
                total_del_bytes += sum(f.stat().st_size for f in p.rglob("*") if f.is_file())
        except OSError:
            pass
    lines.append(f"\n## 4. 删除可再生垃圾（{len(plan.delete)} 项，{fmt_size(total_del_bytes)}）")
    for p in plan.delete[:120]:
        lines.append(f"- {p}")
    if len(plan.delete) > 120:
        lines.append(f"- ... 及另外 {len(plan.delete) - 120} 项")

    if plan.unclassified:
        lines.append(f"\n## 5. 未分类待定（{len(plan.unclassified)} 个，本次不动）")
        for course, p in plan.unclassified:
            lines.append(f"- [{course}] {p}")

    if plan.skipped:
        lines.append(f"\n## 6. 明确跳过不动（{len(plan.skipped)} 个目录）")
        for s in plan.skipped:
            lines.append(f"- {s}")

    lines.append(f"\n## 7. 笔记链接改写 AI Notes/pdf/ -> AI Notes/（{len(links)} 个文件）")
    for p, n in links:
        lines.append(f"- {p}（{n} 处）")

    if apply and pruned:
        lines.append(f"\n## 8. 迁移后清掉的空目录（{len(pruned)} 个）")
        for d in pruned:
            lines.append(f"- {d}")
    return "\n".join(lines) + "\n"


# ------------------------------------------------------------------ main ---

def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    parser = argparse.ArgumentParser(
        description="One-time migration of scattered slide2note output into the "
                    "central workspace layout (dry run by default).")
    parser.add_argument("vault", type=Path, help="Obsidian vault root (contains .obsidian/)")
    parser.add_argument("--course", action="append", default=None, metavar="NAME",
                        help="only process courses whose folder name contains NAME (repeatable)")
    parser.add_argument("--extra", action="append", default=None, metavar="RELPATH",
                        help="force-archive an extra vault-relative path into _legacy/ (repeatable)")
    parser.add_argument("--apply", action="store_true",
                        help="actually move/delete/rewrite (default: dry run)")
    args = parser.parse_args()

    vault = args.vault.resolve()
    if not (vault / ".obsidian").is_dir():
        print(f"error: not an Obsidian vault (no .obsidian/): {vault}", file=sys.stderr)
        return 2
    ws_root = vault / WS_NAME

    courses = sorted(
        d for d in vault.iterdir()
        if d.is_dir()
        and not d.name.startswith((".", "_"))
        and d.name not in SKIP_TOPLEVEL
    )
    if args.course:
        selected = []
        for pat in args.course:
            hits = [c for c in courses if pat.lower() in c.name.lower()]
            if not hits:
                print(f"error: no course matches --course {pat!r}", file=sys.stderr)
                return 2
            selected += hits
        courses = sorted(set(selected))

    plan = Plan()
    for course in courses:
        scan_course(course, ws_root, plan)

    if args.extra:
        for rel in args.extra:
            p = vault / rel
            if not p.exists():
                print(f"error: --extra path not found: {p}", file=sys.stderr)
                return 2
            course_name = Path(rel).parts[0]
            dst = ws_root / LEGACY_NAME / Path(rel)
            if p.is_dir():
                plan.add_legacy_dir(p, dst)
            else:
                plan.add_legacy_file(p, dst)

    links = rewrite_links(vault, apply=False)

    if not (plan.deliver or plan.workspace or plan.legacy_files
            or plan.legacy_dirs or plan.delete or links):
        print("nothing to migrate: all course folders already clean.")
        return 0

    pruned: list[Path] = []
    if args.apply:
        # 1) 目标目录
        for course in courses:
            (course / DELIVERY_NAME).mkdir(parents=True, exist_ok=True)
        for _src, _kind, dst in plan.workspace:
            dst.parent.mkdir(parents=True, exist_ok=True)
        for _src, dst in plan.legacy_files + plan.legacy_dirs:
            dst.parent.mkdir(parents=True, exist_ok=True)
        # 2) 删除
        for p in plan.delete:
            try:
                if p.is_dir():
                    shutil.rmtree(p)
                elif p.is_file():
                    p.unlink()
            except OSError as e:
                print(f"warn: delete failed {p}: {e}", file=sys.stderr)
        # 2.5) 去重跳过的源文件：标准副本已在/将到目标位，原地清掉
        for src, _dst in plan.dedup_skipped:
            try:
                if src.is_file():
                    src.unlink()
            except OSError as e:
                print(f"warn: dedup cleanup failed {src}: {e}", file=sys.stderr)
        # 3) 文件移动
        moves = [(s, d) for s, _k, d in plan.workspace] + plan.deliver + plan.legacy_files
        for src, dst in moves:
            try:
                shutil.move(str(src), str(dst))
            except OSError as e:
                print(f"warn: move failed {src}: {e}", file=sys.stderr)
        # 4) 目录归档
        for src, dst in plan.legacy_dirs:
            try:
                merge_move_dir(src, dst)
            except OSError as e:
                print(f"warn: legacy dir move failed {src}: {e}", file=sys.stderr)
        # 5) 空目录修剪
        for course in courses:
            pruned += prune_empty(course)
        # 6) 链接改写
        links = rewrite_links(vault, apply=True)

    report = build_report(plan, vault, ws_root, links, pruned, args.apply)
    print(report)
    if args.apply:
        ws_root.mkdir(parents=True, exist_ok=True)
        (ws_root / "_migration_report.md").write_text(report, encoding="utf-8")
        print(f"report saved: {ws_root / '_migration_report.md'}")
    else:
        print("dry run: nothing changed. pass --apply to execute.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
