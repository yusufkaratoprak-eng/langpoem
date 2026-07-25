class TicketStore:
    """In-memory ticket store, injected into the pipeline instead of module-level state."""

    def __init__(self):
        self._tickets = []

    def add(self, ticket):
        stored = {"id": len(self._tickets) + 1, **ticket}
        self._tickets.append(stored)
        return stored

    def all(self):
        return list(self._tickets)

    def __repr__(self):
        return f"TicketStore(count={len(self._tickets)})"
