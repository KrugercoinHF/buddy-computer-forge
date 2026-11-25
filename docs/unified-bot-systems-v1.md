# Unified Bot Systems V1 — Blueprint

**Status:** initial architecture proposal, not an execution system. **Branch:** `feat/unified-bot-systems-v1`.

## Goal
Unify the user's bot concepts into a single governed system instead of duplicating standalone products. AutoGenius is the coordinator; specialist bots are profiles/interfaces backed by shared capabilities, context and tools.

## Terminology
- **Bot/persona:** interaction identity, goals, tone and user-facing menu.
- **Agent:** a bounded task worker with a role, policy, model selection and declared inputs/outputs.
- **Skill/tool:** callable capability with schema, permission scope and risk classification.
- **Menu/UI:** command and navigation surface; menus do not grant privileges.
- **Product/repository:** independently deployable system; integrations are adapters, not assumed to exist.

## Proposed topology
Owner -> Buddy Agency Executive/Approval Gateway -> AutoGenius routing and task orchestration
- BuddyBot: personal assistant and conversation interface
- Grokbot: research, reasoning, synthesis and coding assistance profile
- Jarvis: assistant/workflow profile (details from original history remain to be recovered)
- Menusbot: menu/command discovery and interaction layer (details from original history remain to be recovered)
- Manus-style agent patterns: planner, bounded task execution and progress reporting
- BattleMind: evaluation, challenges, comparative tests and quality signals
- Buddy AI Boardroom: multi-model/agent deliberation, recommendations and minutes
- Buddy Knowledge Core: permissioned shared memory, provenance and retrieval
- Muse: interactive interface/workflow surface where verified
- Buddy Computer Forge: authenticated, sandboxed, approval-gated computer operations

## Routing contract (proposal)
Task request -> classify intent/risk -> choose bot profile -> resolve agent + skill -> check permissions and approval -> execute within bounded environment -> verify result -> persist provenance and feedback -> report to Owner.
No bot/persona may bypass the approval gateway. High-risk or external actions require explicit approval bound to the action digest, actor, expiry and idempotency key.

## Menu contract
Menus are navigational, never privilege grants. Each entry contains stable id, label, intent, input schema, target capability, risk class, permission requirement, approval requirement, result type and cancel/back support. Dynamic menu output must be filtered by actor permissions and capability availability.

## Shared profile schema
Profile fields: id, display_name, purpose, personality, supported_intents, capabilities, model_preferences, memory_scope, autonomy_level (advisory only by default), risk_policy, menu_id, evaluation_suite, enabled_state. Missing adapters must be reported unavailable—not simulated as connected.

## Initial risk levels
- R0: local informational/retrieval, read-only.
- R1: reversible internal draft/work product; no external side effect.
- R2: writes or changes in a controlled workspace; approval and sandbox required.
- R3: external communication, account/security settings, financial or deployment actions; explicit owner approval, scoped credential and audit trail required. Execution remains disabled in this blueprint.

## Acceptance criteria
1. Registry validates against schema and duplicate IDs fail.
2. Routing decisions include selected profile, intent, risk, policy decision and reason.
3. Unavailable capability/provider is not silently substituted or represented as live.
4. Menu options obey permissions; direct tool invocation cannot evade approval checks.
5. Approval is tied to a canonical action digest, actor, expiry and idempotency key.
6. Every task records trace ID, inputs/outputs references, timestamps, agent/profile, tool calls, checks and outcome.
7. Tests cover denial, expiry, replay, scope mismatch, cancellation, unavailable adapter and successful advisory-only flow.
8. No computer execution, provider invocation, deployment or external action is enabled by this blueprint.

## Recovery and provenance
Exact Menusbot and Jarvis specifications, original names, dates and implementation locations must be recovered from accessible conversation history before claiming fidelity. This document labels them as proposals pending recovery. Keep dated decision records and attribute user-originated ideas.

## Next implementation phases
P0 history/source inventory and existing code audit; P1 schemas and registry; P2 routing and permission middleware; P3 menus; P4 adapter contracts and simulated fixtures; P5 integration tests and UI; P6 optional provider adapters after explicit configuration/approval.
