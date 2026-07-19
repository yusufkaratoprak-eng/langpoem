import json
import re

from langchain_ollama import ChatOllama

from langpoem import Ollama
from .connector import AppInsightConnector

TICKETS = []


def _resolve_llm(llm):
    cfg = llm if llm is not None else Ollama()
    if hasattr(cfg, "invoke"):
        return cfg
    return ChatOllama(model=cfg.model, base_url=cfg.base_url)


def _resolve_connector(connector):
    return connector if connector is not None else AppInsightConnector()


OPERATION_ID_PATTERN = r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"


def find_trackid_agent(llm, text):
    response = llm.invoke(
        "Find the Application Insights operation_Id mentioned in the text below. "
        "An operation_Id is a GUID, e.g. '6a3fd8b2-9e21-4c3a-8f0d-1a2b3c4d5e6f'. "
        "Reply with ONLY the operation_Id, nothing else.\n\n"
        f"Text: {text}"
    )
    match = re.search(OPERATION_ID_PATTERN, response.content)
    if not match:
        raise ValueError(f"No operation_Id found in text: {response.content!r}")
    print(f"[find_trackid_agent] found -> {match.group()}")
    return match.group()


def find_error_agent(operation_id, connector=None):
    connector = connector or AppInsightConnector()
    for log in connector.fetch_logs():
        if log["operation_Id"] == operation_id or log["operation_ParentId"] == operation_id:
            print(f"[find_error_agent] matched -> {log}")
            return log
    raise ValueError(f"No log entry found for operation_Id: {operation_id}")


def _custom_dimensions(log_entry):
    dims = log_entry.get("customDimensions") or {}
    if isinstance(dims, str):
        try:
            dims = json.loads(dims)
        except ValueError:
            dims = {}
    return dims


def open_ticket_agent(log_entry):
    ticket = {
        "id": len(TICKETS) + 1,
        "title": log_entry["problemId"],
        "operation_Id": log_entry["operation_Id"],
        "operation_ParentId": log_entry["operation_ParentId"],
        "outerMessage": log_entry["outerMessage"],
        "severityLevel": log_entry["severityLevel"],
        "status": "open",
        **_custom_dimensions(log_entry),
    }
    TICKETS.append(ticket)
    print(f"[open_ticket_agent] ticket opened -> {ticket}")
    return ticket


class TicketPipeline:
    def __init__(self, llm=None, connector=None, text=None):
        self.llm = _resolve_llm(llm)
        self.connector = _resolve_connector(connector)
        self.text = text
        self.track_id = None
        self.log_entry = None
        self.ticket = None

    def find_track_id(self):
        self.track_id = find_trackid_agent(self.llm, self.text)
        return self

    def find_error(self):
        self.log_entry = find_error_agent(self.track_id, self.connector)
        return self

    def open_ticket(self):
        self.ticket = open_ticket_agent(self.log_entry)
        return self

    def run(self):
        return self.find_track_id().find_error().open_ticket()


class AppinsightAgent:
    """Fluent builder for the ticket pipeline: .llm(...).connector(...).text(...).build()"""

    def __init__(self):
        self._llm = None
        self._connector = None
        self._text = None

    def llm(self, llm):
        print("[AppinsightAgent] LLM configured")
        self._llm = llm
        return self

    def connector(self, connector):
        print("[AppinsightAgent] Connector configured")
        self._connector = connector
        return self

    def text(self, text):
        print(f"[AppinsightAgent] Text: {text}")
        self._text = text
        return self

    def build(self):
        print("[AppinsightAgent] Build complete")
        return TicketPipeline(llm=self._llm, connector=self._connector, text=self._text)


def run(text, llm=None, connector=None):
    return AppinsightAgent().llm(llm).connector(connector).text(text).build().run()
