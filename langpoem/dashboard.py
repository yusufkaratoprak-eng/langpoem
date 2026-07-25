from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

SEVERITY_LABELS = {
    0: ("VERBOSE", "dim"),
    1: ("INFO", "cyan"),
    2: ("WARNING", "yellow"),
    3: ("ERROR", "bold yellow"),
    4: ("CRITICAL", "bold red"),
}

LOG_FIELDS = (
    ("timestamp", "Timestamp"),
    ("operation_Id", "Operation Id"),
    ("operation_ParentId", "Operation Parent Id"),
    ("operation_Name", "Endpoint"),
    ("problemId", "Problem"),
    ("outerMessage", "Message"),
)


def _render_filters(filters):
    if filters is None or filters.is_empty():
        return
    lines = []
    if filters.operation_id:
        lines.append(f"Operation Id: {filters.operation_id}")
    if filters.track_id:
        lines.append(f"Track Id: {filters.track_id}")
    if filters.start_time:
        lines.append(f"Start: {filters.start_time}")
    if filters.end_time:
        lines.append(f"End: {filters.end_time}")
    console.print(Panel.fit("\n".join(lines), title="Filters", border_style="cyan"))


def render_pipeline(pipeline):
    """Render a TicketPipeline result (text, filters, log_entry, ticket) as a console dashboard."""
    console.print(Panel.fit(pipeline.text or "-", title="Query", border_style="blue"))
    _render_filters(pipeline.filters)

    if not pipeline.log_entry:
        console.print(Panel.fit("No matching log entry found.", border_style="red"))
        return

    log_entry = pipeline.log_entry
    severity = log_entry.get("severityLevel", 0)
    label, style = SEVERITY_LABELS.get(severity, ("UNKNOWN", "white"))

    log_table = Table(
        title=f"Log Entry  [{style}]{label}[/{style}]",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold magenta",
    )
    log_table.add_column("Field", style="dim", width=20)
    log_table.add_column("Value")
    for key, field_label in LOG_FIELDS:
        log_table.add_row(field_label, str(log_entry.get(key, "-")))
    console.print(log_table)

    ticket = pipeline.ticket or {}
    ticket_table = Table(
        title="Ticket",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold green",
    )
    ticket_table.add_column("Field", style="dim", width=20)
    ticket_table.add_column("Value")
    for key, value in ticket.items():
        ticket_table.add_row(str(key), str(value))
    console.print(ticket_table)

    status = str(ticket.get("status", "-")).upper()
    console.print(Panel.fit(f"Status: [{style}]{status}[/{style}]", border_style=style))
