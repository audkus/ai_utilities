Workflow: ai-utilities-sync-async-clients-v1

Goal
- Provide a clean SDK for embedding in other apps with both sync and async clients.
- Public imports must be:
    from ai_utilities import AiClient, AsyncAiClient, AiSettings

Public API (must implement)
1) Sync client: AiClient
- ask(prompt: str, *, return_format: Literal["text","json"]="text", **kwargs) -> str | dict
- ask_many(prompts: Sequence[str], *, return_format: Literal["text","json"]="text", **kwargs) -> list[AskResult]
  - sequential execution (default)
  - returns per-prompt AskResult; one failure must not fail whole batch

2) Async client: AsyncAiClient
- ask(prompt: str, *, return_format: Literal["text","json"]="text", **kwargs) -> str | dict
- ask_many(
    prompts: Sequence[str],
    *,
    concurrency: int = 5,
    return_format: Literal["text","json"]="text",
    fail_fast: bool = False,
    on_progress: Callable[[int,int],None] | None = None,
    **kwargs
  ) -> list[AskResult]
  - parallel execution using asyncio.Semaphore(concurrency)
  - cancellation-friendly
  - retries for transient failures (429/5xx/timeouts) with exponential backoff + jitter, max 3 attempts

3) AskResult model (Pydantic)
- prompt: str
- response: str | dict[str, Any] | None
- error: str | None  (string message only; keep JSON-serializable)
- duration_s: float

Settings
- AiSettings must be Pydantic Settings (pydantic-settings) with env var support.
- Prefer immutable-ish behavior (avoid mutation after init).

Architecture constraints
- Keep provider logic behind explicit provider interfaces:
    SyncProvider.ask(...)
    AsyncProvider.ask(...) (async def)
- Avoid duplicating OpenAI request building / response parsing / error mapping:
  create shared helper(s) and only split transport (sync vs async).
- Do not use asyncio.run() inside library code paths (allowed only in examples/CLI).

Packaging / exports
- Ensure src-layout under src/ai_utilities/
- Top-level ai_utilities/__init__.py must export AiClient, AsyncAiClient, AiSettings in __all__.

Tests (pytest, no network)
- test_ai_client_ask_many_sequential_order
- test_async_ai_client_ask_many_concurrency_cap (max in-flight <= concurrency)
- test_async_ai_client_partial_failures_returned
- test_async_ai_client_retry_success

README updates
- Add minimal sync example using AiClient
- Add minimal async example using AsyncAiClient with ask_many(concurrency=...)
- Add short “Mixing sync + async” guidance:
  - async apps should use AsyncAiClient
  - if sync code must run in async context: use await asyncio.to_thread(...)

Working style
- First: list files you will create/modify and why (no code yet).
- Then implement in small patches, showing diffs per patch.
- After each patch: state how to run tests and what changed.

Stability requirement:
- No breaking changes to existing user-facing sync API (AiClient.ask must keep same semantics).
- Keep existing exceptions/error_codes as canonical; do not introduce parallel exception hierarchies.
