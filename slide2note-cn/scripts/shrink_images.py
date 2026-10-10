#!/usr/bin/env python3
"""
shrink_images.py

Batch-shrink PNG figures in place to keep the final PDF under the
5 MB hard cap (Obsidian sync limit).

Two levers, applied to every *.png under the given directory tree:
  1. 256-color palette quantization + PNG optimize
     (visually lossless for white-background teaching figures)
  2. optional downsampling so the longest edge <= --downscale px
     (LANCZOS, applied before quantization)

Files whose re-encoding would not be smaller are left untouched.

Example:
    python3 shrink_images.py ../images                   # quantize only
    python3 shrink_images.py ../images --downscale 2000
    python3 shrink_images.py ../images --dry-run         # report only
"""

from __future__ import annotations

import argparse
import io
from pathlib import Path
import sys

from PIL import Image


def flatten_on_white(img: Image.Image) -> Image.Image:
    """Composite any transparency onto white and return an RGB image."""
    if img.mode == "RGB":
        return img
    rgba = img.convert("RGBA")
    bg = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
    return Image.alpha_composite(bg, rgba).convert("RGB")


def shrink(img: Image.Image, downscale: int | None) -> Image.Image:
    if downscale:
        longest = max(img.size)
        if longest > downscale:
            ratio = downscale / longest
            size = (
                max(1, round(img.width * ratio)),
                max(1, round(img.height * ratio)),
            )
            img = img.resize(size, Image.LANCZOS)
    return flatten_on_white(img).quantize(
        colors=256, method=Image.Quantize.FASTOCTREE
    )


def encode_png(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Batch-shrink PNG figures for the PDF size budget."
    )
    parser.add_argument("images_dir", type=Path,
                        help="directory tree containing the PNG figures")
    parser.add_argument("--downscale", type=int, default=None,
                        help="downsample so the longest edge <= N px before quantizing")
    parser.add_argument("--dry-run", action="store_true",
                        help="report savings without writing files")
    args = parser.parse_args()

    if not args.images_dir.is_dir():
        print(f"error: not a directory: {args.images_dir}", file=sys.stderr)
        return 2

    pngs = sorted(args.images_dir.rglob("*.png"))
    if not pngs:
        print(f"error: no .png found under {args.images_dir}", file=sys.stderr)
        return 2

    total_before = 0
    total_after = 0

    for path in pngs:
        rel = path.relative_to(args.images_dir)
        before = path.stat().st_size

        with Image.open(path) as im:
            im.load()
            encoded = encode_png(shrink(im, args.downscale))

        if len(encoded) >= before:
            print(f"skip:    {rel}  {before} bytes (re-encode not smaller)")
            total_before += before
            total_after += before
            continue

        if not args.dry_run:
            path.write_bytes(encoded)

        after = len(encoded)
        verb = "would shrink" if args.dry_run else "shrink:   "
        print(f"{verb}  {rel}  {before} -> {after} bytes "
              f"({(1 - after / before) * 100:.1f}% saved)")
        total_before += before
        total_after += after

    print(f"total: {len(pngs)} files, "
          f"{total_before / 1048576:.2f} MB -> {total_after / 1048576:.2f} MB "
          f"({(1 - total_after / total_before) * 100:.1f}% saved)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
