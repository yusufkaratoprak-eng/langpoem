import sys

from langpoem.agents import run
from langpoem.dashboard import render_pipeline

if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    pipeline = run("Hi, could you please check the issue reported under operation ID b7e4c1a0-3f5d-4e2b-9a6c-7d8e9f0a1b2c?")
    render_pipeline(pipeline)
