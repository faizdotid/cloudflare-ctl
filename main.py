"""Standalone CLI entry point for cloudflare-ctl.

Run with: uv run python main.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from rich.panel import Panel

from client import CloudflareAPIError, CloudflareClient
from menus import run_main_menu
from models import Credentials
from prompts import (
    console,
    prompt_credentials,
    show_error,
    show_success,
)

MAX_AUTH_ATTEMPTS: int = 3


def _show_banner() -> None:
    console.print(
        Panel.fit(
            "[bold cyan]cloudflare-ctl[/bold cyan]\n"
            "[dim]Manage domains, DNS records, and nameservers from your terminal[/dim]",
            border_style="cyan",
        )
    )


def _authenticate() -> CloudflareClient | None:
    """Loop credential prompts until verified or attempts run out."""
    for attempt in range(1, MAX_AUTH_ATTEMPTS + 1):
        credentials: Credentials = prompt_credentials()
        client: CloudflareClient = CloudflareClient(credentials)
        try:
            identity: str = client.verify()
        except CloudflareAPIError as exc:
            show_error(f"Verification failed ({attempt}/{MAX_AUTH_ATTEMPTS}): {exc}")
            client.close()
            continue
        show_success(f"Connected as {identity}")
        return client
    show_error("Too many failed attempts. Exiting.")
    return None


def main() -> None:
    try:
        _show_banner()
        client: CloudflareClient | None = _authenticate()
        if client is None:
            raise SystemExit(1)
        try:
            run_main_menu(client)
        finally:
            client.close()
    except KeyboardInterrupt:
        console.print("\n[dim]Interrupted. Exiting.[/dim]")
        raise SystemExit(130) from None


if __name__ == "__main__":
    main()
