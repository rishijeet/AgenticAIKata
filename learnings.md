# Core Building Blocks

## [Agent]
- Role-specific worker with a clear contract: input schema, output schema, tool permissions, time/budget limits.
- Loop: plan → act (use tool) → observe → update state → terminate.
- Deterministic behavior via configs and guardrails (timeouts, retries, max steps).

## [Tool]
- Reusable, side-effect-aware functions: e.g., fetch_rss, fetch_filings, yfinance_quote, parse_html, summarize_text.
- Typed I/O (dataclasses or Pydantic) for validation.
- Policies: rate limiting, caching, retries, circuit breakers.
- Observability hooks (timing, errors, inputs/outputs size, source URL).

## [Memory/State]
- Short-term: per-agent scratchpad (recent observations).
- Long-term: shared store (blackboard) for cross-agent data (JSON/SQLite/diskcache).
- Optional vector memory (FAISS) for semantic recall—still local/no keys.

# Tooling Contracts (suggested)

## [Schema]
- ToolRequest: name, params, deadline, idempotency_key.
- ToolResponse: status, data, cost (time, tokens), errors, cache_hit flag.

## [Policies]
- Retry/backoff with jitter for flaky sources (e.g., yfinance 429).
- Caching (ETag/Last-Modified for RSS, TTL-based for quotes).
- Rate limiting per domain (Yahoo, sec.gov, news sites).
- Idempotency for writes (log to file only once per id).

# Parallelism Patterns

## [In-Process Async]
- Use asyncio + aiohttp/async tools where possible.
- asyncio.gather(*tasks, return_exceptions=True) for concurrent fetches.
- Wrap blocking calls in threadpool (run_in_executor).

## [Task Groups]
- anyio/trio TaskGroup to spawn agents and ensure structured cancellation on timeout/failure.

## [Scale-Out]
- Queue-based execution with Celery/RQ/Arq (Redis), one worker per agent type.
- Orchestrator publishes jobs, subscribes to results/events.*

# Orchestration Models

## [DAG Orchestrator]
- Nodes = agents; edges = data dependencies.
- Example: Fundamentals → CompanyName → News → Deduplicate → Summarize → Report.
- Topological run; parallelize independent nodes; retry nodes on transient failures.

## [Blackboard Orchestrator]
- Shared “blackboard” (JSON/SQLite). Agents post facts; others react to new facts.
- Pros: flexible, event-driven; easy to extend with new agents.

## [Supervisor (Erlang-style)]
- Supervisor tree: Orchestrator monitors child agents.
- Policies: one-for-one restarts, exponential backoff, max restarts/time window, circuit breaker on repeated failures.

# Monitoring and Health

## [Heartbeats]
- Agents periodically emit heartbeats with status, progress, last tool used.
- Orchestrator sets timeouts; cancels or restarts stuck agents.

## [Tracing/Logs]
- Structured logs (agent, tool, duration, input hash, cache_hit).
- Optional OpenTelemetry spans (local export) for timing and dependency visualization.

# Conflict Resolution and Aggregation

## [De-duplication]
- Cluster near-duplicate articles with TF-IDF/rapidfuzz; pick canonical link.

## [Consensus]
- If agents disagree (e.g., metrics from multiple sources), apply source trust scores or last-updated heuristic.

## [Data Contracts]
- Normalize outputs (e.g., iso dates, currency, fields present/nullable).
- Validate with Pydantic; drop inconsistent records; report validation errors.

# Safety and Cost Controls

## [Budgets]
- Per-agent quotas: max tools calls, wall-clock timeout, I/O limits.
- Orchestrator enforces and can degrade gracefully (e.g., skip summaries if over budget).

## [Rate Limiters]
- Token buckets per domain/tool; centralized in the tool layer.