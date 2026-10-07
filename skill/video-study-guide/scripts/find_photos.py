#!/usr/bin/env python3
"""Find openly licensed photos for analogies, review them, and embed the picks.

Two steps:

1) SEARCH: build contact sheets you can look at with the image viewer
   python3 find_photos.py search --q danfo="danfo bus lagos|lagos danfo" --q injera="injera|injera platter" \
       --out /tmp/photos
   -> /tmp/photos/candidates.json and /tmp/photos/sheet_<key>.jpg (numbered thumbnails)

2) PICK: download chosen candidates, crop to 16:9, compress, and write data-URI + credits JSON
   python3 find_photos.py pick --out /tmp/photos danfo=0 injera=2
   -> /tmp/photos/picked.json  {key: {data, title, creator, license, link}}

Then build the HTML with `photo_html(key, alt)` from this file (or copy the snippet in
references/components.md). Photos come from Openverse (openly licensed: CC0, CC BY,
CC BY-SA, public domain), restricted to licenses that allow commercial reuse.
Always keep the credit line under each photo.
"""
import argparse, base64, html, io, json, os, subprocess, sys, urllib.parse

FIELDS = ["title", "creator", "license", "license_version", "url", "thumbnail",
          "foreign_landing_url", "width", "height", "source"]


def curl_json(url):
    r = subprocess.run(["curl", "-s", "-m", "30", url], capture_output=True, text=True)
    try:
        return json.loads(r.stdout)
    except Exception:
        return {}


def ensure_pil():
    try:
        import PIL  # noqa
    except ImportError:
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "pillow", "--break-system-packages"])


def search(args):
    ensure_pil()
    from PIL import Image, ImageDraw
    os.makedirs(os.path.join(args.out, "raw"), exist_ok=True)
    cpath = os.path.join(args.out, "candidates.json")
    cands = json.load(open(cpath)) if os.path.exists(cpath) else {}
    for spec in args.q:
        key, qs = spec.split("=", 1)
        found = []
        for q in qs.split("|"):
            url = "https://api.openverse.org/v1/images/?" + urllib.parse.urlencode(
                {"q": q.strip(), "page_size": 10, "license_type": "commercial"})
            for x in curl_json(url).get("results", []):
                w, h = x.get("width") or 0, x.get("height") or 0
                if w and h and w >= h * 1.05 and x["url"] not in [f["url"] for f in found]:
                    found.append({k: x.get(k) for k in FIELDS})
            if len(found) >= 6:
                break
        cands[key] = found[:6]
        sheet = Image.new("RGB", (930, 500), "white"); d = ImageDraw.Draw(sheet)
        d.rectangle([0, 0, 930, 24], fill="black"); d.text((8, 6), key.upper(), fill="yellow")
        for i, x in enumerate(cands[key]):
            fn = os.path.join(args.out, "raw", f"{key}_{i}.jpg")
            subprocess.run(["curl", "-sL", "-m", "25", "-A", "Mozilla/5.0", "-o", fn, x.get("thumbnail") or x["url"]])
            try:
                im = Image.open(fn).convert("RGB"); im.thumbnail((300, 210))
            except Exception:
                continue
            X, Y = (i % 3) * 310, (i // 3) * 245 + 28
            sheet.paste(im, (X, Y)); d.text((X + 4, Y + 215), f"{i}: {(x['title'] or '')[:36]}", fill="black")
        sp = os.path.join(args.out, f"sheet_{key}.jpg"); sheet.save(sp, quality=78)
        print(f"{key}: {len(cands[key])} candidates -> {sp}")
    json.dump(cands, open(cpath, "w"), indent=1)


def pick(args):
    ensure_pil()
    from PIL import Image
    cands = json.load(open(os.path.join(args.out, "candidates.json")))
    ppath = os.path.join(args.out, "picked.json")
    picked = json.load(open(ppath)) if os.path.exists(ppath) else {}
    os.makedirs(os.path.join(args.out, "full"), exist_ok=True)
    for spec in args.picks:
        key, idx = spec.split("="); x = cands[key][int(idx)]
        fn = os.path.join(args.out, "full", f"{key}.jpg")
        subprocess.run(["curl", "-sL", "-m", "40", "-A", "Mozilla/5.0", "-o", fn, x["url"]])
        try:
            im = Image.open(fn).convert("RGB")
        except Exception:
            im = Image.open(os.path.join(args.out, "raw", f"{key}_{idx}.jpg")).convert("RGB")
        w, h = im.size
        if w > 720:
            im = im.resize((720, int(h * 720 / w))); w, h = im.size
        nh = int(w * 9 / 16)
        if h > nh:
            top = (h - nh) // 2; im = im.crop((0, top, w, top + nh))
        buf = io.BytesIO(); im.save(buf, "JPEG", quality=68, optimize=True, progressive=True)
        lic, ver = x["license"], x.get("license_version") or ""
        name = "CC0" if lic == "cc0" else "Public domain" if lic == "pdm" else f"CC {lic.upper()} {ver}".strip()
        picked[key] = {"data": "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode(),
                       "title": x["title"], "creator": x["creator"], "license": name,
                       "link": x["foreign_landing_url"]}
        print(f"{key}: {x['title']} | {x['creator']} | {name} | {len(buf.getvalue())//1024} KB")
    json.dump(picked, open(ppath, "w"))


def photo_html(key, alt, picked_path="/tmp/photos/picked.json"):
    """Return the <figure class="aph"> snippet for an analogy box."""
    m = json.load(open(picked_path))[key]
    return (f'<figure class="aph"><img src="{m["data"]}" alt="{html.escape(alt)}">'
            f'<figcaption>Photo: <a href="{m["link"]}" target="_blank" rel="noopener">'
            f'{html.escape((m["title"] or "")[:60])}</a> by {html.escape(m["creator"] or "unknown")}, '
            f'{m["license"]}</figcaption></figure>')


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("search"); s.add_argument("--q", action="append", required=True); s.add_argument("--out", default="/tmp/photos")
    p = sub.add_parser("pick"); p.add_argument("picks", nargs="+"); p.add_argument("--out", default="/tmp/photos")
    a = ap.parse_args()
    search(a) if a.cmd == "search" else pick(a)
