from examples.log_agent import run

if __name__ == "__main__":
    pipeline = run("Hi, could you please check the issue reported under operation ID b7e4c1a0-3f5d-4e2b-9a6c-7d8e9f0a1b2c?")
    print("Track ID:", pipeline.track_id)
    print("Ticket:", pipeline.ticket)
