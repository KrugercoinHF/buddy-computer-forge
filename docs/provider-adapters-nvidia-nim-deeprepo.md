# NVIDIA NIM and DeepRepo provider adapters

## Scope

This branch adds backend interfaces only. It does not change the UI, worker
execution, task scheduler, owner authentication, deployment configuration, or
existing provider behavior.

Implemented in `buddy/provider_adapters.py`:

- `ProviderRequest` and `ProviderResponse` value objects.
- `ProviderRegistry` for explicit registration and selection.
- `NvidiaNimAdapter` for the OpenAI-compatible NIM chat-completions shape.
- `DeepRepoAdapter` for a locally installed DeepRepo runtime behind an injected
  Python bridge.

## Safety defaults

Both adapters default to disabled. The NIM adapter has no bundled HTTP client:
it requires an explicitly supplied `JsonTransport`, and it cannot make a live
network request by itself. The DeepRepo adapter does not guess a third-party
package name or API; it requires an application-supplied object implementing
`DeepRepoRuntime.generate(request)`.

No API key is read from disk, logged, or persisted. The caller is responsible
for sourcing secrets from its deployment secret manager and injecting them at
runtime. Do not commit provider keys to the repository.

## Minimal integration

```python
from buddy.provider_adapters import (
    NvidiaNimAdapter,
    ProviderRegistry,
)

registry = ProviderRegistry()
registry.register(
    NvidiaNimAdapter(
        base_url="https://<your-nim-endpoint>",
        model="<your-model-id>",
        api_key=secret_from_runtime_environment,
        enabled=False,  # keep disabled until separately reviewed
        transport=application_owned_transport,
    )
)
```

The application-owned transport is deliberately outside this patch. Before
enabling live calls, implement TLS certificate verification, bounded timeouts,
response-size limits, safe error handling, request budgets, and audit events.
Do not forward computer-operation commands or credentials to a model provider.

For DeepRepo, implement the `DeepRepoRuntime` bridge against the exact installed
DeepRepo distribution/version and test its import/API contract independently.
The adapter accepts only the normalized `ProviderResponse` result.

## Verification

Run:

```bash
pytest -q tests/test_provider_adapters.py
```

Tests use fake transports and fake local runtimes. They make no network calls
and require no NVIDIA or DeepRepo installation.
