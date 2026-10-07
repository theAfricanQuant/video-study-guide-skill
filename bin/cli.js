#!/usr/bin/env node
/* video-study-guide-skill: install the lesson-making skill into agent harnesses. */
"use strict";
const fs = require("fs");
const os = require("os");
const path = require("path");
const { spawnSync } = require("child_process");

const SKILL = "video-study-guide";
const PKG_ROOT = path.resolve(__dirname, "..");
const SRC = path.join(PKG_ROOT, "skill", SKILL);
const VERSION = require(path.join(PKG_ROOT, "package.json")).version;
const MARK_START = "<!-- video-study-guide-skill:start -->";
const MARK_END = "<!-- video-study-guide-skill:end -->";
const isWin = process.platform === "win32";

const c = (code, s) => (process.stdout.isTTY ? `\x1b[${code}m${s}\x1b[0m` : s);
const ok = (s) => console.log(c("32", "✓ ") + s);
const warn = (s) => console.log(c("33", "! ") + s);
const bad = (s) => console.log(c("31", "✗ ") + s);
const info = (s) => console.log("  " + s);

function parseArgs(argv) {
  const args = { _: [] };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a.startsWith("--")) {
      const key = a.slice(2);
      const next = argv[i + 1];
      if (next !== undefined && !next.startsWith("--")) { args[key] = next; i++; } else { args[key] = true; }
    } else args._.push(a);
  }
  return args;
}

function targetDir(args) {
  if (args.dir) return path.resolve(String(args.dir), SKILL);
  const t = args.target || "claude";
  switch (t) {
    case "claude": return path.join(os.homedir(), ".claude", "skills", SKILL);
    case "claude-project": return path.resolve(".claude", "skills", SKILL);
    case "agents": return path.resolve("skills", SKILL);
    default:
      bad(`Unknown --target "${t}". Use claude, claude-project, agents, or --dir <path>.`);
      process.exit(1);
  }
}

function copyDir(src, dest) {
  fs.mkdirSync(dest, { recursive: true });
  for (const entry of fs.readdirSync(src, { withFileTypes: true })) {
    if (entry.name === "__pycache__" || entry.name === ".venv") continue;
    const s = path.join(src, entry.name), d = path.join(dest, entry.name);
    if (entry.isDirectory()) copyDir(s, d); else fs.copyFileSync(s, d);
  }
}

function addAgentsPointer(skillPath) {
  const agentsFile = path.resolve("AGENTS.md");
  const rel = path.relative(process.cwd(), path.join(skillPath, "SKILL.md")).split(path.sep).join("/");
  const block = `${MARK_START}
## Lessons from videos, PDFs and repos
When asked to turn YouTube videos, PDFs, articles or GitHub repos into a lesson, study guide,
explainer page or PDF, read and follow \`${rel}\` (scripts are in the same folder).
${MARK_END}`;
  let text = fs.existsSync(agentsFile) ? fs.readFileSync(agentsFile, "utf8") : "";
  const re = new RegExp(`${MARK_START}[\\s\\S]*?${MARK_END}`);
  text = re.test(text) ? text.replace(re, block) : (text ? text.trimEnd() + "\n\n" : "") + block + "\n";
  fs.writeFileSync(agentsFile, text);
  ok(`Added a pointer to ${path.relative(process.cwd(), agentsFile) || "AGENTS.md"} (also works for CLAUDE.md-style files: copy the block there if your tool reads that instead).`);
}

function install(args) {
  const dest = targetDir(args);
  if (fs.existsSync(dest)) {
    if (!args.force) {
      warn(`${dest} already exists. Re-run with --force to overwrite (your .venv, if any, is kept).`);
      process.exit(1);
    }
    for (const entry of fs.readdirSync(dest)) if (entry !== ".venv") fs.rmSync(path.join(dest, entry), { recursive: true, force: true });
  }
  if (args.link) {
    fs.mkdirSync(path.dirname(dest), { recursive: true });
    if (fs.existsSync(dest)) fs.rmSync(dest, { recursive: true, force: true });
    fs.symlinkSync(SRC, dest, "dir");
    ok(`Linked ${dest} → ${SRC}`);
  } else {
    copyDir(SRC, dest);
    ok(`Installed ${SKILL} v${VERSION} to ${dest}`);
  }
  if ((args.target || "") === "agents") addAgentsPointer(dest);
  console.log("\nNext steps:");
  info(`npx video-study-guide-skill setup${args.dir ? ` --dir ${args.dir}` : args.target ? ` --target ${args.target}` : ""}   # Python deps + Chromium`);
  info(`npx video-study-guide-skill doctor${args.dir ? ` --dir ${args.dir}` : args.target ? ` --target ${args.target}` : ""}  # check everything`);
  info("Then ask your agent: \"Make a beginner lesson from this video and PDF\".");
}

function uninstall(args) {
  const dest = targetDir(args);
  if (!fs.existsSync(dest)) { warn(`Nothing at ${dest}`); return; }
  fs.rmSync(dest, { recursive: true, force: true });
  ok(`Removed ${dest}`);
  if ((args.target || "") === "agents" && fs.existsSync("AGENTS.md")) {
    const re = new RegExp(`\\n*${MARK_START}[\\s\\S]*?${MARK_END}\\n?`);
    const rest = fs.readFileSync("AGENTS.md", "utf8").replace(re, "\n");
    if (rest.trim()) fs.writeFileSync("AGENTS.md", rest.trimEnd() + "\n"); else fs.rmSync("AGENTS.md");
    ok(rest.trim() ? "Removed the pointer from AGENTS.md" : "Removed AGENTS.md (it only contained the pointer)");
  }
}

function run(cmd, cmdArgs, opts = {}) {
  const r = spawnSync(cmd, cmdArgs, { stdio: opts.quiet ? "pipe" : "inherit", encoding: "utf8", shell: isWin });
  return r;
}
function has(cmd) {
  const r = spawnSync(isWin ? "where" : "which", [cmd], { encoding: "utf8" });
  return r.status === 0;
}
function venvPython(dest) {
  return isWin ? path.join(dest, ".venv", "Scripts", "python.exe") : path.join(dest, ".venv", "bin", "python");
}

function setup(args) {
  const dest = targetDir(args);
  if (!fs.existsSync(dest)) { bad(`Skill not installed at ${dest}. Run install first.`); process.exit(1); }
  const req = path.join(dest, "requirements.txt");
  const py = venvPython(dest);
  if (has("uv")) {
    ok("Using uv to create a private virtual environment for the skill");
    if (!fs.existsSync(py) && run("uv", ["venv", path.join(dest, ".venv")]).status !== 0) process.exit(1);
    if (run("uv", ["pip", "install", "--python", py, "-r", req]).status !== 0) process.exit(1);
  } else {
    warn("uv not found; falling back to python3 -m venv + pip (install uv for faster setup: https://docs.astral.sh/uv/)");
    const sysPy = has("python3") ? "python3" : "python";
    if (!fs.existsSync(py) && run(sysPy, ["-m", "venv", path.join(dest, ".venv")]).status !== 0) process.exit(1);
    if (run(py, ["-m", "pip", "install", "-q", "-r", req]).status !== 0) process.exit(1);
  }
  ok("Python packages installed");
  if (args["no-browser"]) { warn("Skipped Chromium download (--no-browser). PDF export and page checks need it."); }
  else {
    ok("Installing Chromium for Playwright (page checks + PDF export)");
    const extra = process.platform === "linux" && args["with-deps"] ? ["--with-deps"] : [];
    if (run(py, ["-m", "playwright", "install", ...extra, "chromium"]).status !== 0) {
      warn("Chromium install failed. On Linux, try: npx video-study-guide-skill setup --with-deps (needs sudo).");
    }
  }
  console.log("");
  doctor(args);
}

function doctor(args) {
  const dest = targetDir(args);
  console.log(c("1", `video-study-guide-skill v${VERSION} doctor\n`));
  let problems = 0;
  if (fs.existsSync(path.join(dest, "SKILL.md"))) ok(`Skill installed at ${dest}`);
  else { bad(`Skill not found at ${dest} (run: npx video-study-guide-skill install)`); problems++; }

  const py = fs.existsSync(venvPython(dest)) ? venvPython(dest) : (has("python3") ? "python3" : "python");
  const pv = spawnSync(py, ["--version"], { encoding: "utf8", shell: isWin });
  if (pv.status === 0) ok(`Python: ${(pv.stdout || pv.stderr).trim()} (${py === "python3" || py === "python" ? "system" : "skill .venv"})`);
  else { bad("Python 3 not found"); problems++; }

  const mods = [["yt_dlp", "yt-dlp (YouTube transcripts)"], ["PIL", "pillow (photos)"], ["playwright", "playwright (page checks, PDF)"],
                ["youtube_transcript_api", "youtube-transcript-api (fallback)"], ["pypdf", "pypdf (PDF checks)"]];
  for (const [m, label] of mods) {
    const r = spawnSync(py, ["-c", `import ${m}`], { encoding: "utf8", shell: isWin });
    if (r.status === 0) ok(label); else { (m === "youtube_transcript_api" || m === "pypdf" ? warn : bad)(`${label}: missing`); if (!(m === "youtube_transcript_api" || m === "pypdf")) problems++; }
  }
  const chrome = spawnSync(py, ["-c", "from playwright.sync_api import sync_playwright\nwith sync_playwright() as p:\n  b=p.chromium.launch(); b.close()"], { encoding: "utf8", shell: isWin });
  if (chrome.status === 0) ok("Chromium launches"); else { bad("Chromium not ready (run: npx video-study-guide-skill setup)"); problems++; }

  for (const [cmd, label, required] of [["curl", "curl (downloads, photo search)", true], ["git", "git (cloning repos)", true],
                                        ["pdftoppm", "pdftoppm / poppler (PDF page previews)", false], ["uv", "uv (recommended)", false], ["zip", "zip (building .skill files)", false]]) {
    if (has(cmd)) ok(label); else { (required ? bad : warn)(`${label}: not found`); if (required) problems++; }
  }
  console.log("");
  if (problems) { bad(`${problems} problem(s). Fix the ✗ items above, or run: npx video-study-guide-skill setup`); process.exitCode = 1; }
  else ok("All set. Ask your agent to make a lesson from a video, PDF or repo.");
}

function where(args) {
  console.log(targetDir(args));
}

function pack() {
  const r = spawnSync(process.execPath, [path.join(PKG_ROOT, "tools", "build-skill.js")], { stdio: "inherit" });
  process.exit(r.status || 0);
}

function help() {
  console.log(`video-study-guide-skill v${VERSION}
Turn YouTube videos, PDFs, articles and repos into beginner lessons (HTML + PDF).

Usage:
  npx video-study-guide-skill <command> [options]

Commands:
  install      Copy the skill into an agent harness
  setup        Create a private Python env for the skill, install packages + Chromium
  doctor       Check that everything the skill needs is available
  uninstall    Remove the installed skill
  where        Print the install path for the chosen target
  pack         Build dist/video-study-guide.skill (zip) for Claude.ai upload

Targets (for install/setup/doctor/uninstall/where):
  --target claude           ~/.claude/skills/video-study-guide          (default; Claude Code, Agent SDK)
  --target claude-project   ./.claude/skills/video-study-guide          (this project only)
  --target agents           ./skills/video-study-guide + AGENTS.md pointer (Codex, Cursor, other agents)
  --dir <path>              <path>/video-study-guide                    (any harness's skills folder)

Options:
  --force        Overwrite an existing install (keeps its .venv)
  --link         Symlink instead of copy (for developing the skill)
  --with-deps    (setup, Linux) also install Chromium's system libraries (needs sudo)
  --no-browser   (setup) skip the Chromium download

Examples:
  npx video-study-guide-skill install && npx video-study-guide-skill setup
  npx video-study-guide-skill install --target agents
  npx video-study-guide-skill install --dir ~/.config/my-agent/skills
`);
}

const args = parseArgs(process.argv.slice(2));
const cmd = args._[0] || (args.version ? "version" : "help");
({ install, uninstall, setup, doctor, where, pack, version: () => console.log(VERSION), help }[cmd] || (() => { bad(`Unknown command: ${cmd}`); help(); process.exit(1); }))(args);
