#!/usr/bin/env node
// scaffold-bundle.js <trace.jsonl> [--run ID] [--seed HEX] [--prev SHA]
const fs = require("node:fs");
const path = require("node:path");
const crypto = require("node:crypto");
const sha = s => crypto.createHash("sha256").update(s).digest("hex");
function canonical(v) {
  if (v === null || typeof v !== "object") return JSON.stringify(v);
  if (Array.isArray(v)) return "[" + v.map(canonical).join(",") + "]";
  return "{" + Object.keys(v).sort().map(k => JSON.stringify(k) + ":" + canonical(v[k])).join(",") + "}";
}
function option(name, fallback) { const i = process.argv.indexOf(name); return i >= 0 ? process.argv[i + 1] : fallback; }
try {
  const input = process.argv[2];
  if (!input || input.startsWith("--")) throw new Error("usage: node scaffold-bundle.js <trace.jsonl> [--run ID] [--seed HEX] [--prev SHA]");
  const events = fs.readFileSync(input, "utf8").split(/\r?\n/).filter(Boolean).map((line, i) => {
    try { return JSON.parse(line); } catch (e) { throw new Error("invalid JSON at line " + (i + 1) + ": " + e.message); }
  });
  const runId = option("--run", path.basename(input, path.extname(input)));
  const seed = option("--seed", null);
  const prev = option("--prev", null);
  const frames = events.filter(e => e && e.frame && typeof e.frame === "object").map(e => e.frame);
  const bundle = {
    format: "buddy-boardroom-bundle/v1",
    bundle_id: runId + "-" + sha(canonical(events)).slice(0, 12),
    run: { id: runId, seed, created_at: new Date().toISOString() },
    trace: { sha_prev: prev, sha256: sha(canonical(events)), events },
    frames: { sha256: sha(canonical(frames)), items: frames },
    scorecard: { metrics: [], status: "not_scored" },
    confirmation: { status: "pending", required: true, confirmed_by: null, confirmed_at: null },
    hash_algo: "sha256"
  };
  bundle.hash = sha(canonical(bundle));
  const output = runId + "-bundle.json";
  fs.writeFileSync(output, JSON.stringify(bundle, null, 2) + "\n", { flag: "wx" });
  console.log("created: " + output);
  console.log("bundle sha256: " + bundle.hash);
  console.log("events: " + events.length + "; frames: " + frames.length);
  console.log("verify: node " + path.join(__dirname, "verify-bundle.js") + " " + output);
} catch (e) { console.error(e.message); process.exit(2); }
