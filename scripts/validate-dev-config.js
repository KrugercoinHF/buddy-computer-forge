#!/usr/bin/env node
// Validates the declarative Dev wing, skill registry and PM seed files.
const fs = require("node:fs");
const path = require("node:path");
const root = path.resolve(__dirname, "..");
const read = p => JSON.parse(fs.readFileSync(path.join(root, p), "utf8"));
const fail = message => { console.error("✗ " + message); process.exitCode = 1; };
const pass = message => console.log("✓ " + message);
function unique(values, label) {
  if (!Array.isArray(values) || new Set(values).size !== values.length) fail(label + " must be an array of unique values");
}
try {
  const wing = read("wings/dev.json");
  const registry = read("skills/registry.json");
  const pm = read("pm/artifacts.json");
  const expectedAgents = ["A-architect", "A-implementer", "A-reviewer", "A-tester", "A-docs", "A-release"];
  if (wing.id !== "dev" || wing.class !== "meta") fail("dev wing identity/class invalid"); else pass("dev wing is classified as meta");
  unique(wing.agents, "dev.agents");
  if (JSON.stringify(wing.agents) !== JSON.stringify(expectedAgents)) fail("dev agent roster does not match the six declared roles"); else pass("six Dev agents declared");
  if (!["spec", "build", "review", "test", "release"].every(x => wing.hud_lanes.includes(x))) fail("required construction HUD lanes missing"); else pass("construction HUD lanes present");
  if (!wing.gates.includes("P0") || !wing.gates.includes("P10-release")) fail("P0 and P10-release gates are required");
  if (wing.daily_cycle?.enabled !== false || wing.release_policy?.deployment_enabled !== false || wing.release_policy?.computer_execution_enabled !== false) fail("scheduler, deployment and computer execution must remain disabled"); else pass("scheduler and risky execution remain disabled");
  if (registry.format !== "boardroom-skill/v1" || registry.runtime_registry_connected !== false) fail("registry format or disconnected-runtime declaration invalid");
  for (const skill of registry.skills) {
    if (!wing.agents.includes("A-architect") || !wing.agents.includes("A-implementer") || !wing.agents.includes("A-reviewer")) fail("skill bound-agent prerequisites missing");
    if (!fs.existsSync(path.join(root, skill.entrypoint))) fail("missing skill entrypoint: " + skill.entrypoint);
    for (const tool of skill.tools) if (!fs.existsSync(path.join(root, tool))) fail("missing registered tool: " + tool);
    if (skill.registration_state !== "declared") fail("skill must remain declarative until runtime registration exists");
  }
  pass("skill registry references existing skill files and tools");
  if (pm.format !== "boardroom-artifacts/v1" || pm.source_of_truth !== "chronicle.dev.event") fail("PM source-of-truth contract invalid");
  const levels = pm.lifecycle_levels;
  const ids = pm.artifacts.map(a => a.id);
  unique(ids, "pm.artifacts ids");
  for (const artifact of pm.artifacts) {
    if (!levels.includes(artifact.level)) fail("invalid lifecycle level for " + artifact.id);
    if (["RUNNING", "MAINTAINED"].includes(artifact.level)) {
      const e = artifact.owner_evidence;
      if (!e || e.exit_code !== 0 || !e.output || !artifact.artifact_sha256) fail("owner evidence required before " + artifact.id + " can be RUNNING/MAINTAINED");
    }
    if (artifact.owner_agent === "A-architect" && artifact.path.startsWith("skills/")) fail("implementation artifact should be owned by A-implementer, not A-architect");
  }
  if (pm.transition_rules?.ci_success_alone_promotes !== false || pm.transition_rules?.agent_assertion_alone_promotes !== false) fail("promotion evidence policy must reject CI-only and agent-only claims");
  pass("PM lifecycle records and promotion evidence rules valid");
  if (process.exitCode) process.exit(process.exitCode);
  console.log("result: DEV CONFIG VALID");
} catch (error) {
  console.error(error.stack || String(error));
  process.exit(2);
}
