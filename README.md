<p align="center">
  <img src="docs/logo.svg" alt="langpoem" width="360" />
</p>

<p align="center"><em>Write agent pipelines like verses — declare what you want, not how to wire it.</em></p>

langpoem is a thin, fluent wrapper around [LangGraph](https://github.com/langchain-ai/langgraph). The graph — nodes, edges, state — is still plain LangGraph underneath; langpoem's only job is to let you *write* a pipeline the way you'd write a short poem: one line per intent, no boilerplate.

```python
AppinsightAgent().llm(Ollama()).text(user_message).build().run()
```

That single chain configures the LLM, hands it the user's message, and runs the whole `extract_filters -> find_error -> open_ticket` graph.

## How it fits together

```mermaid
flowchart LR
    U([Prompt]) --> LP[["langpoem<br/>fluent builder"]]
    LP --> LG{{"LangGraph<br/>StateGraph"}}
    LG -- "1 extract_filters" --> OL[("Ollama<br/>local LLM")]
    OL -. QueryFilters .-> LG
    LG -- "2 find_error" --> AI[("Application Insights<br/>KQL / REST")]
    AI -. log entry .-> LG
    LG -- "3 open_ticket" --> T([Ticket])

    classDef poem fill:#3b3fa1,color:#fff,stroke:#1c1f3d,stroke-width:1px
    classDef graph fill:#6f42c1,color:#fff,stroke:#3a2360,stroke-width:1px
    classDef ollama fill:#ff5fa8,color:#1a0d14,stroke:#c23f80,stroke-width:1px
    classDef appinsight fill:#0d9488,color:#fff,stroke:#0a6f66,stroke-width:1px
    classDef io fill:#1f2430,color:#f5f6fa,stroke:#3a4155,stroke-width:1px

    class U,T io
    class LP poem
    class LG graph
    class OL ollama
    class AI appinsight
```

- **langpoem** — the fluent builder (`.llm().text().build().run()`). The only layer application code (`app.py`, `examples/`) ever touches.
- **LangGraph** — the actual `StateGraph` langpoem builds and runs underneath, once, in `langpoem/agents/appinsight_agent.py`.
- **Ollama** — the local LLM the `extract_filters` node calls to turn free text into structured filters.
- **Application Insights** — the log source the `find_error` node queries, via KQL (remote) or an equivalent Python filter (local dummy data).

## Why Ollama?

- **Private** — the prompt may contain operation/track identifiers, so nothing leaves the machine; no API key, no per-token cost.
- **Offline-capable** — a support-tooling pipeline should keep working during an incident even with restricted outbound network access.
- **Swappable** — `langpoem.Ollama` is a plain config object (`model`, `base_url`). Pointing it at a different local model, or replacing it with any object exposing `.invoke()`, doesn't touch pipeline code.
- **Configurable** — `OLLAMA_MODEL` / `OLLAMA_BASE_URL` in `.env` (default: `llama3.2` at `http://localhost:11434`).

## How a prompt becomes a KQL query

- **`extract_filters`** — sends the prompt to the LLM and asks it to pull out a `QueryFilters`:
  - `operation_id` — also called a *correlation id*; Application Insights treats them as the same value.
  - `track_id` — a custom, app-defined identifier (not a GUID).
  - `start_time` / `end_time` — if the prompt mentions a date or time range.
  - Nothing about the prompt's shape is hardcoded — whatever the LLM finds is what gets used downstream.
- **`find_error`** — turns those filters into an actual query:
  - locally (`APPINSIGHT_LOCAL=true`, the default) — filters the bundled dummy data in Python with the same rules.
  - remotely — `connector.build_kql(filters)` generates the KQL on the fly, e.g. `exceptions | where (operation_Id == '...' or operation_ParentId == '...') | order by timestamp desc | take 50`, or a `where timestamp >= datetime(...) and timestamp <= datetime(...)` clause for a time-range prompt, or `where tostring(customDimensions.trackId) == '...'` for a track id — combined depending on what the prompt actually contained.
  - the same time range is also sent as the REST API's `timespan` parameter, since Application Insights defaults it to the last 24h and intersects it with the KQL — an id/track-id-only lookup with no explicit time range would otherwise silently miss anything older than a day. `build_timespan()` widens that window automatically when the prompt didn't ask for a specific range.
- **`open_ticket`** — turns the matched log entry into a ticket, stored in an injected `TicketStore` — no shared global state; each pipeline run gets its own store unless you hand it one explicitly.

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
