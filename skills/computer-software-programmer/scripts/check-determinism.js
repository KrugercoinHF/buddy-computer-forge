#!/usr/bin/env node
// check-determinism.js <module.js> <seed>
const path = require("node:path");
const crypto = require("node:crypto");
function canonical(v) {
  if (v === null || typeof v !== "object") return JSON.stringify(v);
  if (Array.isArray(v)) return "[" + v.map(canonical).join(",") + "]";
  return "{" + Object.keys(v).sort().map(k => JSON.stringify(k) + ":" + canonical(v[k])).join(",") + "}";
}
async function run(fn, seed) {
  const output = await fn(seed);
  return { output, hash: crypto.createHash("sha256").update(canonical(output)).digest("hex") };
}
(async () => {
  const [, , modulePath, seedArg] = process.argv;
  if (!modulePath || seedArg === undefined) { console.error("usage: node check-determinism.js <module.js> <seed>"); process.exit(2); }
  const seed = Number(seedArg);
  if (!Number.isFinite(seed)) { console.error("seed must be a finite number"); process.exit(2); }
  try {
    const target = require(path.resolve(modulePath));
    const fn = target.generate || target.default || target;
    if (typeof fn !== "function") throw new Error("module must export a function");
    const [a, b] = await Promise.all([run(fn, seed), run(fn, seed)]);
    console.log("run 1 sha256: " + a.hash);
    console.log("run 2 sha256: " + b.hash);
    if (a.hash === b.hash) { console.log("result: DETERMINISTIC"); process.exit(0); }
    console.error("result: DIVERGED");
    const left = JSON.stringify(a.output, null, 2).split("\n");
    const right = JSON.stringify(b.output, null, 2).split("\n");
    for (let i = 0; i < Math.max(left.length, right.length); i++) if (left[i] !== right[i]) {
      console.error("first differing line " + (i + 1)); console.error("run 1: " + left[i]); console.error("run 2: " + right[i]); break;
    }
    process.exit(1);
  } catch (e) { console.error(e.stack || String(e)); process.exit(2); }
})();
