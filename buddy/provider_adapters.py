"""Backend-only provider interfaces for Buddy Computer Forge.

No network client or third-party DeepRepo dependency is imported here.
NVIDIA NIM calls require an explicitly injected transport and opt-in enablement.
DeepRepo calls require an explicitly injected local runtime bridge.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Protocol


class ProviderError(RuntimeError):
    """Base class for provider adapter failures."""


class ProviderDisabledError(ProviderError):
    """Raised when a provider has not been explicitly enabled."""


class ProviderConfigurationError(ProviderError):
    """Raised when required provider configuration is missing."""


@dataclass(frozen=True)
class ProviderRequest:
    prompt: str
    system_prompt: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ProviderResponse:
    provider: str
    model: str
    output: str
    usage: Mapping[str, Any] = field(default_factory=dict)


class JsonTransport(Protocol):
    """Small injectable boundary; implementations may perform HTTP in deployment."""

    def post_json(
        self,
        url: str,
        *,
        headers: Mapping[str, str],
        payload: Mapping[str, Any],
        timeout: float,
    ) -> Mapping[str, Any]: ...


class DeepRepoRuntime(Protocol):
    """Bridge implemented by the locally installed/open-source DeepRepo runtime."""

    def generate(self, request: ProviderRequest) -> ProviderResponse: ...


class NvidiaNimAdapter:
    """OpenAI-compatible NVIDIA NIM adapter with an injected transport.

    This class never creates a network client. A caller must deliberately supply
    a transport and set enabled=True before any request can be sent.
    """

    name = "nvidia_nim"

    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        api_key: str | None = None,
        enabled: bool = False,
        transport: JsonTransport | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.enabled = enabled
        self.transport = transport
        self.timeout = timeout

    def generate(self, request: ProviderRequest) -> ProviderResponse:
        if not self.enabled:
            raise ProviderDisabledError("NVIDIA NIM is disabled")
        if not self.base_url or not self.model:
            raise ProviderConfigurationError("NVIDIA NIM base_url and model are required")
        if self.transport is None:
            raise ProviderConfigurationError(
                "No NVIDIA NIM transport is configured; no network client is bundled"
            )

        messages: list[dict[str, str]] = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.prompt})
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        payload = {"model": self.model, "messages": messages}

        try:
            result = self.transport.post_json(
                f"{self.base_url}/v1/chat/completions",
                headers=headers,
                payload=payload,
                timeout=self.timeout,
            )
            choices = result["choices"]
            output = choices[0]["message"]["content"]
        except ProviderError:
            raise
        except Exception as exc:
            raise ProviderError("NVIDIA NIM request or response failed") from exc

        if not isinstance(output, str):
            raise ProviderError("NVIDIA NIM returned a non-text completion")
        usage = result.get("usage", {})
        return ProviderResponse(
            provider=self.name,
            model=self.model,
            output=output,
            usage=usage if isinstance(usage, Mapping) else {},
        )


class DeepRepoAdapter:
    """Adapter for a local DeepRepo Python runtime supplied by the application.

    The project intentionally does not guess DeepRepo's package/API surface.
    Integrators provide a runtime bridge implementing DeepRepoRuntime.
    """

    name = "deeprepo"

    def __init__(
        self,
        *,
        runtime: DeepRepoRuntime | None = None,
        enabled: bool = False,
        model: str = "deeprepo-local",
    ) -> None:
        self.runtime = runtime
        self.enabled = enabled
        self.model = model

    def generate(self, request: ProviderRequest) -> ProviderResponse:
        if not self.enabled:
            raise ProviderDisabledError("DeepRepo is disabled")
        if self.runtime is None:
            raise ProviderConfigurationError(
                "DeepRepo runtime bridge is not configured"
            )
        try:
            response = self.runtime.generate(request)
        except ProviderError:
            raise
        except Exception as exc:
            raise ProviderError("DeepRepo runtime failed") from exc
        if not isinstance(response, ProviderResponse):
            raise ProviderError("DeepRepo runtime must return ProviderResponse")
        return ProviderResponse(
            provider=self.name,
            model=response.model or self.model,
            output=response.output,
            usage=response.usage,
        )


class ProviderRegistry:
    """Explicit registry; providers are never discovered or enabled implicitly."""

    def __init__(self) -> None:
        self._providers: dict[str, Any] = {}

    def register(self, provider: Any) -> None:
        name = getattr(provider, "name", None)
        if not isinstance(name, str) or not name:
            raise ProviderConfigurationError("Provider must expose a non-empty name")
        if name in self._providers:
            raise ProviderConfigurationError(f"Provider already registered: {name}")
        if not callable(getattr(provider, "generate", None)):
            raise ProviderConfigurationError("Provider must expose generate(request)")
        self._providers[name] = provider

    def get(self, name: str) -> Any:
        try:
            return self._providers[name]
        except KeyError as exc:
            raise ProviderConfigurationError(f"Unknown provider: {name}") from exc

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._providers))

    def generate(self, name: str, request: ProviderRequest) -> ProviderResponse:
        return self.get(name).generate(request)


def build_provider_registry(
    *,
    nim_base_url: str = "",
    nim_model: str = "",
    nim_api_key: str | None = None,
    nim_enabled: bool = False,
    nim_transport: JsonTransport | None = None,
    deeprepo_runtime: DeepRepoRuntime | None = None,
    deeprepo_enabled: bool = False,
) -> ProviderRegistry:
    """Build a registry from explicit settings; both providers default to disabled."""
    registry = ProviderRegistry()
    registry.register(
        NvidiaNimAdapter(
            base_url=nim_base_url,
            model=nim_model,
            api_key=nim_api_key,
            enabled=nim_enabled,
            transport=nim_transport,
        )
    )
    registry.register(
        DeepRepoAdapter(runtime=deeprepo_runtime, enabled=deeprepo_enabled)
    )
    return registry
