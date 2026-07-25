import json
import logging
import re
from datetime import datetime, timezone
from typing import Any, TypedDict

from langchain_ollama import ChatOllama
from langgraph.graph import END, START, StateGraph

from langpoem import Ollama
from .connector import AppInsightConnector, QueryFilters
from .ticket_store import TicketStore

logger = logging.getLogger(__name__)


def _resolve_llm(llm):
    cfg = llm if llm is not None else Ollama()
    if hasattr(cfg, "invoke"):
        return cfg
    return ChatOllama(model=cfg.model, base_url=cfg.base_url)


def _resolve_connector(connector):
    return connector if connector is not None else AppInsightConnector()


OPERATION_ID_PATTERN = r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"

FILTER_EXTRACTION_PROMPT = """Extract Application Insights exception-lookup filters from the text below.
Today's date is {today} (UTC).

Return ONLY a JSON object with these keys (use null for anything not mentioned):
- "operation_id": a GUID identifying the operation, e.g. "6a3fd8b2-9e21-4c3a-8f0d-1a2b3c4d5e6f". \
Also called "correlation id" / "correlationId" — in Application Insights, operation_Id and \
correlation_id are the same value, and it is matched against both operation_Id and operation_ParentId.
- "track_id": a custom application-defined identifier that is not a GUID, e.g. "TRK-1001".
- "start_time": ISO 8601 UTC datetime for the start of a time range, resolving relative dates \
("yesterday", "last 2 hours") against today's date.
- "end_time": ISO 8601 UTC datetime for the end of a time range.

Reply with ONLY the JSON object, nothing else.

Text: {text}
"""


def _parse_filters_response(content):
    content = content.strip()
    if content.startswith("```"):
        content = content.strip("`")
        content = content.split("\n", 1)[1] if "\n" in content else content
    try:
        data = json.loads(content)
    except (TypeError, ValueError):
        data = {}
    return QueryFilters(
        operation_id=data.get("operation_id") or None,
        track_id=data.get("track_id") or None,
        start_time=data.get("start_time") or None,
        end_time=data.get("end_time") or None,
    )


def extract_filters_agent(llm, text):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    response = llm.invoke(FILTER_EXTRACTION_PROMPT.format(today=today, text=text))
    filters = _parse_filters_response(response.content)
    if not filters.operation_id:
        match = re.search(OPERATION_ID_PATTERN, text)
        if match:
            filters.operation_id = match.group()
    logger.debug("extract_filters_agent -> %s", filters)
    return filters


def find_error_agent(filters, connector=None):
    connector = connector or AppInsightConnector()
    logs = connector.fetch_logs(filters)
    if not logs:
        raise ValueError(f"No log entry found for filters: {filters}")
    logger.debug("find_error_agent matched -> %s", logs[0])
    return logs[0]


def _custom_dimensions(log_entry):
    dims = log_entry.get("customDimensions") or {}
    if isinstance(dims, str):
        try:
            dims = json.loads(dims)
        except ValueError:
            dims = {}
    return dims


def open_ticket_agent(log_entry, store):
    ticket = store.add({
        "title": log_entry["problemId"],
        "operation_Id": log_entry["operation_Id"],
        "operation_ParentId": log_entry["operation_ParentId"],
        "outerMessage": log_entry["outerMessage"],
        "severityLevel": log_entry["severityLevel"],
        "status": "open",
        **_custom_dimensions(log_entry),
    })
    logger.debug("open_ticket_agent ticket opened -> %s", ticket)
    return ticket


class TicketState(TypedDict, total=False):
    text: str
    llm: Any
    connector: Any
    store: TicketStore
    filters: QueryFilters
    log_entry: dict
    ticket: dict


def _node_extract_filters(state: TicketState) -> dict:
    return {"filters": extract_filters_agent(state["llm"], state["text"])}


def _node_find_error(state: TicketState) -> dict:
    return {"log_entry": find_error_agent(state["filters"], state["connector"])}


def _node_open_ticket(state: TicketState) -> dict:
    return {"ticket": open_ticket_agent(state["log_entry"], state["store"])}


def _build_ticket_graph():
    graph = StateGraph(TicketState)
    graph.add_node("extract_filters", _node_extract_filters)
    graph.add_node("find_error", _node_find_error)
    graph.add_node("open_ticket", _node_open_ticket)
    graph.add_edge(START, "extract_filters")
    graph.add_edge("extract_filters", "find_error")
    graph.add_edge("find_error", "open_ticket")
    graph.add_edge("open_ticket", END)
    return graph.compile()


TICKET_GRAPH = _build_ticket_graph()


class TicketPipeline:
    """Runs the extract_filters -> find_error -> open_ticket workflow on TICKET_GRAPH."""

    def __init__(self, llm=None, connector=None, text=None, store=None):
        self.llm = _resolve_llm(llm)
        self.connector = _resolve_connector(connector)
        self.text = text
        self.store = store or TicketStore()
        self.filters = None
        self.log_entry = None
        self.ticket = None

    def run(self):
        result = TICKET_GRAPH.invoke({
            "text": self.text,
            "llm": self.llm,
            "connector": self.connector,
            "store": self.store,
        })
        self.filters = result.get("filters")
        self.log_entry = result.get("log_entry")
        self.ticket = result.get("ticket")
        return self


class AppinsightAgent:
    """Fluent builder for the ticket pipeline: .llm(...).connector(...).store(...).text(...).build()"""

    def __init__(self):
        self._llm = None
        self._connector = None
        self._text = None
        self._store = None

    def llm(self, llm):
        logger.debug("AppinsightAgent LLM configured -> %r", llm)
        self._llm = llm
        return self

    def connector(self, connector):
        logger.debug("AppinsightAgent connector configured -> %r", connector)
        self._connector = connector
        return self

    def store(self, store):
        logger.debug("AppinsightAgent store configured -> %r", store)
        self._store = store
        return self

    def text(self, text):
        logger.debug("AppinsightAgent text -> %s", text)
        self._text = text
        return self

    def build(self):
        logger.debug("AppinsightAgent build complete")
        return TicketPipeline(llm=self._llm, connector=self._connector, text=self._text, store=self._store)


def run(text, llm=None, connector=None, store=None):
    return AppinsightAgent().llm(llm).connector(connector).store(store).text(text).build().run()
