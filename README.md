<p align="center">
  <img src="docs/logo.svg" alt="langpoem" width="360" />
</p>

<p align="center"><em>Write agent pipelines like verses — declare what you want, not how to wire it.</em></p>

langpoem is a thin, fluent wrapper around [LangGraph](https://github.com/langchain-ai/langgraph). The graph — nodes, edges, state — is still plain LangGraph underneath; langpoem's only job is to let you *write* a pipeline the way you'd write a short poem: one line per intent, no boilerplate.

```python
AppinsightAgent().llm(Ollama()).text(user_message).build().run()
```

That single chain configures the LLM, hands it the user's message, and runs the whole `extract_filters -> find_error -> open_ticket` graph. The `StateGraph`, its nodes, and its edges are built once in `langpoem/agents/appinsight_agent.py` — every caller just states what it wants and gets a result back.

## Why Ollama?

The pipeline needs an LLM for exactly one job: reading a free-text prompt ("check the issue for operation b7e4c1a0...", "anything for TRK-1001 yesterday?") and turning it into structured filters. [Ollama](https://ollama.com) runs that model locally:

- no API key, no per-token cost, no data leaving the machine — the prompt may contain operation/track identifiers, so keeping it local matters
- works offline, which matters for a support-tooling pipeline that should keep working during an incident even with restricted outbound network access
- swappable — `langpoem.Ollama` is a plain config object (`model`, `base_url`); pointing it at a different local model, or replacing it with any object exposing `.invoke()`, doesn't touch pipeline code

`OLLAMA_MODEL` / `OLLAMA_BASE_URL` in `.env` control which model and endpoint are used (default: `llama3.2` at `http://localhost:11434`).

## How a prompt becomes a KQL query

`langpoem/agents/appinsight_agent.py` runs a 3-node LangGraph `StateGraph`:

```text
extract_filters -> find_error -> open_ticket
```

1. **`extract_filters`** sends your prompt to the LLM and asks it to pull out a `QueryFilters`: an `operation_id` (also called a *correlation id* — Application Insights treats them as the same value), a custom `track_id`, and/or a `start_time`/`end_time` if the prompt mentions a date or time range. Nothing about the prompt's shape is hardcoded — whatever the LLM finds is what gets used downstream.
2. **`find_error`** turns those filters into an actual query:
   - locally (`APPINSIGHT_LOCAL=true`, the default), it filters the bundled dummy data in Python using the same rules;
   - against the real API, `connector.build_kql(filters)` generates the KQL on the fly. An operation id produces `exceptions | where (operation_Id == '...' or operation_ParentId == '...') | order by timestamp desc | take 50`; a time-range prompt instead produces a `where timestamp >= datetime(...) and timestamp <= datetime(...)` clause; a track id produces `where tostring(customDimensions.trackId) == '...'` — and any combination of these is `and`/`or`-ed together depending on what the prompt actually contained.
   - The same time range is also sent as the REST API's `timespan` parameter. Application Insights defaults `timespan` to the last 24h when it's omitted and intersects it with any `timestamp` filter inside the KQL — so an id/track-id-only lookup with no explicit time range would otherwise silently miss anything older than a day. `build_timespan()` widens that window automatically when the prompt didn't ask for a specific range.
   - The connector then executes that query against the real Application Insights REST API (or the local filter) and returns the matching rows.
3. **`open_ticket`** turns the matched log entry into a ticket, stored in an injected `TicketStore` — no shared global state; each pipeline run gets its own store unless you hand it one explicitly.

## Application Insights agent

Controlled via env vars (see `.env`):

- `APPINSIGHT_LOCAL` (default `true`) — use the bundled dummy data in `langpoem/agents/dummy_logs.py` instead of a live call. Set to `false` to query the real Application Insights REST API instead.
- `APPINSIGHT_APP_ID` / `APPINSIGHT_API_KEY` — required when `APPINSIGHT_LOCAL=false`.

## Setup

### Linux / macOS

```bash
make setup   # create venv, install deps, create .env
make run     # start Ollama if needed, run the app
```

### Windows

```bat
setup.bat
run.bat
```

### Manual

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```
