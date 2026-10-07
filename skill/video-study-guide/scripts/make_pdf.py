#!/usr/bin/env python3
"""Print a finished lesson page to a colorful A4 PDF with headless Chromium.

Usage:
    python3 make_pdf.py /mnt/user-data/outputs/<slug>.html [--out <slug>.pdf] [--title "Short title"]

Adds assets/print.css (cover page, Contents page from the chapter nav, one chapter per
page, no split boxes/diagrams, wrapped code, light theme), opens all quiz answers, and
prints with page headers and "Page X of Y" footers.
"""
import argparse, os, subprocess, sys, html

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("page"); ap.add_argument("--out"); ap.add_argument("--title", default="")
    a = ap.parse_args()
    out = a.out or os.path.splitext(a.page)[0] + ".pdf"
    try:
        import playwright  # noqa
    except ImportError:
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "playwright", "--break-system-packages"])
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"])
    from playwright.sync_api import sync_playwright
    css = open(os.path.join(HERE, "..", "assets", "print.css")).read()
    style = "width:100%;font-size:7.5pt;color:#8a90a8;padding:0 14mm;font-family:Helvetica,Arial,sans-serif;display:flex;justify-content:space-between"
    header = f'<div style="{style}"><span>{html.escape(a.title)}</span><span></span></div>'
    footer = f'<div style="{style}"><span></span><span>Page <span class="pageNumber"></span> of <span class="totalPages"></span></span></div>'
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={"width": 900, "height": 1200})
        pg.goto("file://" + os.path.abspath(a.page), wait_until="networkidle"); pg.wait_for_timeout(1500)
        pg.evaluate("()=>{document.documentElement.setAttribute('data-theme','light');document.querySelectorAll('details').forEach(d=>d.open=true);}")
        pg.add_style_tag(content=css); pg.emulate_media(media="print"); pg.wait_for_timeout(800)
        pg.pdf(path=out, format="A4", print_background=True, display_header_footer=True,
               header_template=header, footer_template=footer,
               margin={"top": "16mm", "bottom": "18mm", "left": "14mm", "right": "14mm"})
        b.close()
    print(f"Wrote {out} ({os.path.getsize(out)/1e6:.1f} MB). Check pages with: pdftoppm -r 40 -png {out} /tmp/pp")


if __name__ == "__main__":
    main()
