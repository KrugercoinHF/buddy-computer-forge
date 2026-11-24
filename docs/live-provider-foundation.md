# Live-provider foundation (opt-in)

This branch adds a single-response OpenAI-compatible adapter (works with compatible hosted APIs and local services such as Ollama when exposed through its OpenAI-compatible endpoint). It is intentionally not wired to meeting orchestration yet.

## Configuration

```bash
export BOARDROOM_LIVE_PROVIDER=false # default; leave off until reviewed
export BOARDROOM_PROVIDER_BASE_URL=https://api.openai.com/v1
export BOARDROOM_PROVIDER_MODEL=gpt-4o-mini
export BOARDROOM_PROVIDER_API_KEY=... # keep out of git and logs
export BOARDROOM_PROVIDER_TIMEOUT=30
```

For local compatible endpoints, API key may be omitted when base URL includes localhost or 127.0.0.1.

## API within Python

```python
from boardroom_provider import capabilities, deliberate
print(capabilities()) # never returns key
result = deliberate("You are a careful advisor.", "Assess this proposal.")
```

Safety limits: opt-in environment flag, one response, 90-second maximum timeout, prompt length bounds, bounded response read, no tool/function calling, no execution, no automatic retries, and sanitized error messages. Provider credentials are never returned by capabilities or error messages.

This is a provider adapter foundation, not an end-to-end Boardroom integration. Wiring into meetings, attribution, persistence, cost accounting, provider-specific adapters (Anthropic/Gemini), and governance reviews remain follow-up work.
