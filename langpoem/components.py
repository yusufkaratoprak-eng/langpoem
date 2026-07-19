import os

class Ollama:
    def __init__(self, model=None, base_url=None):
        self.model = model or os.environ.get("OLLAMA_MODEL", "llama3.2")
        self.base_url = base_url or os.environ.get(
            "OLLAMA_BASE_URL", "http://localhost:11434"
        )

    def __repr__(self):
        return f"Ollama(model={self.model!r}, base_url={self.base_url!r})"

class SQLiteMemory:
    def __repr__(self):
        return "SQLiteMemory()"
