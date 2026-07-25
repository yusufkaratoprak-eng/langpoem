"""Standalone demo: run the Application Insights ticket pipeline directly.

Run with: python examples/log_agent.py
"""

from langpoem.agents import run

if __name__ == "__main__":
    pipeline = run(
        "Hi, could you please check the issue reported under operation ID "
        "b7e4c1a0-3f5d-4e2b-9a6c-7d8e9f0a1b2c?"
    )
    print("Filters:", pipeline.filters)
    print("Ticket:", pipeline.ticket)
