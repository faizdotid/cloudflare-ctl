"""Terminal interaction helpers based on rich (Prompt, Confirm, Table)."""

from __future__ import annotations

from rich.console import Console
from rich.prompt import Confirm, IntPrompt, Prompt
from rich.table import Table

from models import AuthMethod, Credentials, DNSRecord, Zone

console: Console = Console()

DNS_RECORD_TYPES: list[str] = ["A", "AAAA", "CNAME", "TXT", "MX", "NS"]


def show_error(message: str) -> None:
    console.print(f"[bold red]Error:[/bold red] {message}")


def show_success(message: str) -> None:
    console.print(f"[bold green]OK:[/bold green] {message}")


def show_info(message: str) -> None:
    console.print(f"[cyan]{message}[/cyan]")


def prompt_credentials() -> Credentials:
    """Prompt for credentials: API Token or Email + Global API Key."""
    console.print("[bold]Choose authentication method:[/bold]")
    console.print("  1. API Token (Bearer)")
    console.print("  2. Email + Global API Key")
    choice: str = Prompt.ask("Method", choices=["1", "2"], default="1")

    if choice == "1":
        token: str = Prompt.ask("API Token", password=True)
        return Credentials(method=AuthMethod.API_TOKEN, token=token)

    email: str = Prompt.ask("Cloudflare account email")
    api_key: str = Prompt.ask("Global API Key", password=True)
    return Credentials(method=AuthMethod.GLOBAL_KEY, email=email, api_key=api_key)


def render_zones_table(zones: list[Zone]) -> None:
    table: Table = Table(title="Domains (Zones)")
    table.add_column("No", justify="right", style="dim")
    table.add_column("Domain Name", style="bold")
    table.add_column("Status")
    table.add_column("Nameservers")
    for index, zone in enumerate(zones, start=1):
        table.add_row(
            str(index),
            zone.name,
            zone.status,
            ", ".join(zone.name_servers),
        )
    console.print(table)


def render_dns_table(records: list[DNSRecord]) -> None:
    table: Table = Table(title="DNS Records")
    table.add_column("No", justify="right", style="dim")
    table.add_column("Type", style="bold")
    table.add_column("Name")
    table.add_column("Content")
    table.add_column("TTL", justify="right")
    table.add_column("Proxied")
    for index, record in enumerate(records, start=1):
        ttl: str = "Auto" if record.ttl == 1 else str(record.ttl)
        table.add_row(
            str(index),
            record.type,
            record.name,
            record.content,
            ttl,
            "Yes" if record.proxied else "No",
        )
    console.print(table)


def _ask_number(question: str, maximum: int) -> int:
    """Ask for a number in [0, maximum], re-asking on out-of-range input."""
    while True:
        number: int = IntPrompt.ask(f"{question} (0-{maximum}, 0 to cancel)")
        if 0 <= number <= maximum:
            return number
        show_error(f"Enter a number between 0 and {maximum}.")


def prompt_zone(zones: list[Zone]) -> Zone | None:
    """Pick one zone from the list; None if empty or cancelled."""
    if not zones:
        show_error("No domains (zones) found in this account.")
        return None
    render_zones_table(zones)
    index: int = _ask_number("Pick a domain number", len(zones))
    if index == 0:
        show_info("Cancelled.")
        return None
    return zones[index - 1]


def prompt_dns_record() -> tuple[str, str, str, int, bool]:
    """Form for a new DNS record. Returns (type, name, content, ttl, proxied)."""
    record_type: str = Prompt.ask("Record type", choices=DNS_RECORD_TYPES, default="A")
    name: str = Prompt.ask("Name (e.g. www or @)")
    content: str = Prompt.ask("Content (e.g. 192.0.2.1)")
    ttl_auto: bool = Confirm.ask("Automatic TTL?", default=True)
    ttl: int = 1 if ttl_auto else IntPrompt.ask("TTL (seconds)", default=3600)
    proxied: bool = False
    if record_type in ("A", "AAAA", "CNAME"):
        proxied = Confirm.ask("Enable Cloudflare proxy (orange cloud)?", default=False)
    return record_type, name, content, ttl, proxied


def prompt_record_choice(records: list[DNSRecord]) -> DNSRecord | None:
    """Pick one DNS record from the list; None if empty or cancelled."""
    if not records:
        show_error("This zone has no DNS records yet.")
        return None
    render_dns_table(records)
    index: int = _ask_number("Pick a record number", len(records))
    if index == 0:
        show_info("Cancelled.")
        return None
    return records[index - 1]


def prompt_dns_record_update(
    record: DNSRecord,
) -> tuple[str, str, str, int, bool]:
    """Edit form prefilled with current values. Returns (type, name, content, ttl, proxied)."""
    console.print("[dim]Press Enter to keep the current value.[/dim]")
    record_type: str = Prompt.ask(
        "Record type", choices=DNS_RECORD_TYPES, default=record.type
    )
    name: str = Prompt.ask("Name", default=record.name)
    content: str = Prompt.ask("Content", default=record.content)
    ttl_auto: bool = Confirm.ask("Automatic TTL?", default=record.ttl == 1)
    ttl: int = (
        1
        if ttl_auto
        else IntPrompt.ask(
            "TTL (seconds)", default=record.ttl if record.ttl != 1 else 3600
        )
    )
    proxied: bool = record.proxied
    if record_type in ("A", "AAAA", "CNAME"):
        proxied = Confirm.ask(
            "Enable Cloudflare proxy (orange cloud)?", default=record.proxied
        )
    return record_type, name, content, ttl, proxied
