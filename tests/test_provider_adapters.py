from __future__ import annotations

import pytest

from buddy.provider_adapters import (
    DeepRepoAdapter,
    NvidiaNimAdapter,
    ProviderConfigurationError,
    ProviderDisabledError,
    ProviderRequest,
    ProviderResponse,
    ProviderRegistry,
    build_provider_registry,
)


class FakeTransport:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def post_json(self, url, *, headers, payload, timeout):
        self.calls.append((url, headers, payload, timeout))
        return self.response


class FakeDeepRepoRuntime:
    def __init__(self):
        self.requests = []

    def generate(self, request):
        self.requests.append(request)
        return ProviderResponse(
            provider="deeprepo-runtime",
            model="local-model",
            output="local result",
            usage={"tokens": 7},
        )


def test_nim_is_disabled_by_default_and_does_not_call_transport():
    transport = FakeTransport({})
    adapter = NvidiaNimAdapter(
        base_url="https://nim.example",
        model="test-model",
        transport=transport,
    )
    with pytest.raises(ProviderDisabledError):
        adapter.generate(ProviderRequest(prompt="hello"))
    assert transport.calls == []


def test_nim_maps_chat_request_through_injected_transport():
    transport = FakeTransport(
        {
            "choices": [{"message": {"content": "hello from NIM"}}],
            "usage": {"total_tokens": 12},
        }
    )
    adapter = NvidiaNimAdapter(
        base_url="https://nim.example/",
        model="test-model",
        api_key="test-secret",
        enabled=True,
        transport=transport,
        timeout=9,
    )
    response = adapter.generate(
        ProviderRequest(prompt="question", system_prompt="be concise")
    )
    assert response.provider == "nvidia_nim"
    assert response.output == "hello from NIM"
    assert response.usage == {"total_tokens": 12}
    url, headers, payload, timeout = transport.calls[0]
    assert url == "https://nim.example/v1/chat/completions"
    assert headers["Authorization"] == "Bearer test-secret"
    assert payload["messages"] == [
        {"role": "system", "content": "be concise"},
        {"role": "user", "content": "question"},
    ]
    assert timeout == 9


def test_nim_requires_injected_transport_even_when_enabled():
    adapter = NvidiaNimAdapter(
        base_url="https://nim.example", model="model", enabled=True
    )
    with pytest.raises(ProviderConfigurationError):
        adapter.generate(ProviderRequest(prompt="hello"))


def test_deeprepo_requires_explicit_runtime_bridge():
    adapter = DeepRepoAdapter(enabled=True)
    with pytest.raises(ProviderConfigurationError):
        adapter.generate(ProviderRequest(prompt="hello"))


def test_deeprepo_delegates_to_local_runtime_bridge():
    runtime = FakeDeepRepoRuntime()
    adapter = DeepRepoAdapter(runtime=runtime, enabled=True)
    request = ProviderRequest(prompt="inspect repository")
    response = adapter.generate(request)
    assert runtime.requests == [request]
    assert response.provider == "deeprepo"
    assert response.model == "local-model"
    assert response.output == "local result"


def test_registry_requires_explicit_registration_and_rejects_duplicates():
    registry = ProviderRegistry()
    adapter = DeepRepoAdapter()
    registry.register(adapter)
    assert registry.names() == ("deeprepo",)
    with pytest.raises(ProviderConfigurationError):
        registry.register(adapter)


def test_factory_registers_both_providers_disabled_by_default():
    registry = build_provider_registry()
    assert registry.names() == ("deeprepo", "nvidia_nim")
    with pytest.raises(ProviderDisabledError):
        registry.generate("nvidia_nim", ProviderRequest(prompt="hello"))
    with pytest.raises(ProviderDisabledError):
        registry.generate("deeprepo", ProviderRequest(prompt="hello"))
