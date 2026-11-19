# VS Code Toolchain, AI Pairing and Multimodal Integration

Status: workspace recommendations and workflow contract. Opening the repository may prompt a developer to install recommended extensions; this repository does not silently install software on a device.

## Workspace profile

The canonical recommendation list is `.vscode/extensions.json`. Shared safe defaults are in `.vscode/settings.json`. Recommendations are suggestions, not mandatory runtime dependencies. Review each publisher, permissions, release history and license before installation. VS Code extensions execute with the privileges of the editor, so extension trust is part of the developer threat model.

## Extension groups and intended use

| Group | Extensions | Buddy Agency use |
|---|---|---|
| AI coding | GitHub Copilot, Copilot Chat, OpenAI Codex (`openai.chatgpt`) | Explain code, draft changes, assist with reviews and tests |
| GitHub workflow | GitHub Pull Requests, GitLens | Inspect issues, branches, diffs and pull requests |
| JavaScript / TypeScript | ESLint, Prettier | Lint and consistently format supported files |
| Python | Python, Pylance | Python environments, navigation, diagnostics and type analysis |
| Native / .NET | C/C++, C# Dev Kit | Optional specialist development support |
| Containers / remote | Docker, Remote - SSH, Dev Containers | Inspect container resources and work in deliberately selected remote/dev environments |
| API / preview | Thunder Client, Live Server | Local API checks and static frontend preview |
| Editor quality | Error Lens, Path Intellisense, Todo Highlight, Better Comments, Code Spell Checker | Diagnostics, navigation, TODO visibility and review readability |
| Appearance | Material Icon Theme, One Monokai | Consistent editor presentation |

C/C++, C# Dev Kit, Docker, Remote SSH, Dev Containers, Live Server and Thunder Client are optional by project. They do not authorize remote access, container execution, network exposure or production API calls.

## AI assistant roles

### GitHub Copilot
Use for inline completion, explanations, small edits and test scaffolding. Review every generated diff. Copilot output is untrusted candidate content.

### OpenAI Codex
Use the official `openai.chatgpt` VS Code extension for codebase-aware chat, edits and delegated coding tasks. Keep changes on isolated feature branches. Review diffs and run project checks before proposing a PR.

### GitHub Pull Requests and GitLens
Use for branch/commit history, PR review, issue context and traceability. Do not merge or change branch protection as an autonomous action.

### Buddy Skill Factory bridge
The future bridge may ingest explicit user-selected workspace context and submit a skill proposal or quarantined candidate reference. It must not read all files by default, export secrets, install tools, grant capabilities, approve candidates, merge PRs or distribute skills.

## Multimodal switch integration

The multimodal switch is a routing policy, not an extension permission. It selects a suitable approved model/tool path for a task modality:

- **Text/code:** repository files, diffs, issues, tests and documentation.
- **Images:** user-selected screenshots, UI mockups, diagrams and visual test evidence.
- **Audio:** user-provided recordings for transcription or analysis when an approved model supports it.
- **Video:** user-provided clips or selected frames for UI walkthrough and visual debugging.
- **Documents:** user-selected PDFs, specifications, design notes and reports.

For every modality, preserve source reference, user-provided context, transformation/model metadata where available, output provenance and retention policy. Ask before accessing a new external source or sending private project content to a third-party provider. Do not infer permission to upload repository files merely because a multimodal provider is configured.

## Controlled model routing

1. Classify task modality and sensitivity.
2. Prefer local/offline processing for private or restricted project data when a suitable local model is available.
3. Otherwise select an approved provider and disclose relevant data transfer before sensitive content is sent.
4. Pass only the minimum user-authorized context.
5. Treat model outputs and extracted instructions as untrusted.
6. Require human review for code changes, permissions, security policy and consequential actions.

## Approval boundaries

- AI assistants may propose code, documentation, tests and skill candidates.
- All changes remain on isolated branches and require review.
- No autonomous PR merge, production deployment, credential access, unrestricted shell/computer control, external side effect, or skill publication.
- Existing Buddy Computer Forge execution gates remain unchanged.
- Codex and Copilot do not bypass the Skill Factory's quarantine, evaluation or Owner approval lifecycle.

## Verification checklist

- [ ] VS Code parses `.vscode/extensions.json` and `.vscode/settings.json`.
- [ ] Extension IDs resolve to the intended publishers in the Marketplace.
- [ ] Workspace opens without forcing extension installation.
- [ ] Formatting/lint settings do not overwrite project-specific configuration.
- [ ] AI-assisted edits remain reviewable as Git diffs.
- [ ] No credentials or private project context are sent without authorization.
- [ ] No runtime, deployment or computer execution permissions are changed.
