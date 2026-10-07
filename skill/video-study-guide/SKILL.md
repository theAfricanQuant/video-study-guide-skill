---
name: video-study-guide
description: Turn learning materials (YouTube videos, PDFs, articles, slide decks, GitHub repos, transcripts) into a long, beautiful, beginner-friendly HTML lesson, with an optional colorful PDF copy. Lessons use simple 12th-grade English, Nigerian and wider African / Global South metaphors (okada / boda boda, danfo / matatu, keke / tuk-tuk, jollof, injera, ugali), openly licensed photos, original SVG diagrams, tested code with real outputs, short histories, every story from the sources, a step-by-step plan, a glossary and a References section. Use this skill whenever the user shares videos, PDFs, links or repos and asks to "study this", "break it down", "explain this simply", "make a lesson / study guide / textbook chapter", "turn this into an HTML page or PDF", "do the same as before", or uploads earlier guides and asks for more like them.
---

# Materials → Lesson (HTML + optional PDF)

Turn whatever the user provides into one self-contained HTML lesson that a complete beginner reads start to finish, then optionally print it to a colorful PDF. Write it like a good textbook chapter or blog post meant for students, not a reply to the user.

## Paths and environment (read first)

- **Skill directory (`$SKILL_DIR`)**: the folder containing this `SKILL.md`. All scripts are in `$SKILL_DIR/scripts/`. Run them from anywhere with the full path, e.g. `python3 "$SKILL_DIR/scripts/assemble.py" …` (or `uv run --no-project python …`).
- **Output folder (`$OUTPUT_DIR`)**: where finished `.html` and `.pdf` files go. Default: `./lesson-output/` in the current project. In the Claude.ai sandbox use `/mnt/user-data/outputs/`.
- **Work folder (`$WORK_DIR`)**: scratch space for body parts, transcripts and photos. Default: `./lesson-work/`. In the Claude.ai sandbox use `/home/claude/` and `/tmp/`.
- **Delivery**: if an Artifact/publish tool exists (Claude.ai), publish the HTML; else if `present_files` exists, present it; otherwise just save it to `$OUTPUT_DIR` and tell the user the path and to open it in a browser.
- **Python to use**: if `$SKILL_DIR/.venv/bin/python` (Windows: `$SKILL_DIR\.venv\Scripts\python.exe`) exists, run every script with it instead of `python3`; it has all dependencies installed (created by `npx video-study-guide-skill setup`).
- **Dependencies**: Python 3.10+, `yt-dlp`, `pillow`, `playwright` (+ Chromium), `curl`, `git`, and `pdftoppm` (poppler). If something is missing, run `npx video-study-guide-skill doctor` (when installed via npm) or install it before starting.

## Inputs you may get (often several at once)

| Material | How to get the content |
|---|---|
| YouTube link or ID | `scripts/fetch_transcript.py` (below). If it fails, ask the user to paste the transcript. |
| PDF (article, paper, slides) | If its text is already in context, use it. Otherwise read the `pdf-reading` (or `file-reading`) skill and extract it from the uploads folder (Claude.ai: `/mnt/user-data/uploads/`). |
| GitHub repo | `git clone --depth 1 <url> "$WORK_DIR/repo"`, then read the README, docs and main code files. |
| Web article URL | `curl -sL -A "Mozilla/5.0" <url>` and strip tags; if blocked, ask for a PDF or paste. |
| Earlier guide (HTML) to "do the same" with | Pull its source links (`youtube.com/watch`, `youtu.be`, `github.com`) from the file, re-fetch the materials, and rebuild from scratch in this format. |

When several materials are given, make **one combined lesson** that flows from basics to advanced, unless the user asks for separate guides.

## Workflow

### 1. Gather and read everything
```bash
python3 "$SKILL_DIR/scripts/fetch_transcript.py" "<url>" --out "$WORK_DIR/<slug>.txt"
```
The transcript script also writes `<out>.meta.json` with the exact title, channel and URL; use them in the hero buttons and References. Read every source completely (long transcripts in ~40,000-character chunks). Keep a running outline:
- every concept, framework, number and piece of advice
- **every story and anecdote** (who, what happened, the lesson)
- all code and commands in the materials
- jargon to explain
- names auto-captions probably misspelled (correct them when confident)
- claims or code that look wrong (you'll test them in step 3)

### 2. Plan the lesson
Group 10–17 chapters into **Parts** (Part I, II, III… with `.part` dividers), from foundations to advanced. Good shape for technical topics:
1. **The big picture:** what the thing is, the basic vocabulary (what a table/row/column is, and how to picture it), a short **history** of the ideas and tools (dated timeline diagram), and comparisons with what learners already know. If a beginner would ask "why not just use X?", answer it directly with a fair comparison and a real test.
2. **Hands-on basics**, following the sources.
3. **Deeper material and related formats/tools.**
4. **Advanced or AI material**, ending with a code walkthrough when there's a repo.
5. **Step-by-step plan** (`id="plan"`), **Glossary** (`id="glossary"`), **References** (`id="references"`).

Aim for 15–25 original diagrams, at least one analogy per chapter, story cards for every anecdote, and 3–6 quizzes.

### 3. Test everything you can (this is what makes the lesson trustworthy)
Run all code from the materials, and any code you add, in the sandbox (install missing Python packages with `uv pip install …` or `pip install …`). Download the sample datasets the sources use. Then:
- Show genuine results in `pre.out` "real output" boxes. Never invent outputs.
- Where it helps, run small **benchmarks** (same data, two tools; time and peak memory in fresh processes) and chart them, saying they're from the test machine.
- When the materials contain a bug, an impossible value or an outdated detail, explain it in a `.warn` box with the tested fix.
- If something can't run (no API key, paid service), say so and, if useful, rehearse with the real helper code plus a clearly labeled scripted stand-in.

### 4. Find photos for the analogies
Read `references/metaphors.md`. Then:
```bash
python3 "$SKILL_DIR/scripts/find_photos.py" search --out $WORK_DIR/photos \
  --q danfo="danfo bus lagos|lagos danfo" --q injera="injera|injera platter"
# view $WORK_DIR/photos/sheet_<key>.jpg with the image viewer, choose the best index for each key
python3 "$SKILL_DIR/scripts/find_photos.py" pick --out $WORK_DIR/photos danfo=0 injera=0
```
`pick` writes `$WORK_DIR/photos/picked.json` (compressed data URIs plus credits). Use `photo_html(key, alt)` from the script, or the snippet in `references/components.md`, to place each photo inside its analogy box **with its credit line**. Aim for 10–20 photos; skip any analogy where no good photo exists rather than using a poor match.

### 5. Write the body in parts
Read `references/components.md` for every snippet. Write 6–10 part files (`$WORK_DIR/<slug>/02.html …`) so no single write is huge. Required order: header (hero + chapter nav including Glossary and References) → intro → Parts and chapters → plan → glossary → references → footer.

### 6. Assemble, check, publish
```bash
python3 "$SKILL_DIR/scripts/assemble.py" --title "…" --description "…" --accent "#C27C0E" \
  --out $OUTPUT_DIR/<slug>.html $WORK_DIR/<slug>/02.html …
python3 "$SKILL_DIR/scripts/check_page.py" $OUTPUT_DIR/<slug>.html
```
"Mobile overflow" should list nothing except `SPAN`s inside scrolling code blocks; fix anything else (usually `min-width:0` or a long unbroken string). View a few screenshot slices and fix clipped diagram labels. Publish with the Artifact tool if available (update the same artifact URL when revising), otherwise `present_files`.

### 7. PDF copy (when asked, or offer it in one line)
```bash
python3 "$SKILL_DIR/scripts/make_pdf.py" $OUTPUT_DIR/<slug>.html --title "Short running title"
pdftoppm -r 40 -png $OUTPUT_DIR/<slug>.pdf $WORK_DIR/pp   # then view a few pages
```
Headless Chromium prints the same page with `assets/print.css`: a cover, a Contents page, one chapter per page, unsplit boxes and diagrams, wrapped code, open quiz answers, and "Page X of Y" footers. If a diagram is too large on paper, adjust `print.css` and re-run. Deliver with `present_files`.

## Writing rules

**Voice: a textbook for students, not a reply to the user.**
- Never write "you shared", "you asked", "your question", "for you". Write "A common first question is…", "We tested…", "This guide…".
- First person plural ("we built the same table…") for tests; otherwise neutral.
- Mention the source authors by name only in the intro (one sentence) and the References. Elsewhere: "the article", "the first video", "the repo", "the creator".
- Simple English for a curious 12th grader: short sentences, active voice. Define every technical term the first time (inline `term` tooltip) and again in the glossary, and help readers *picture* it (what a table looks like, what a row represents).

**Metaphors** come from Nigeria first and the wider Global South (see `references/metaphors.md`). Name both regional terms when they differ (okada / boda boda, danfo / matatu, keke / bajaj / tuk-tuk). No German, American or European metaphors unless the user asks.

**Your own words, always.** Paraphrase video and article content. Short attributed quotes only. Never paste transcript passages, lyrics, book excerpts, or long periodical passages. Code and short excerpts from documents the user supplied may be quoted with attribution.

**Images:**
- Diagrams are original SVG drawn from simple shapes. Never draw logos, brand marks, film/TV/game/comic characters, movie posters or other existing artwork; name them in text instead.
- Photos must be openly licensed (CC0, CC BY, CC BY-SA, public domain) and credited under the image with title, creator, license and link. `find_photos.py` handles this.
- Do not embed news-outlet or magazine photos. Link to the article instead. Official government pages released under open licences (e.g. GOV.UK's Open Government Licence) may be clipped with the licence noted, but crop out crests and logos.

**Accuracy:**
- Attribute claims ("the video says…"). Present money, follower and benchmark figures from sources as their claims; present your own measurements as from the test machine.
- Flag simplifications (e.g. "this left/right-brain split is a simplification") and correct known errors gently.
- Correct caption-garbled names when confident, and mention it in the reply.
- Python commands shown to readers use `uv` (`uv add …`, `uv run …`).

**History** belongs in the foundations: when a topic has a past (SQL, spreadsheets, file formats, a framework), add a dated timeline with original diagrams and cite primary sources in References.

**Every lesson ends with:**
- **"Your step-by-step plan to do the same":** 10–14 ordered steps with `when` tags. State that it draws the sources together rather than quoting one of them.
- **Glossary:** 25–60 terms.
- **References:** grouped as History and concepts, Articles, Videos, Code, Software and documentation, News, Datasets, Photographs. Include year, title, venue and link where known.

## Bundled files

- `scripts/fetch_transcript.py`: YouTube → transcript text + metadata. Cycles yt-dlp player clients and subtitle tracks and backs off on HTTP 429; falls back to youtube-transcript-api.
- `scripts/find_photos.py`: Openverse search → contact sheets → picked photos as data URIs with credits.
- `scripts/assemble.py`: template + body parts → final HTML (derives the accent palette).
- `scripts/check_page.py`: mobile overflow check + desktop/mobile screenshot slices.
- `scripts/make_pdf.py` + `assets/print.css`: colorful A4 PDF via headless Chromium.
- `assets/template_head.html` / `assets/template_foot.html`: design system (light/dark, fonts, code/output/warn/table/part/photo styles) and the lightweight scroll script.
- `references/components.md`: every HTML snippet and the SVG diagram cookbook.
- `references/metaphors.md`: metaphor rules, a bank of concept → metaphor mappings, and photo search terms.
