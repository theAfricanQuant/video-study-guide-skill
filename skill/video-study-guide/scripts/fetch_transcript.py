#!/usr/bin/env python3
"""Fetch a YouTube video's title and transcript as clean plain text.

Usage:
    python3 fetch_transcript.py <youtube-url-or-id> [--out /tmp/transcript.txt]

Writes:
    <out>            cleaned transcript (one long paragraph, speaker changes marked with " | ")
    <out>.meta.json  {"id", "url", "title", "channel", "chars", "words"}

Strategy (first one that works wins):
    1. yt-dlp auto/manual English subtitles (VTT), with certificate checks off
       (sandboxes often sit behind a TLS-inspecting proxy).
    2. youtube-transcript-api (often blocked from cloud IPs, but worth a try).
If both fail, the script exits non-zero and tells you to ask the user to paste
or upload the transcript instead.
"""
import argparse
import glob
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.request
import ssl


def video_id(s: str) -> str:
    m = re.search(r"(?:v=|youtu\.be/|shorts/|embed/)([A-Za-z0-9_-]{11})", s)
    if m:
        return m.group(1)
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", s):
        return s
    sys.exit(f"Could not find a YouTube video id in: {s}")


def ensure(pkg: str, import_name: str | None = None):
    try:
        __import__(import_name or pkg)
    except ImportError:
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", pkg,
                        "--break-system-packages"], check=False)


def oembed(vid: str) -> dict:
    url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={vid}&format=json"
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    try:
        with urllib.request.urlopen(url, context=ctx, timeout=20) as r:
            d = json.load(r)
            return {"title": d.get("title", ""), "channel": d.get("author_name", "")}
    except Exception:
        return {"title": "", "channel": ""}


def clean_vtt(text: str) -> str:
    out, prev = [], ""
    for line in text.splitlines():
        if "-->" in line or line.startswith(("WEBVTT", "Kind:", "Language:")) or not line.strip():
            continue
        t = re.sub(r"<[^>]+>", "", line).strip()
        if t and t != prev:
            out.append(t)
            prev = t
    # auto-captions roll: each cue often repeats the previous one plus new words
    merged = []
    for t in out:
        if merged and t.startswith(merged[-1]):
            merged[-1] = t
        elif not merged or t not in merged[-1]:
            merged.append(t)
    s = " ".join(merged)
    s = (s.replace("&gt;&gt;", "|").replace("&nbsp;", " ").replace("&amp;", "&")
           .replace("&gt;", ">").replace("&lt;", "<").replace("&#39;", "'").replace("&quot;", '"'))
    return re.sub(r"\s+", " ", s).strip()


PLAYER_CLIENTS = [None, "web_embedded", "web_safari", "mweb", "tv", "android"]


def via_ytdlp(vid: str) -> str | None:
    """Try yt-dlp with several YouTube player clients.

    YouTube sometimes answers sandbox IPs with "Sign in to confirm you're not a bot"
    for the default client while another client (often web_embedded) still serves
    subtitles, so we cycle through them.
    """
    ensure("yt-dlp", "yt_dlp")
    ensure("curl_cffi")  # lets yt-dlp impersonate a browser; avoids many HTTP 429s
    # Requesting one track at a time ("en-orig" first) also avoids 429 Too Many Requests,
    # which YouTube often returns when several subtitle tracks are fetched back to back.
    for attempt, (client, langs) in enumerate(
            [(c, l) for c in PLAYER_CLIENTS for l in ("en-orig", "en", "en.*")]):
        tmp = tempfile.mkdtemp()
        cmd = [sys.executable, "-m", "yt_dlp", "--no-check-certificates", "--skip-download",
               "--ignore-no-formats-error", "--write-auto-subs", "--write-subs",
               "--sub-langs", langs, "--sub-format", "vtt", "--sleep-subtitles", "2",
               "-o", os.path.join(tmp, "v")]
        if client:
            cmd += ["--extractor-args", f"youtube:player_client={client}"]
        cmd.append(f"https://www.youtube.com/watch?v={vid}")
        r = subprocess.run(cmd, capture_output=True, text=True)
        files = glob.glob(os.path.join(tmp, "v*.vtt"))
        if files:
            files.sort(key=lambda f: len(f))
            text = clean_vtt(open(files[0], encoding="utf-8", errors="ignore").read())
            if len(text) > 200:
                print(f"[yt-dlp] subtitles via client={client or 'default'} langs={langs}", file=sys.stderr)
                return text
        if "429" in (r.stderr + r.stdout):
            time.sleep(15)  # back off before the next attempt
    return None


def via_api(vid: str) -> str | None:
    ensure("youtube-transcript-api", "youtube_transcript_api")
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        t = YouTubeTranscriptApi().fetch(vid)
        return re.sub(r"\s+", " ", " ".join(s.text for s in t)).strip()
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--out", default="/tmp/transcript.txt")
    a = ap.parse_args()
    vid = video_id(a.video)
    meta = {"id": vid, "url": f"https://www.youtube.com/watch?v={vid}", **oembed(vid)}
    text = via_ytdlp(vid) or via_api(vid)
    if not text:
        sys.exit("No transcript could be fetched. Ask the user to paste or upload the transcript.")
    open(a.out, "w", encoding="utf-8").write(text)
    meta.update(chars=len(text), words=len(text.split()))
    json.dump(meta, open(a.out + ".meta.json", "w"), indent=2)
    print(json.dumps(meta, indent=2))
    print(f"\nTranscript saved to {a.out}. Read it fully in ~40,000-character chunks before writing.")


if __name__ == "__main__":
    main()
