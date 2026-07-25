import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

from .dummy_logs import DUMMY_LOGS

DEFAULT_TABLE = "exceptions"
DEFAULT_TAKE = 50
# The REST API defaults `timespan` to the last 24h when omitted, and intersects it
# with any `timestamp` filter in the KQL itself. An id/track_id-only lookup with no
# explicit time range must still send a wide timespan, or older matches get silently
# dropped by that 24h default.
DEFAULT_LOOKBACK = timedelta(days=30)


def _as_bool(value):
    return str(value).strip().lower() in ("1", "true", "yes", "on")


@dataclass
class QueryFilters:
    """Filters narrowing an exceptions lookup.

    operation_id also covers what Application Insights calls a "correlation id":
    operation_Id and correlation_id refer to the same value, matched against both
    operation_Id and operation_ParentId. track_id is a separate, app-defined
    identifier stored in customDimensions.trackId.
    """

    operation_id: Optional[str] = None
    track_id: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None

    def is_empty(self):
        return not any((self.operation_id, self.track_id, self.start_time, self.end_time))


def _parse_iso(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def build_kql(filters):
    id_conditions = []
    if filters.operation_id:
        id_conditions.append(
            f"operation_Id == '{filters.operation_id}' or operation_ParentId == '{filters.operation_id}'"
        )
    if filters.track_id:
        id_conditions.append(f"tostring(customDimensions.trackId) == '{filters.track_id}'")

    clauses = []
    if id_conditions:
        clauses.append("(" + " or ".join(id_conditions) + ")")

    start = _parse_iso(filters.start_time)
    if start:
        clauses.append(f"timestamp >= datetime({start.isoformat()})")
    end = _parse_iso(filters.end_time)
    if end:
        clauses.append(f"timestamp <= datetime({end.isoformat()})")

    kql = DEFAULT_TABLE
    if clauses:
        kql += " | where " + " and ".join(clauses)
    kql += f" | order by timestamp desc | take {DEFAULT_TAKE}"
    return kql


def _matches_filters(log, filters):
    if filters.operation_id or filters.track_id:
        id_match = filters.operation_id in (log.get("operation_Id"), log.get("operation_ParentId"))
        if not id_match and filters.track_id:
            dims = log.get("customDimensions") or {}
            id_match = str(dims.get("trackId")) == str(filters.track_id)
        if not id_match:
            return False

    log_time = _parse_iso(log.get("timestamp"))
    start = _parse_iso(filters.start_time)
    if start and log_time and log_time < start:
        return False
    end = _parse_iso(filters.end_time)
    if end and log_time and log_time > end:
        return False

    return True


def build_timespan(filters):
    start = _parse_iso(filters.start_time)
    end = _parse_iso(filters.end_time)
    if start or end:
        end = end or datetime.now(timezone.utc)
        start = start or (end - DEFAULT_LOOKBACK)
        return f"{start.isoformat()}/{end.isoformat()}"
    return f"P{DEFAULT_LOOKBACK.days}D"


def _filter_local_logs(logs, filters):
    matched = [log for log in logs if _matches_filters(log, filters)]
    matched.sort(key=lambda log: log.get("timestamp", ""), reverse=True)
    return matched[:DEFAULT_TAKE]


class AppInsightConnector:
    def __init__(self, local=None, app_id=None, api_key=None):
        self.local = (
            _as_bool(local)
            if local is not None
            else _as_bool(os.environ.get("APPINSIGHT_LOCAL", "true"))
        )
        self.app_id = app_id or os.environ.get("APPINSIGHT_APP_ID")
        self.api_key = api_key or os.environ.get("APPINSIGHT_API_KEY")

    def __repr__(self):
        return f"AppInsightConnector(local={self.local!r})"

    def fetch_logs(self, filters=None):
        filters = filters or QueryFilters()
        if self.local:
            return _filter_local_logs(DUMMY_LOGS, filters)
        return self._fetch_remote_logs(filters)

    def _fetch_remote_logs(self, filters):
        import requests

        if not self.app_id or not self.api_key:
            raise ValueError(
                "APPINSIGHT_APP_ID and APPINSIGHT_API_KEY must be set when APPINSIGHT_LOCAL is disabled"
            )

        response = requests.get(
            f"https://api.applicationinsights.io/v1/apps/{self.app_id}/query",
            headers={"x-api-key": self.api_key},
            params={
                "query": build_kql(filters),
                "timespan": build_timespan(filters),
            },
            timeout=10,
        )
        response.raise_for_status()
        return _parse_query_response(response.json())


def _parse_query_response(payload):
    table = payload["tables"][0]
    columns = [c["name"] for c in table["columns"]]
    return [dict(zip(columns, row)) for row in table["rows"]]
