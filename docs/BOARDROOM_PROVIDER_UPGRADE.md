# Buddy AI Boardroom — live provider foundation

Branch: `feat/boardroom-live-provider-foundation`

This incremental upgrade adds a bounded opt-in OpenAI-compatible provider adapter without changing the existing simulation lifecycle or enabling actions.

- `boardroom_provider.py`: single model-response API; disabled by default.
- `tests/test_boardroom_provider.py`: guardrail tests.
- `docs/live-provider-foundation.md`: configuration and limitations.

Run tests: `pytest -q tests/test_boardroom_provider.py`.

**Not yet integrated:** meetings, UI provider settings, persistent attribution/usage accounting, Anthropic/Gemini native adapters, or execution. The boardroom remains simulation-only unless this module is explicitly called with the opt-in enabled.