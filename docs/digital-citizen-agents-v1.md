# Buddy Digital Citizen Agents V1

**Status:** first bounded decision-engine prototype; simulation-only. **Branch:** `feat/digital-citizen-agents-v1`.

## Concept
A bot is presented as an individual digital citizen: stable identity, name, role, personality traits, values, goals, declared capabilities, autonomy level and scoped memory. Citizens may disagree, evaluate options and make bounded choices. These are software personas and agent processes, not claims that the system is conscious or has human rights or feelings.

## Decision model
1. Receive a task and candidate options from the Router/AutoGenius.
2. Filter options by declared capabilities and the citizen's maximum risk ceiling.
3. Score eligible options using expected value × confidence, estimated cost and declared value alignment.
4. Select the highest-scoring eligible option with deterministic tie-breaking.
5. Emit a structured decision record: selection, scorecard, evidence references, reasons, rejected options and disposition.
6. Require Owner approval for R2/R3, external-effect or irreversible actions. This prototype never executes actions.

## Learning and development
Feedback is recorded as a reviewable training signal. Do not silently rewrite a citizen's identity, values, permissions or model. Profile changes, memory sharing, new capabilities and autonomy increases require explicit policy and Owner-controlled promotion. Training should use curated examples, held-out evaluations, adversarial tests and regression suites; not unrestricted self-modification or reward hacking.

## Reasoning transparency
The system records concise decision rationales, evidence, assumptions, confidence and alternatives. It does not expose or require private hidden chain-of-thought. The goal is useful auditability and reproducibility, not a raw internal reasoning transcript.

## Integration boundaries
- Router chooses which citizen/profile is relevant; the citizen cannot select itself into privileged access.
- AutoGenius schedules work and tracks dependencies; it cannot raise permissions.
- Boardroom can request independent opinions and challenge evidence; votes/recommendations do not authorize execution.
- Shared policy gateway enforces identity, scope, risk and approval for every tool call.
- Computer Forge remains disabled for execution until a separately reviewed, action-bound approval and sandbox design is proven.

## Prototype limits
No live LLM/provider calls, durable memory, autonomous background loop, external tools, computer execution, self-training or deployment. The decision engine is deterministic and testable. A model adapter can be added later behind the same contracts.

## Acceptance tests
- No option outside capability/risk boundaries is selected.
- External, irreversible or high-risk options require approval.
- Observe-only profiles never select actions.
- Every choice has an auditable scorecard and reasons.
- Empty or invalid choices fail closed.
- Feedback never changes identity, capabilities or autonomy without reviewed promotion.
