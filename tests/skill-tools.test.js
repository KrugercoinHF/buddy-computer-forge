const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { spawnSync } = require("node:child_process");

const root = path.resolve(__dirname, "..");
const scripts = path.join(root, "skills", "computer-software-programmer", "scripts");
function node(script, args, cwd) {
  return spawnSync(process.execPath, [path.join(scripts, script), ...args], {
    cwd, encoding: "utf8"
  });
}
test("determinism checker accepts same-seed generator", () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "buddy-skill-"));
  try {
    const mod = path.join(dir, "generator.js");
    fs.writeFileSync(mod, "exports.generate = seed => ({seed, nested:{b:2,a:1}});");
    const r = node("check-determinism.js", [mod, "123"], dir);
    assert.equal(r.status, 0, r.stderr + r.stdout);
    assert.match(r.stdout, /DETERMINISTIC/);
  } finally { fs.rmSync(dir, {recursive:true, force:true}); }
});
test("determinism checker detects unstable generator", () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "buddy-skill-"));
  try {
    const mod = path.join(dir, "generator.js");
    fs.writeFileSync(mod, "exports.generate = () => ({value: Math.random()});");
    const r = node("check-determinism.js", [mod, "123"], dir);
    assert.equal(r.status, 1, r.stderr + r.stdout);
    assert.match(r.stdout + r.stderr, /DIVERGED/);
  } finally { fs.rmSync(dir, {recursive:true, force:true}); }
});
test("scaffolded bundle verifies and tampering is detected", () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "buddy-bundle-"));
  try {
    fs.writeFileSync(path.join(dir, "trace.jsonl"), [
      JSON.stringify({event:"click", frame:{t:1,x:10}}),
      JSON.stringify({event:"submit", frame:{t:2,x:20}})
    ].join("\n") + "\n");
    const built = node("scaffold-bundle.js", ["trace.jsonl", "--run", "test-run"], dir);
    assert.equal(built.status, 0, built.stderr + built.stdout);
    const bundlePath = path.join(dir, "test-run-bundle.json");
    const verified = node("verify-bundle.js", [bundlePath], dir);
    assert.equal(verified.status, 0, verified.stderr + verified.stdout);
    const bundle = JSON.parse(fs.readFileSync(bundlePath, "utf8"));
    bundle.trace.events[0].event = "tampered";
    fs.writeFileSync(bundlePath, JSON.stringify(bundle));
    const tampered = node("verify-bundle.js", [bundlePath], dir);
    assert.equal(tampered.status, 1, tampered.stderr + tampered.stdout);
    assert.match(tampered.stdout, /trace-hash/);
  } finally { fs.rmSync(dir, {recursive:true, force:true}); }
});
