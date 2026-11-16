# Terminal Skill — read-only command surface

Status: SPEC / local CLI implementation. This skill is intentionally not a general shell.

## Allowed commands
1. help — print commands.
2. status — show artifact-presence status.
3. score — run presence heuristics.
4. verify — validate JSON and ledger shape.
5. determinism — run the fixed determinism fixture.
6. registry — print the declared skill registry.
7. wings — list wing configuration names.
8. artifacts — list lifecycle artifact IDs and levels.
9. hash — SHA-256 a path under the repository root.
10. poster — verify poster prompt presence.
11. calibrate — run the 10-repeat fixture harness.

## Refusal rules
- T1: refuse arbitrary shell commands, pipes, redirects and command chaining.
- T2: refuse writes outside the documented generated report.
- T3: refuse file paths outside the repository root.
- T4: refuse secrets, environment dumps and credential reads.
- T5: refuse network access, deployment, process control and computer operations.
- T6: refuse destructive commands and mutations to Git or GitHub settings.
- T7: report execution honestly; never claim a command ran unless its exit code is observed.

The CLI is a local developer utility, not an OS sandbox. Do not expose it as a remote service.
