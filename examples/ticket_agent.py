import re

from langchain_ollama import ChatOllama

from langpoem import Ollama

TICKETS = []

# Simulates Application Insights exception telemetry already exported as JSON.
APP_INSIGHTS_LOGS = [
    {
        "trackId": "TRK-1001",
        "timestamp": "2026-07-10T08:15:32Z",
        "severityLevel": 3,
        "problemId": "NullReferenceException at OrderService.Process",
        "message": "Object reference not set to an instance of an object.",
    },
    {
        "trackId": "TRK-1002",
        "timestamp": "2026-07-11T14:02:10Z",
        "severityLevel": 4,
        "problemId": "SqlTimeoutException at PaymentRepository.Save",
        "message": "Timeout expired while waiting for the SQL connection pool.",
    },
    {
        "trackId": "TRK-1003",
        "timestamp": "2026-07-12T09:47:55Z",
        "severityLevel": 2,
        "problemId": "HttpRequestException at InventoryClient.GetStock",
        "message": "Connection refused by the downstream inventory service.",
    },
]


def find_trackid_agent(llm, text):
    response = llm.invoke(
        "Find the track ID mentioned in the text below. "
        "A track ID looks like 'TRK-1234'. "
        "Reply with ONLY the track ID, nothing else.\n\n"
        f"Text: {text}"
    )
    match = re.search(r"TRK-\d+", response.content)
    if not match:
        raise ValueError(f"No track ID found in text: {response.content!r}")
    print(f"[find_trackid_agent] found -> {match.group()}")
    return match.group()


def find_error_agent(track_id):
    for log in APP_INSIGHTS_LOGS:
        if log["trackId"] == track_id:
            print(f"[find_error_agent] matched -> {log}")
            return log
    raise ValueError(f"No log entry found for track ID: {track_id}")


def open_ticket_agent(log_entry):
    ticket = {
        "id": len(TICKETS) + 1,
        "title": log_entry["problemId"],
        "trackId": log_entry["trackId"],
        "message": log_entry["message"],
        "severityLevel": log_entry["severityLevel"],
        "status": "open",
    }
    TICKETS.append(ticket)
    print(f"[open_ticket_agent] ticket opened -> {ticket}")
    return ticket


def run(text):
    cfg = Ollama()
    llm = ChatOllama(model=cfg.model, base_url=cfg.base_url)

    track_id = find_trackid_agent(llm, text)
    log_entry = find_error_agent(track_id)
    ticket = open_ticket_agent(log_entry)
    return ticket


if __name__ == "__main__":
    sample_text = "Hi, could you please check the issue reported under track ID TRK-1002?"
    run(sample_text)
