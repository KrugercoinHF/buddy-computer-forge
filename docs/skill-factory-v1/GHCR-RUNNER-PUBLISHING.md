# Buddy Skill Factory runner — GHCR build and publication

## Status

This adds a manually dispatched build-and-scan workflow. It does not itself publish an image. The workflow defaults to **dry-run**. A run publishes only when its operator explicitly selects `publish`.

Workflow: `.github/workflows/skill-factory-runner-ghcr.yml`  
Image definition: `Dockerfile.skill-factory-runner`  
Proposed package: `ghcr.io/<repository-owner>/buddy-skill-factory-runner`

## Controls

- Pull-request CI remains read-only and has no package-write permission.
- The build-and-scan job has `contents: read` only.
- The separate publish job receives `packages: write` only when `release_mode=publish`.
- The image is built once, scanned, smoke-tested, saved as an artifact, and that exact saved image is loaded for publication.
- SBOM is emitted in CycloneDX format and retained as a workflow artifact for 14 days.
- HIGH and CRITICAL vulnerabilities with available fixes fail the workflow. Unfixed findings are not silently treated as fixed; review the scan output and SBOM.
- The push uses the workflow-scoped `GITHUB_TOKEN`; no long-lived registry password is stored.
- The package is intended to remain private. Verify its visibility in GitHub Packages after the first push; this workflow does not change package visibility.
- Tags include the source commit, but all local evaluations must use the pushed `image@sha256:<digest>` reference, never a mutable tag.

## First run

1. Open Actions → **Skill Factory runner — build, scan, optional GHCR publish**.
2. Select the feature branch `feat/skill-factory-vscode-bridge-v1`.
3. Run with `dry-run` first. Review the build, SBOM and vulnerability scan.
4. Only after review, dispatch again with `publish` to push the exact scanned image.
5. Verify package visibility is Private and record the returned digest.
6. Supply that digest to the local bridge's `--sandbox-image` argument.

## Security boundary and limitations

This is a constrained developer test image, not a hardened multi-tenant sandbox. Docker containers are not sufficient isolation for hostile or malicious code. Do not run untrusted code with sensitive host access. The current bridge mounts source read-only, disables container networking, drops capabilities, applies resource limits and passes no secrets, but a separately reviewed microVM or equivalent boundary is required before treating candidate code as hostile.

The image uses a versioned Python slim base tag; the base image digest is not yet pinned in the Dockerfile. The published runner digest is immutable, but reproducible rebuilds require pinning and reviewing the base-image digest. Trivy action is version-tagged rather than commit-pinned and should be pinned to a verified commit before production use.

No PR merge, deployment, skill distribution, capability grant, or computer-operation enablement is performed by this workflow.
