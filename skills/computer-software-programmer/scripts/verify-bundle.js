#!/usr/bin/env node
// verify-bundle.js <bundle.json>
const fs = require("node:fs");
const crypto = require("node:crypto");
const sha = s => crypto.createHash("sha256").update(s).digest("hex");
function canonical(v) {
  if (v === null || typeof v !== "object") return JSON.stringify(v);
  if (Array.isArray(v)) return "[" + v.map(canonical).join(",") + "]";
  return "{" + Object.keys(v).sort().map(k => JSON.stringify(k) + ":" + canonical(v[k])).join(",") + "}";
}
function check(name, pass, detail) { console.log((pass ? "✓ " : "✗ ") + name.padEnd(16) + detail); return pass; }
try {
  const file = process.argv[2];
  if (!file) { console.error("usage: node verify-bundle.js <bundle.json>"); process.exit(2); }
  const b = JSON.parse(fs.readFileSync(file, "utf8"));
  let ok = true;
  const required = ["format", "bundle_id", "run", "trace", "frames", "scorecard", "confirmation", "hash", "hash_algo"];
  const missing = required.filter(k => !(k in b));
  ok = check("schema-minimum", !missing.length, missing.length ? "missing " + missing.join(", ") : "required fields present") && ok;
  ok = check("hash-algorithm", b.hash_algo === "sha256", String(b.hash_algo)) && ok;
  const traceOk = b.trace && Array.isArray(b.trace.events) && typeof b.trace.sha256 === "string" && sha(canonical(b.trace.events)) === b.trace.sha256;
  ok = check("trace-hash", !!traceOk, traceOk ? "canonical events hash matches" : "missing or mismatched events hash") && ok;
  const framesOk = b.frames && Array.isArray(b.frames.items) && typeof b.frames.sha256 === "string" && sha(canonical(b.frames.items)) === b.frames.sha256;
  ok = check("frames-hash", !!framesOk, framesOk ? "canonical frames hash matches" : "missing or mismatched frames hash") && ok;
  const chainOk = b.trace && (b.trace.sha_prev === null || typeof b.trace.sha_prev === "string");
  ok = check("chain-link", !!chainOk, chainOk ? (b.trace.sha_prev || "genesis") : "sha_prev must be null or string") && ok;
  const { hash, ...body } = b;
  const bundleOk = typeof hash === "string" && sha(canonical(body)) === hash;
  ok = check("bundle-hash", !!bundleOk, bundleOk ? "canonical bundle hash matches" : "missing or mismatched bundle hash") && ok;
  process.exit(ok ? 0 : 1);
} catch (e) { console.error(e.stack || String(e)); process.exit(2); }
