#!/usr/bin/env python3
"""Fetch a YouTube video's title and transcript as clean plain text.

Usage:
    python3 fetch_transcript.py <youtube-url-or-id> [--out /tmp/transcript.txt]
    python3 fetch_transcript.py <url> --cookies ~/cookies.txt
    python3 fetch_transcript.py <url> --cookies-from-browser chrome
    python3 fetch_transcript.py <url> --player-client tv --player-client mweb

Writes:
    <out>            cleaned transcript (one long paragraph, speaker changes marked with " | ")
    <out>.meta.json  {"id", "url", "title", "channel", "chars", "words"}

Strategy (first one that works wins):
    1. yt-dlp auto/manual English subtitles (VTT), with certificate checks off
       (sandboxes often sit behind a TLS-inspecting proxy).
    2. youtube-transcript-api (often blocked from cloud IPs, but worth a try).
If both fail, the script exits non-zero and tells you to ask the user to paste
or upload the transcript instead.

Bot walls ("Sign in to confirm you're not a bot" / LOGIN_REQUIRED) are a cookie
problem first and a player-client problem second: YouTube treats an anonymous
request from a cloud IP exactly like an expired session. Pass a Netscape
`cookies.txt` exported from a browser that is logged in to youtube.com, either
as `--cookies <file>` or by letting yt-dlp read the browser profile directly
with `--cookies-from-browser <chrome|firefox|edge|brave|...>`. The jar is also
loaded into the youtube-transcript-api fallback's HTTP session. Environment
fallbacks: YT_DLP_COOKIES, YT_DLP_COOKIES_FROM_BROWSER, YT_DLP_PLAYER_CLIENT
(comma-separated). Some networks also need a PO-token provider (bgutil) on top
of cookies; see the `youtube-download-access` skill.
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


# Filled in by via_ytdlp so main() can explain *why* everything failed.
DIAG = {"walled": False, "cookies_used": False, "attempts": 0}


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
LANGS = ("en-orig", "en", "en.*")


def cookies_from_env() -> str | None:
    return os.environ.get("YT_DLP_COOKIES") or None


def browser_from_env() -> str | None:
    return os.environ.get("YT_DLP_COOKIES_FROM_BROWSER") or None


def clients_from_env() -> list[str]:
    return [c.strip() for c in os.environ.get("YT_DLP_PLAYER_CLIENT", "").split(",") if c.strip()]


def cookie_names(jar_path: str) -> list[str]:
    """Cookie names in a Netscape cookies.txt jar (names only — never values)."""
    names = []
    try:
        with open(jar_path, encoding="utf-8", errors="ignore") as fh:
            for line in fh:
                if line.startswith("#") or not line.strip():
                    continue
                parts = line.rstrip("\n").split("\t")
                if len(parts) >= 7:
                    names.append(parts[5])
    except OSError:
        pass
    return names


AUTH_COOKIES = ("SID", "__Secure-1PSID", "__Secure-3PSID", "HSID", "SSID",
                "APISID", "SAPISID", "LOGIN_INFO")


def warn_if_anonymous(jar_path: str) -> None:
    """A jar with no login cookies is an anonymous export: it cannot pass a bot
    wall. Warn loudly rather than failing later with a misleading message."""
    names = set(cookie_names(jar_path))
    if names and not (names & set(AUTH_COOKIES)):
        print(f"[cookies] WARNING: {jar_path} carries no login cookies "
              f"(no SID / __Secure-1PSID / SAPISID …) — export it while logged in "
              f"to youtube.com, or YouTube keeps answering with a bot wall.",
              file=sys.stderr)


def netscape_session(jar_path: str):
    """requests.Session carrying the cookies from a Netscape cookies.txt jar."""
    import requests
    s = requests.Session()
    with open(jar_path, encoding="utf-8", errors="ignore") as fh:
        for line in fh:
            if line.startswith("#") or not line.strip():
                continue
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 7:
                continue
            domain, _flag, path, _secure, _expires, name, value = parts[:7]
            try:
                s.cookies.set(name, value, domain=domain.lstrip("."), path=path or "/")
            except Exception:
                continue
    return s


def via_ytdlp(vid: str, cookies: str | None = None, browser: str | None = None,
              clients: list[str] | None = None) -> str | None:
    """Try yt-dlp with several YouTube player clients.

    YouTube sometimes answers sandbox IPs with "Sign in to confirm you're not a bot"
    for the default client while another client (often web_embedded) still serves
    subtitles, so we cycle through them. Cookies ride along on every attempt: the
    wall is a cookie problem first, a client problem second.
    """
    ensure("yt-dlp", "yt_dlp")
    ensure("curl_cffi")  # lets yt-dlp impersonate a browser; avoids many HTTP 429s
    cookie_args: list[str] = []
    if cookies:
        cookie_args += ["--cookies", cookies]
    if browser:
        cookie_args += ["--cookies-from-browser", browser]
    DIAG["cookies_used"] = bool(cookie_args)
    # Requesting one track at a time ("en-orig" first) also avoids 429 Too Many Requests,
    # which YouTube often returns when several subtitle tracks are fetched back to back.
    for client, langs in [(c, l) for c in (clients or PLAYER_CLIENTS) for l in LANGS]:
        DIAG["attempts"] += 1
        tmp = tempfile.mkdtemp()
        cmd = [sys.executable, "-m", "yt_dlp", "--no-check-certificates", *cookie_args,
               "--skip-download", "--ignore-no-formats-error", "--write-auto-subs",
               "--write-subs", "--sub-langs", langs, "--sub-format", "vtt",
               "--sleep-subtitles", "2", "-o", os.path.join(tmp, "v")]
        if client:
            cmd += ["--extractor-args", f"youtube:player_client={client}"]
        cmd.append(f"https://www.youtube.com/watch?v={vid}")
        r = subprocess.run(cmd, capture_output=True, text=True)
        files = glob.glob(os.path.join(tmp, "v*.vtt"))
        if files:
            files.sort(key=lambda f: len(f))
            text = clean_vtt(open(files[0], encoding="utf-8", errors="ignore").read())
            if len(text) > 200:
                print(f"[yt-dlp] subtitles via client={client or 'default'} langs={langs}",
                      file=sys.stderr)
                return text
        blob = r.stderr + r.stdout
        if "Sign in to confirm" in blob or "LOGIN_REQUIRED" in blob or "not a bot" in blob:
            DIAG["walled"] = True
            break  # every client hits the same wall until the cookies change
        if "429" in blob:
            time.sleep(15)  # back off before the next attempt
    return None


def via_api(vid: str, cookies: str | None = None) -> str | None:
    ensure("youtube-transcript-api", "youtube_transcript_api")
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        http_client = None
        if cookies:
            try:
                http_client = netscape_session(cookies)
            except Exception:
                http_client = None
        api = YouTubeTranscriptApi(http_client=http_client) if http_client else YouTubeTranscriptApi()
        t = api.fetch(vid)
        return re.sub(r"\s+", " ", " ".join(s.text for s in t)).strip()
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser(
        description="Fetch a YouTube transcript (cookie- and player-client-aware).")
    ap.add_argument("video")
    ap.add_argument("--out", default="/tmp/transcript.txt")
    ap.add_argument("--cookies", default=None,
                    help="Netscape cookies.txt exported from a browser logged in to "
                         "youtube.com; needed to pass a bot wall (env: YT_DLP_COOKIES)")
    ap.add_argument("--cookies-from-browser", default=None, metavar="BROWSER",
                    help="let yt-dlp read cookies from a local browser profile, e.g. "
                         "chrome, firefox, edge, brave (env: YT_DLP_COOKIES_FROM_BROWSER)")
    ap.add_argument("--player-client", action="append", default=None, metavar="CLIENT",
                    help="YouTube player client to try, repeatable and ordered, e.g. "
                         "--player-client tv --player-client mweb (env: "
                         "YT_DLP_PLAYER_CLIENT, comma-separated). Default: "
                         + ", ".join(c or "default" for c in PLAYER_CLIENTS))
    a = ap.parse_args()

    cookies = a.cookies or cookies_from_env()
    browser = a.cookies_from_browser or browser_from_env()
    clients = a.player_client or clients_from_env() or None

    if cookies:
        if not os.path.exists(cookies):
            sys.exit(f"Cookie file not found: {cookies}")
        print(f"[cookies] using {cookies} ({len(cookie_names(cookies))} cookies)", file=sys.stderr)
        warn_if_anonymous(cookies)
    if browser:
        print(f"[cookies] reading cookies from browser profile: {browser}", file=sys.stderr)

    vid = video_id(a.video)
    meta = {"id": vid, "url": f"https://www.youtube.com/watch?v={vid}", **oembed(vid)}
    text = via_ytdlp(vid, cookies, browser, clients) or via_api(vid, cookies)
    if not text:
        msg = ["No transcript could be fetched."]
        if DIAG["walled"]:
            msg.append('YouTube answered with a bot wall ("Sign in to confirm you\'re not a bot").')
            if not DIAG["cookies_used"]:
                msg.append("Fix: export cookies.txt from a browser logged in to youtube.com and "
                           "re-run with --cookies <file> (or --cookies-from-browser chrome). "
                           "A PO-token provider (bgutil) may also be needed — see the "
                           "youtube-download-access skill.")
            else:
                msg.append("Cookies were sent but rejected: export a fresh jar while logged in to "
                           "youtube.com, and check that a PO-token provider (bgutil) is running.")
        msg.append("Otherwise ask the user to paste or upload the transcript.")
        sys.exit(" ".join(msg))
    open(a.out, "w", encoding="utf-8").write(text)
    meta.update(chars=len(text), words=len(text.split()))
    json.dump(meta, open(a.out + ".meta.json", "w"), indent=2)
    print(json.dumps(meta, indent=2))
    print(f"\nTranscript saved to {a.out}. Read it fully in ~40,000-character chunks before writing.")


if __name__ == "__main__":
    main()
