import os

from .dummy_logs import DUMMY_LOGS


def _as_bool(value):
    return str(value).strip().lower() in ("1", "true", "yes", "on")


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

    def fetch_logs(self):
        if self.local:
            return DUMMY_LOGS
        return self._fetch_remote_logs()

    def _fetch_remote_logs(self):
        import requests

        if not self.app_id or not self.api_key:
            raise ValueError(
                "APPINSIGHT_APP_ID and APPINSIGHT_API_KEY must be set when APPINSIGHT_LOCAL is disabled"
            )

        response = requests.get(
            f"https://api.applicationinsights.io/v1/apps/{self.app_id}/query",
            headers={"x-api-key": self.api_key},
            params={"query": "exceptions | order by timestamp desc | take 50"},
            timeout=10,
        )
        response.raise_for_status()
        return _parse_query_response(response.json())


def _parse_query_response(payload):
    table = payload["tables"][0]
    columns = [c["name"] for c in table["columns"]]
    return [dict(zip(columns, row)) for row in table["rows"]]
