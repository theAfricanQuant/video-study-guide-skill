# Component library

Copy these snippets into body part files. All classes are already styled by
`assets/template_head.html`. Don't invent new CSS unless a component is truly missing.

## Contents
0. Lesson components (code, output, warnings, parts, tables, photos)
1. Header: hero, watch button, chapter nav
2. Intro block
3. Chapter wrapper
4. Two-column split (prose + diagram)
5. Story card
6. Analogy box
7. Card grid
8. Pull quote
9. Checklist
10. Quick-check quiz
11. Inline term (hover/tap definition)
12. Diagram figure + SVG cookbook
13. Step-by-step plan
14. Glossary
15. Footer

---

## 0. Lesson components

All styles below are already in `assets/template_head.html`.

**Part divider** (groups chapters into Parts I, II, III…):
```html
<div class="part"><span class="lbl">Part II</span><h2>Hands-on: the basics</h2><p>One-line description.</p></div>
```

**Code block** (dark, with a language tag; color spans optional: `k` keyword, `c` comment, `s` string, `n` number):
```html
<pre class="code" data-lang="sql"><span class="k">SELECT</span> city, <span class="k">count</span>(*) <span class="k">FROM</span> sales <span class="k">GROUP BY</span> city;  <span class="c">-- comment</span></pre>
```
Escape `<`, `>` and `&` inside code. Use `data-lang="bash"`, `"python"`, `"sql"`, `"text"`.

**Real output box** (only for output you actually produced by running the code):
```html
<pre class="out">Abuja 833334 · Enugu 833333 · …</pre>
```

**Warning / correction box** (mistakes in sources, security notes, gotchas found while testing):
```html
<div class="warn"><b>Small fix to the article.</b> What was wrong, why, and the corrected version.</div>
```

**Verified box** (once, near the start):
```html
<div class="verify"><b>Everything here was tested.</b> Every example was run on … Boxes marked <em>real output</em> are actual results.</div>
```

**Comparison table**:
```html
<div class="tablewrap"><table class="cmp">
  <thead><tr><th></th><th>Option A</th><th>Option B</th></tr></thead>
  <tbody><tr><td>Built for</td><td>…</td><td>…</td></tr></tbody>
</table></div>
```

**Analogy with a photo** (photo from `scripts/find_photos.py`; keep the credit):
```html
<div class="analogy ng"><div class="icon">🛺</div><div>
  <figure class="aph"><img src="data:image/jpeg;base64,…" alt="Describe the photo">
    <figcaption>Photo: <a href="LANDING_URL" target="_blank" rel="noopener">TITLE</a> by CREATOR, LICENSE</figcaption></figure>
  <b>Keke / bajaj / tuk-tuk analogy: the passenger and the driver</b>
  <p>…</p>
</div></div>
```
Use class `analogy ng` for all analogy boxes (warm gold style).

**Code-style text inside SVG**: put `class="mono"` on the `<g>` so it renders in a monospace font.

## 1. Header

```html
<header>
  <section class="hero">
    <div>
      <p class="who">A study guide to the [Channel] interview with [Guest]</p>
      <h1>[Short, punchy title: the core idea]</h1>
      <p class="dek">[1–2 sentences: who they are + what the reader will get.]</p>
      <div class="meta">
        <span class="chip">📚 [N] chapters + a step-by-step plan</span>
        <span class="chip">🧭 Built for beginners</span>
        <span class="chip">⏱ About [N] minutes</span>
      </div>
      <p style="margin-top:1.25rem;display:flex;gap:.6rem;flex-wrap:wrap">
        <a class="watch" href="[VIDEO URL]" target="_blank" rel="noopener">▶ Video: short title</a>
        <!-- one button per video; a teal one for a repo: style="background:var(--teal)" -->
      </p>
    </div>
    <div class="hero-art">
      <svg viewBox="0 0 420 360" role="img" aria-labelledby="hT hD">
        <title id="hT">[what it shows]</title>
        <desc id="hD">[plain-text description for screen readers]</desc>
        <!-- one memorable diagram: a growth staircase, a journey path, a machine… -->
      </svg>
    </div>
  </section>
  <nav class="toc" aria-label="Chapters">
    <ol>
      <li><a href="#c1">1 · [2-word label]</a></li>
      <!-- one per chapter -->
      <li><a href="#plan">Your plan</a></li>
      <li><a href="#glossary">Glossary</a></li>
      <li><a href="#references">References</a></li>
    </ol>
  </nav>
</header>
<main>
```

## 2. Intro block

```html
<section class="prose" style="padding:2.5rem 0 1rem">
  <p><strong>Who is [he/she/they]?</strong> [2–3 sentences of context. Note caption spelling if you corrected a name.]</p>
  <p>[Their one big idea, in bold.]</p>
  <p class="note">Figures are as stated in the interview. The original video link is at the top and bottom of this page.</p>
</section>
```

## 3. Chapter wrapper

```html
<section class="chapter" id="c1">
  <div class="chapter-head"><div class="chapter-num">1</div><div><h2>[Chapter title]</h2><p>[One-line subtitle]</p></div></div>
  <div class="prose">
    <p>…</p>
    <h3>[Sub-heading]</h3>
    <h4>[Smaller heading]</h4>
  </div>
</section>
```
Use `chapter-num` = `★` for the plan, `Aa` for the glossary.

## 4. Two-column split

```html
<div class="split">
  <div class="prose">…text…</div>
  <figure class="diagram" style="margin-top:0">…svg…<figcaption>…</figcaption></figure>
</div>
```
Collapses to one column under 980px. A narrow (400-wide viewBox) diagram fits the right column; a wide (860–900) one goes full width outside `.split`.

## 5. Story card

```html
<div class="story">
  <p class="label">Story</p>            <!-- or "Example", "From the interview", "Honest confession" -->
  <h4>[Memorable story title]</h4>
  <p>[Story in your own words: who, what happened, the turn, the outcome.]</p>
  <p class="lesson">Lesson: [one sentence]</p>
</div>
```

## 6. Analogy box

```html
<div class="analogy"><div class="icon">🚲</div><div><b>Analogy: [name]</b><p>[Everyday comparison a 17-year-old instantly gets.]</p></div></div>
```

## 7. Card grid

```html
<div class="grid3">
  <div class="card teal"><p class="k">[Icon + label]</p><p>[1–3 sentences]</p></div>
  <div class="card coral">…</div>
  <div class="card gold">…</div>
  <div class="card plum">…</div>
</div>
```
Colors: `teal`, `coral` (the accent), `gold`, `plum`. For a single stacked column: `style="grid-template-columns:1fr"`.

## 8. Pull quote

```html
<p class="pull">[A short paraphrased idea, or a very short attributed quote.]</p>
```

## 9. Checklist

```html
<ul class="check">
  <li><span><strong>[Bold lead].</strong> [Detail]</span></li>
</ul>
```
For a numbered-feeling list without numbers, use `<ol class="check" style="list-style:none">`.

## 10. Quick-check quiz

```html
<details class="quiz"><summary>[A realistic scenario question]</summary><p><strong>[Answer].</strong> [Why]</p></details>
```

## 11. Inline term

```html
<span class="term" tabindex="0">reverse mortgage<span class="tip">A loan that lets you borrow cash against the value of your house.</span></span>
```
Use on the first appearance of jargon. Keep tips under ~25 words.

## 12. Diagram figure + SVG cookbook

```html
<figure class="diagram">
  <svg viewBox="0 0 860 260" role="img" aria-labelledby="xT xD">
    <title id="xT">[Title]</title>
    <desc id="xD">[Full plain-language description of what the diagram shows]</desc>
    …
  </svg>
  <figcaption>[One sentence: the takeaway]</figcaption>
</figure>
```

**Always use theme classes, never hard-coded colors** (except `fill="#fff"` for text on a solid accent shape), so dark mode works:

| Purpose | Class |
|---|---|
| Text, dark | `svg-ink` |
| Text, secondary | `svg-muted` |
| Card background | `svg-sheet` / `svg-paper` |
| Solid fills | `f-coral` `f-teal` `f-gold` `f-plum` |
| Soft fills | `f-coral-soft` `f-teal-soft` `f-gold-soft` `f-plum-soft` |
| Strokes | `s-coral` `s-teal` `s-gold` `s-plum`, `stroke-ink` `stroke-rule` `stroke-muted` |
| Text sizes | `t-sm` (13) `t-md` (15 bold) `t-lg` (19 bold) `t-xl` (26) `t-disp` (30 serif) |

Inline color via style also works: `style="fill:var(--coral);font-weight:700"`.

**Arrow marker** (give each marker a unique id per page):
```html
<defs><marker id="arrA" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="8" markerHeight="8" orient="auto"><path d="M0 0 L10 5 L0 10 z" style="fill:var(--muted)"/></marker></defs>
<line x1="100" y1="50" x2="160" y2="50" class="stroke-muted" stroke-width="3" marker-end="url(#arrA)"/>
```

**Diagram types that work well** (pick what matches the idea):
- **Process / flow**: rounded boxes + arrows (funnels, workflows, 1‑1‑1 chains).
- **Staircase / bars**: growth milestones, before/after comparisons. Draw to scale when the numbers matter and say "to scale" in the caption.
- **Timeline**: a thick rounded line with circles and two-line labels under each (life stories).
- **Line chart**: trends, plateaus, "valley where people quit," feast-and-famine zigzags. Draw axes with `stroke-rule`, label axes with `t-sm svg-muted`.
- **Cycle / loop**: a circle with 3–4 nodes and curved arrows (feedback loops, repeating processes).
- **Venn / overlap**: semi-transparent circles (`opacity=".35"`) for combinations.
- **Decision filter**: inputs → diamond (`polygon`) → YES/NO boxes.
- **Spectrum / scale**: a bar with markers (−100…+100, easy-to-copy → hard-to-copy).
- **Concentric circles**: audiences, test groups, ponds.
- **Simple scenes**: abstract shapes only (paths, pipes, a lens and rays, an elevator). Keep it schematic.

**Originality:** every diagram is drawn from scratch to explain an idea. Never draw or trace a real company's logo, a film/TV/comic/game character, a movie poster, an album cover or any other existing artwork, even if the video mentions it. Refer to it in words instead.

**Layout tips:** keep labels at least 10px inside the viewBox edges. Labels drawn right of a shape near the right edge get clipped, so use `text-anchor="end"`. Wide diagrams (860–900) need ≥13px text to stay legible on phones.

## 13. Step-by-step plan

```html
<section class="chapter" id="plan">
  <div class="chapter-head"><div class="chapter-num">★</div><div><h2>Your step-by-step plan to do the same</h2><p>[Guest]'s advice, turned into an order of operations.</p></div></div>
  <div class="prose"><p>This sequence is my synthesis of the interview. The timing is a suggested pace, not something [guest] prescribes word for word.</p></div>
  <ol class="playbook">
    <li><div><span class="when">Week 1</span><h4>[Imperative step title]</h4><p>[What to do, concretely.]</p></div></li>
    <li><div><span class="when">Ongoing</span><h4>…</h4><ul><li>…</li></ul></div></li>
  </ol>
</section>
```

## 14. Glossary

```html
<section class="chapter" id="glossary">
  <div class="chapter-head"><div class="chapter-num">Aa</div><div><h2>[Topic] words, explained</h2><p>The jargon from the interview, in plain English.</p></div></div>
  <dl class="gloss">
    <div><dt>[Term]</dt><dd>[Plain definition, one sentence.]</dd></div>
  </dl>
</section>
</main>
```

## 15. References + footer

End `<main>` with a References chapter, then a short footer.
```html
<section class="chapter" id="references">
  <div class="chapter-head"><div class="chapter-num">§</div><div><h2>References</h2><p>Sources, data, and credits.</p></div></div>
  <div class="prose">
    <h3>History and concepts</h3><ul class="check"><li><span>Author, A. (Year). Title. <em>Journal</em>, vol(issue).</span></li></ul>
    <h3>Articles</h3> … <h3>Videos</h3> … <h3>Code</h3> … <h3>Software and documentation</h3> … <h3>News</h3> … <h3>Datasets</h3> …
    <h3>Photographs</h3><p>All photographs are openly licensed … credited beneath each image.</p>
  </div>
</section>
</main>
<footer><p>Video content is summarized and paraphrased; code is quoted from the supplied materials with attribution; outputs marked "real output" were produced on [versions]; …</p></footer>
```

## 15b. Old single-video footer (still fine for one-video guides)

```html
<footer>
  <p><strong>Original video:</strong> <a href="[URL]" target="_blank" rel="noopener">"[Exact video title]" on [Channel] (YouTube)</a></p>
  <p>This guide summarizes and paraphrases the interview for learning. Figures and results are as stated in the conversation and haven't been independently verified. Names were taken from auto-generated captions; double-check before quoting. The step-by-step plan is a synthesis of the advice, not a plan given word-for-word in the video.</p>
</footer>
```
