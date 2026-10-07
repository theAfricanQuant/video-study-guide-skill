#!/usr/bin/env python3
"""Assemble a study-guide page from the template plus body part files.

Usage:
    python3 assemble.py --title "..." --description "..." --accent "#E07A10" \
        --out /mnt/user-data/outputs/my-guide.html part1.html part2.html ...

Body parts are concatenated in the order given, between the template's <head>/<style>
(assets/template_head.html) and the scroll script (assets/template_foot.html).
Write the body in several part files so no single file is huge.

Accent: pass one hex colour. Soft/dark-mode variants are derived automatically
unless you pass --accent-soft / --accent-dark / --accent-soft-dark.
"""
import argparse, os, html, colorsys

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "..", "assets")


def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def rgb_to_hex(r, g, b):
    return "#%02X%02X%02X" % tuple(max(0, min(255, round(c * 255))) for c in (r, g, b))


def derive(accent):
    r, g, b = hex_to_rgb(accent)
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    soft = rgb_to_hex(*colorsys.hls_to_rgb(h, 0.92, min(s, 0.75)))
    dark = rgb_to_hex(*colorsys.hls_to_rgb(h, 0.68, min(1, s + 0.1)))
    soft_dark = rgb_to_hex(*colorsys.hls_to_rgb(h, 0.17, min(s, 0.45)))
    return soft, dark, soft_dark


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--title", required=True)
    ap.add_argument("--description", required=True)
    ap.add_argument("--accent", default="#D6336C")
    ap.add_argument("--accent-soft")
    ap.add_argument("--accent-dark")
    ap.add_argument("--accent-soft-dark")
    ap.add_argument("--out", required=True)
    ap.add_argument("parts", nargs="+")
    a = ap.parse_args()

    soft, dark, soft_dark = derive(a.accent)
    head = open(os.path.join(ASSETS, "template_head.html"), encoding="utf-8").read()
    for k, v in {
        "{{TITLE}}": html.escape(a.title),
        "{{DESCRIPTION}}": html.escape(a.description, quote=True),
        "{{ACCENT}}": a.accent,
        "{{ACCENT_SOFT}}": a.accent_soft or soft,
        "{{ACCENT_DARK}}": a.accent_dark or dark,
        "{{ACCENT_SOFT_DARK}}": a.accent_soft_dark or soft_dark,
    }.items():
        head = head.replace(k, v)
    body = "".join(open(p, encoding="utf-8").read() for p in a.parts)
    foot = open(os.path.join(ASSETS, "template_foot.html"), encoding="utf-8").read()
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    open(a.out, "w", encoding="utf-8").write(head + body + foot)
    print(f"Wrote {a.out} ({os.path.getsize(a.out):,} bytes)")


if __name__ == "__main__":
    main()
