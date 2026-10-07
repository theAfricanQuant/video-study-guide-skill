#!/usr/bin/env node
// Build dist/video-study-guide.skill (a zip of skill/video-study-guide) for Claude.ai upload.
const { execFileSync } = require("child_process");
const fs = require("fs");
const path = require("path");
const root = path.resolve(__dirname, "..");
const dist = path.join(root, "dist");
fs.mkdirSync(dist, { recursive: true });
const out = path.join(dist, "video-study-guide.skill");
if (fs.existsSync(out)) fs.rmSync(out);
try {
  execFileSync("zip", ["-r", "-q", out, "video-study-guide", "-x", "*/__pycache__/*", "*.pyc"], {
    cwd: path.join(root, "skill"), stdio: "inherit",
  });
} catch (e) {
  console.error("Could not run `zip`. Install it (e.g. `sudo apt install zip`) or zip skill/video-study-guide manually.");
  process.exit(1);
}
console.log(`Built ${path.relative(process.cwd(), out)}. Upload it in Claude.ai settings, or share it with others.`);
