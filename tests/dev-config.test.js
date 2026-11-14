const test = require("node:test");
const assert = require("node:assert/strict");
const { spawnSync } = require("node:child_process");
const path = require("node:path");

test("Dev wing, skill registry and PM contracts validate without enabling runtime actions", () => {
  const root = path.resolve(__dirname, "..");
  const result = spawnSync(process.execPath, [path.join(root, "scripts/validate-dev-config.js")], {
    cwd: root, encoding: "utf8"
  });
  assert.equal(result.status, 0, result.stdout + result.stderr);
  assert.match(result.stdout, /DEV CONFIG VALID/);
  assert.match(result.stdout, /scheduler and risky execution remain disabled/);
});
