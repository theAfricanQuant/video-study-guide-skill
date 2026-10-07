# video-study-guide-skill

An **agent skill** that turns learning materials (YouTube videos, PDFs, articles, slide decks and GitHub repos) into a long, beautiful, beginner-friendly **HTML lesson**, plus an optional **colorful PDF**.

Lessons are written in simple 12th-grade English, like a textbook chapter, and include:

- **Everyday Global South metaphors:** Nigerian first (danfo, okada, jollof, the POS agent), then wider Africa and Asia (boda boda, matatu, injera, ugali, matoke, banku, tuk-tuk), always naming both regional words.
- **Openly licensed photos**, found through Openverse and credited under each image.
- **Original SVG diagrams** that teach, with no logos or copyrighted characters.
- **Tested code** with genuine "real output" boxes, small benchmarks, and correction boxes when the source material has mistakes.
- **Short histories**, every story from the sources, quizzes, a step-by-step plan, a glossary and a References section.

It works with **Claude Code**, the **Claude Agent SDK**, **Claude.ai**, and any agent that can read a `SKILL.md` file or an `AGENTS.md` pointer (Codex, Cursor, Gemini CLI, OpenCode, and others).

---

## Quick start

Install straight from GitHub (works before it's on npm):

```bash
npx github:theAfricanQuant/video-study-guide-skill install
```

Or from npm:

```bash
# 1. Install the skill (default target: Claude Code, ~/.claude/skills/)
npx video-study-guide-skill install

# 2. Give the skill its own Python environment + Chromium (uses uv if you have it)
npx video-study-guide-skill setup

# 3. Check everything
npx video-study-guide-skill doctor
```

Then ask your agent:

> Make a beginner lesson from https://youtu.be/… and this PDF. Use Naija metaphors and make a PDF copy too.

## Install targets

| Target | Command | Where it goes | Use for |
|---|---|---|---|
| Claude Code, all projects (default) | `npx video-study-guide-skill install` | `~/.claude/skills/video-study-guide/` | Claude Code, Claude Agent SDK |
| Claude Code, this project only | `… install --target claude-project` | `./.claude/skills/video-study-guide/` | Sharing the skill with a team via the repo |
| Any agent that reads AGENTS.md | `… install --target agents` | `./skills/video-study-guide/` + a pointer block in `./AGENTS.md` | Codex, Cursor, Gemini CLI, OpenCode… |
| Any folder | `… install --dir <path>` | `<path>/video-study-guide/` | Harnesses with their own skills folder |
| Claude.ai | `npx video-study-guide-skill pack` | `dist/video-study-guide.skill` | Upload in Claude.ai settings |

Use the same `--target` or `--dir` with `setup`, `doctor`, `uninstall` and `where`.

If your tool reads `CLAUDE.md` or another instructions file instead of `AGENTS.md`, copy the pointer block from `AGENTS.md` into it.

## Commands

| Command | What it does |
|---|---|
| `install` | Copies the skill into the target (`--force` to overwrite, `--link` to symlink while developing) |
| `setup` | Creates `<skill>/.venv`, installs the Python packages from `requirements.txt`, and downloads Chromium. Add `--with-deps` on Linux for Chromium's system libraries (needs sudo), or `--no-browser` to skip Chromium. |
| `doctor` | Checks Python, packages, Chromium, curl, git, poppler, uv and zip |
| `uninstall` | Removes the skill (and the AGENTS.md pointer for `--target agents`) |
| `where` | Prints the install path |
| `pack` | Builds `dist/video-study-guide.skill` for Claude.ai |

## Requirements

- **Node.js 18+** (for the installer only; it has no npm dependencies)
- **Python 3.10+.** `setup` installs: `yt-dlp`, `curl_cffi`, `youtube-transcript-api`, `pillow`, `playwright`, `pypdf`
- **Command-line tools:** `curl` and `git`; `pdftoppm` from poppler (recommended, for PDF page previews); `uv` (recommended)

Linux / WSL:
```bash
sudo apt install curl git poppler-utils zip
curl -LsSf https://astral.sh/uv/install.sh | sh
```
macOS:
```bash
brew install poppler uv
```

## Bot walls: cookies for YouTube

`Sign in to confirm you're not a bot` on a cloud/CI box is not a broken install — YouTube treats an anonymous request from a datacenter IP like an expired session. Give the script a jar exported from a browser that is logged in to youtube.com:

```bash
# 1. export cookies.txt (a "Get cookies.txt LOCALLY"-style extension, while on youtube.com)
# 2. pass it in
python3 "<skill>/scripts/fetch_transcript.py" "<url>" --cookies ~/cookies.txt

# or let yt-dlp read a local browser profile directly
python3 "<skill>/scripts/fetch_transcript.py" "<url>" --cookies-from-browser chrome

# still walled on a locked-down network: try another player client
python3 "<skill>/scripts/fetch_transcript.py" "<url>" --cookies ~/cookies.txt \
  --player-client tv --player-client mweb
```

Env fallbacks for harnesses that cannot pass flags: `YT_DLP_COOKIES`, `YT_DLP_COOKIES_FROM_BROWSER`, `YT_DLP_PLAYER_CLIENT` (comma-separated). The same jar is loaded into the `youtube-transcript-api` fallback's HTTP session. The script warns when a jar contains no login cookies (`SID`, `__Secure-1PSID`, `SAPISID`…) — an anonymous export cannot pass the wall. Where cookies are valid and it still fails, a PO-token provider may be needed: `uv pip install bgutil-ytdlp-pot-provider` plus the bgutil server.

## What's inside

```
skill/video-study-guide/
├── SKILL.md                 # the workflow and writing rules the agent follows
├── requirements.txt         # Python packages for the scripts
├── scripts/
│   ├── fetch_transcript.py  # YouTube → transcript (+ title, channel, URL)
│   ├── find_photos.py       # Openverse search → contact sheets → embedded, credited photos
│   ├── assemble.py          # template + body parts → one HTML file
│   ├── check_page.py        # mobile-overflow check + screenshots
│   └── make_pdf.py          # colorful A4 PDF via headless Chromium
├── assets/
│   ├── template_head.html   # design system: light/dark, code, outputs, warnings, photos
│   ├── template_foot.html   # lightweight scroll script
│   └── print.css            # cover, contents, one chapter per page
└── references/
    ├── components.md        # every HTML building block + SVG diagram cookbook
    └── metaphors.md         # metaphor rules, concept→metaphor bank, photo search terms
```

## Where the agent saves things

By default the skill tells the agent to write finished lessons to `./lesson-output/` and scratch files to `./lesson-work/`. In the Claude.ai sandbox it uses `/mnt/user-data/outputs/`. You can ask for a different folder in your prompt.

## Responsible use

- Lessons **paraphrase** video and article content and quote only short, attributed passages. Code from materials you supply is quoted with attribution.
- Photos must be **openly licensed** and credited. News or magazine photos are linked, not embedded.
- Diagrams are **original**. No logos, brand marks or copyrighted characters are drawn.
- YouTube sometimes rate-limits transcript downloads. The script retries several ways; if it still fails, paste the transcript.

## Developing

```bash
git clone https://github.com/theAfricanQuant/video-study-guide-skill
cd video-study-guide-skill
node bin/cli.js install --link --force   # edits in skill/ take effect immediately
npm test                                 # installs into ./.test-install and runs doctor
npm run build:skill                      # dist/video-study-guide.skill
```

Publish to npm with `npm publish` after updating `version` in `package.json`.

## License

MIT
