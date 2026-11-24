"""Bounded OpenAI-compatible provider adapter for Buddy AI Boardroom.

Opt-in only. This module performs a single model request and has no tool execution.
"""
from __future__ import annotations
import json, os, urllib.request, urllib.error
from dataclasses import dataclass

@dataclass(frozen=True)
class ProviderConfig:
    base_url: str
    model: str
    api_key: str | None
    timeout_seconds: float = 30.0

    @classmethod
    def from_env(cls) -> "ProviderConfig":
        base = os.getenv("BOARDROOM_PROVIDER_BASE_URL", "https://api.openai.com/v1").rstrip("/")
        model = os.getenv("BOARDROOM_PROVIDER_MODEL", "gpt-4o-mini")
        key = os.getenv("BOARDROOM_PROVIDER_API_KEY")
        timeout = float(os.getenv("BOARDROOM_PROVIDER_TIMEOUT", "30"))
        if not 1 <= timeout <= 90:
            raise ValueError("Provider timeout must be between 1 and 90 seconds.")
        if not model or len(model) > 200:
            raise ValueError("Invalid model identifier.")
        return cls(base, model, key, timeout)

class ProviderError(RuntimeError):
    """Safe, user-facing provider failure; never contains credentials."""

def capabilities() -> dict:
    cfg = ProviderConfig.from_env()
    return {
        "enabled": os.getenv("BOARDROOM_LIVE_PROVIDER", "false").lower() == "true",
        "configured": bool(cfg.api_key) or "localhost" in cfg.base_url or "127.0.0.1" in cfg.base_url,
        "model": cfg.model,
        "base_url": cfg.base_url,
        "tool_execution": False,
        "execution": False,
        "policy": "one model response per request; no tools; no actions",
    }

def deliberate(system_prompt: str, user_prompt: str) -> dict:
    """Send one bounded request. Must be explicitly enabled by the operator."""
    if os.getenv("BOARDROOM_LIVE_PROVIDER", "false").lower() != "true":
        raise ProviderError("Live provider calls are disabled. Set BOARDROOM_LIVE_PROVIDER=true to opt in.")
    cfg = ProviderConfig.from_env()
    if not cfg.api_key and not ("localhost" in cfg.base_url or "127.0.0.1" in cfg.base_url):
        raise ProviderError("Provider API key is not configured.")
    if not system_prompt.strip() or not user_prompt.strip():
        raise ProviderError("Both system and user prompts are required.")
    if len(system_prompt) > 12000 or len(user_prompt) > 20000:
        raise ProviderError("Prompt size exceeds the Boardroom limit.")
    body = json.dumps({
        "model": cfg.model,
        "messages": [{"role":"system","content":system_prompt},{"role":"user","content":user_prompt}],
        "temperature": 0.2,
        "max_tokens": 1200,
    }).encode("utf-8")
    headers = {"Content-Type":"application/json"}
    if cfg.api_key:
        headers["Authorization"] = "Bearer " + cfg.api_key
    req = urllib.request.Request(cfg.base_url + "/chat/completions", data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=cfg.timeout_seconds) as response:
            raw = response.read(1_000_000).decode("utf-8")
        data = json.loads(raw)
        answer = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        return {"provider":"openai-compatible", "model":cfg.model, "content":answer,
                "usage":usage, "tool_calls_disabled":True}
    except urllib.error.HTTPError as exc:
        raise ProviderError(f"Provider returned HTTP {exc.code}.") from None
    except urllib.error.URLError:
        raise ProviderError("Provider connection failed.") from None
    except (ValueError, KeyError, IndexError, TypeError):
        raise ProviderError("Provider returned an invalid response.") from None
