"""Main menu and per-action handlers."""

from __future__ import annotations

from rich.prompt import Confirm, Prompt

from client import CloudflareAPIError, CloudflareClient
from models import DNSRecord, Zone
from prompts import (
    console,
    prompt_dns_record,
    prompt_dns_record_update,
    prompt_record_choice,
    prompt_zone,
    render_dns_table,
    render_zones_table,
    show_error,
    show_info,
    show_success,
)

MENU_OPTIONS: list[str] = [
    "List Domains",
    "List DNS Records",
    "Add DNS Record",
    "Edit DNS Record",
    "Delete DNS Record",
    "Change Nameservers",
    "Exit",
]


def handle_list_zones(client: CloudflareClient) -> None:
    zones: list[Zone] = client.list_zones()
    if not zones:
        show_info("No domains (zones) found in this account.")
        return
    render_zones_table(zones)


def handle_list_dns(client: CloudflareClient) -> None:
    zone: Zone | None = prompt_zone(client.list_zones())
    if zone is None:
        return
    records: list[DNSRecord] = client.list_dns_records(zone.id)
    if not records:
        show_info(f"Zone {zone.name} has no DNS records yet.")
        return
    render_dns_table(records)


def handle_add_dns(client: CloudflareClient) -> None:
    zone: Zone | None = prompt_zone(client.list_zones())
    if zone is None:
        return
    record_type: str
    name: str
    content: str
    ttl: int
    proxied: bool
    record_type, name, content, ttl, proxied = prompt_dns_record()
    record: DNSRecord = client.create_dns_record(
        zone.id, record_type, name, content, ttl, proxied
    )
    show_success(f"Record {record.type} {record.name} -> {record.content} added.")


def handle_edit_dns(client: CloudflareClient) -> None:
    zone: Zone | None = prompt_zone(client.list_zones())
    if zone is None:
        return
    record: DNSRecord | None = prompt_record_choice(client.list_dns_records(zone.id))
    if record is None:
        return
    record_type: str
    name: str
    content: str
    ttl: int
    proxied: bool
    record_type, name, content, ttl, proxied = prompt_dns_record_update(record)
    updated: DNSRecord = client.update_dns_record(
        zone.id, record.id, record_type, name, content, ttl, proxied
    )
    show_success(f"Record {updated.type} {updated.name} -> {updated.content} updated.")


def handle_delete_dns(client: CloudflareClient) -> None:
    zone: Zone | None = prompt_zone(client.list_zones())
    if zone is None:
        return
    record: DNSRecord | None = prompt_record_choice(client.list_dns_records(zone.id))
    if record is None:
        return
    if not Confirm.ask(
        f"Delete record {record.type} {record.name} -> {record.content}?", default=False
    ):
        show_info("Cancelled.")
        return
    client.delete_dns_record(zone.id, record.id)
    show_success(f"Record {record.type} {record.name} deleted.")


def handle_update_ns(client: CloudflareClient) -> None:
    show_info(
        "Note: changing NS via API uses vanity_name_servers "
        "(Business/Enterprise plans only). Registration NS changes stay at the registrar."
    )
    zone: Zone | None = prompt_zone(client.list_zones())
    if zone is None:
        return
    console.print(f"Current nameservers: {', '.join(zone.name_servers) or '-'}")
    raw: str = Prompt.ask("New nameservers (comma-separated)")
    name_servers: list[str] = [ns.strip() for ns in raw.split(",") if ns.strip()]
    if not name_servers:
        show_info("Cancelled.")
        return
    if not Confirm.ask(
        f"Set {zone.name} NS -> {', '.join(name_servers)}?", default=False
    ):
        show_info("Cancelled.")
        return
    updated: Zone = client.update_nameservers(zone.id, name_servers)
    show_success(f"Nameservers for {updated.name} updated.")


def run_main_menu(client: CloudflareClient) -> None:
    """Main menu loop until the user chooses Exit."""
    while True:
        console.print()
        console.print("[bold]Main Menu[/bold]")
        for index, option in enumerate(MENU_OPTIONS, start=1):
            console.print(f"  {index}. {option}")
        choice: str = Prompt.ask(
            "Choose a menu",
            choices=[str(i) for i in range(1, len(MENU_OPTIONS) + 1)],
            default=str(len(MENU_OPTIONS)),
        )
        console.print()
        try:
            if choice == "1":
                handle_list_zones(client)
            elif choice == "2":
                handle_list_dns(client)
            elif choice == "3":
                handle_add_dns(client)
            elif choice == "4":
                handle_edit_dns(client)
            elif choice == "5":
                handle_delete_dns(client)
            elif choice == "6":
                handle_update_ns(client)
            else:
                show_info("Goodbye!")
                return
        except CloudflareAPIError as exc:
            show_error(str(exc))
