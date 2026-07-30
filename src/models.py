"""Cloudflare data models with explicit types."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Self


class AuthMethod(Enum):
    """Cloudflare API authentication method."""

    API_TOKEN = "api_token"
    GLOBAL_KEY = "global_key"


@dataclass
class Credentials:
    """Credentials for accessing the Cloudflare API."""

    method: AuthMethod
    token: str | None = None
    email: str | None = None
    api_key: str | None = None


@dataclass
class Zone:
    """Represents a Cloudflare zone (domain)."""

    id: str
    name: str
    status: str
    name_servers: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls(
            id=str(data.get("id", "")),
            name=str(data.get("name", "")),
            status=str(data.get("status", "")),
            name_servers=[str(ns) for ns in data.get("name_servers", [])],
        )


@dataclass
class DNSRecord:
    """Represents a DNS record inside a zone."""

    id: str
    type: str
    name: str
    content: str
    ttl: int
    proxied: bool

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls(
            id=str(data.get("id", "")),
            type=str(data.get("type", "")),
            name=str(data.get("name", "")),
            content=str(data.get("content", "")),
            ttl=int(data.get("ttl", 1)),
            proxied=bool(data.get("proxied", False)),
        )
