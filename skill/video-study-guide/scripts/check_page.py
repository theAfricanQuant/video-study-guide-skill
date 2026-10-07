#!/usr/bin/env python3
"""QA a finished study-guide page: horizontal overflow on mobile, plus screenshots.

Usage:
    python3 check_page.py /mnt/user-data/outputs/my-guide.html [--shots /tmp/guide-shots]

Prints any elements that overflow a 390px-wide viewport (should print nothing),
then saves desktop and mobile screenshots cut into viewable slices
(desk_0.png, desk_1.png, ..., mob_0.png, ...). View a few slices to eyeball
diagrams for clipped labels or overlapping text.
"""
import argparse, os, subprocess, sys


def ensure():
    try:
        import playwright  # noqa
    except ImportError:
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "playwright",
                        "--break-system-packages"], check=False)
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("page")
    ap.add_argument("--shots", default="/tmp/guide-shots")
    a = ap.parse_args()
    ensure()
    from playwright.sync_api import sync_playwright
    from PIL import Image
    os.makedirs(a.shots, exist_ok=True)
    url = "file://" + os.path.abspath(a.page)
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 390, "height": 900})
        pg.goto(url); pg.wait_for_timeout(800)
        over = pg.evaluate("""()=>{const W=document.documentElement.clientWidth;const o=[];
          document.querySelectorAll('body *').forEach(e=>{const r=e.getBoundingClientRect();
          if(r.right>W+1&&!e.closest('nav.toc'))o.push(e.tagName+' '+(e.id||'')+' right='+Math.round(r.right))});return o.slice(0,20)}""")
        print("Mobile overflow:", over if over else "none ✓")
        for w, name in [(1280, "desk"), (390, "mob")]:
            pg = b.new_page(viewport={"width": w, "height": 900})
            pg.goto(url); pg.wait_for_timeout(1200)
            path = os.path.join(a.shots, f"{name}.png")
            pg.screenshot(path=path, full_page=True)
            im = Image.open(path); W, H = im.size; step = 3200
            for i, y in enumerate(range(0, H, step)):
                c = im.crop((0, y, W, min(H, y + step)))
                if name == "desk":
                    c = c.resize((W // 2, c.size[1] // 2))
                c.save(os.path.join(a.shots, f"{name}_{i}.png"))
            print(f"{name}: {W}x{H}px → {i + 1} slices in {a.shots}")
        b.close()


if __name__ == "__main__":
    main()
