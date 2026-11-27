# Buddy Agency Bot Department System V1

**Branch:** `feat/bot-departments-v1`  
**Base:** `feat/unified-bot-systems-v1`  
**Status:** proposed integration slice; advisory router only.

## Design

Menusbot is the navigation layer. Jarvis is the command/intake profile. AutoGenius is the routing coordinator. Department profiles are specialists, not independent privileged agents. All share a common policy gateway and task trace. The registry is declarative and capability-labelled.

| Department | Lead profile(s) | Scope | Status |
|---|---|---|---|
| Executive Command | Jarvis, Menusbot | intake, navigation, task status | Advisory |
| Intelligence & Research | BuddyGrokBot | research, synthesis, evidence | Advisory |
| Engineering | A-architect, A-implementer, A-reviewer, A-tester, A-docs | code proposals, tests, review | Advisory |
| AI Boardroom | Boardroom | multi-role deliberation, decision memos | Advisory |
| Knowledge | Knowledge Core | governed retrieval and memory proposals | Advisory |
| QA / BattleMind | BattleMind | comparative tests, challenges, evaluation | Advisory |
| Operations | AutoGenius / Ops | task coordination, mission plans, monitoring | Advisory |
| Finance / Business | Finance | budgets, analysis, plans | Advisory |
| Communications | Content | drafts and editorial work | Advisory |
| Computer | Buddy Computer Forge | controlled device operations | Disabled |

## Routing

Task -> menu/intake -> deterministic intent match or explicit department choice -> registry check -> advisory route -> trace and explanation. No external provider call, shell, network action, computer operation, deployment or repository mutation is enabled. Disabled departments fail closed and are not silently replaced.

## User interface and follow-on

A future integrated command-centre UI should provide department cards, task entry, explicit specialist selection, risk/permission explanation, trace, and approvals. This branch provides the contracts and routing foundation; it does not claim a live production UI or service.

## Safety / acceptance

- Menus are not permissions.
- Capability declarations are not authorization.
- All consequential operations require approval through the central gateway.
- Computer department is disabled in the registry and router.
- Router output is advisory, deterministic, inspectable, testable.
- Add provider adapters and durable tasks only after shared policy, auth, evidence and approvals are integrated.
