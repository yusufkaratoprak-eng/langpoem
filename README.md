# LangPoem Starter

Requires a local [Ollama](https://ollama.com) install (`OLLAMA_MODEL` / `OLLAMA_BASE_URL` in `.env`, defaults to `llama3.2` at `http://localhost:11434`).

## Linux / macOS

```bash
make setup   # create venv, install deps, create .env
make run     # start Ollama if needed, run the app
```

## Windows

```bat
setup.bat
run.bat
```

## Manual

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Current implementation only prints messages. Later you can replace RuntimeGraph with LangGraph.
