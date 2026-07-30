"""HTTP client for the Cloudflare API v4."""

from __future__ import annotations

from typing import Any

import httpx

from models import AuthMethod, Credentials, DNSRecord, Zone

BASE_URL: str = "https://api.cloudflare.com/client/v4"


class CloudflareAPIError(Exception):
    """Error from the Cloudflare API (success=false or HTTP error)."""


class CloudflareClient:
    """httpx wrapper for the Cloudflare API v4."""

    def __init__(self, credentials: Credentials) -> None:
        self._credentials: Credentials = credentials
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if credentials.method is AuthMethod.API_TOKEN:
            headers["Authorization"] = f"Bearer {credentials.token}"
        else:
            headers["X-Auth-Email"] = credentials.email or ""
            headers["X-Auth-Key"] = credentials.api_key or ""
        self._http: httpx.Client = httpx.Client(
            base_url=BASE_URL, headers=headers, timeout=30.0
        )

    def close(self) -> None:
        self._http.close()

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        try:
            response: httpx.Response = self._http.request(method, path, **kwargs)
        except httpx.HTTPError as exc:
            raise CloudflareAPIError(f"Failed to connect to Cloudflare: {exc}") from exc

        try:
            payload: dict[str, Any] = response.json()
        except ValueError as exc:
            raise CloudflareAPIError(
                f"Invalid response (HTTP {response.status_code})"
            ) from exc

        if not payload.get("success", False):
            errors: list[dict[str, Any]] = payload.get("errors", [])
            messages: str = (
                "; ".join(
                    f"{e.get('code', '?')}: {e.get('message', 'unknown error')}"
                    for e in errors
                )
                or f"HTTP {response.status_code}"
            )
            raise CloudflareAPIError(messages)

        return payload.get("result")

    def verify(self) -> str:
        """Verify credentials, returns the account/token identity."""
        if self._credentials.method is AuthMethod.API_TOKEN:
            result: Any = self._request("GET", "/user/tokens/verify")
            return str(result.get("id", "token valid"))
        result = self._request("GET", "/user")
        email: str = str(result.get("email", ""))
        username: str = str(result.get("username", ""))
        return f"{username} <{email}>" if email else username

    def list_zones(self) -> list[Zone]:
        result: Any = self._request("GET", "/zones", params={"per_page": 50})
        return [Zone.from_dict(z) for z in result or []]

    def list_dns_records(self, zone_id: str) -> list[DNSRecord]:
        result: Any = self._request(
            "GET", f"/zones/{zone_id}/dns_records", params={"per_page": 100}
        )
        return [DNSRecord.from_dict(r) for r in result or []]

    def create_dns_record(
        self,
        zone_id: str,
        record_type: str,
        name: str,
        content: str,
        ttl: int,
        proxied: bool,
    ) -> DNSRecord:
        payload: dict[str, Any] = {
            "type": record_type,
            "name": name,
            "content": content,
            "ttl": ttl,
            "proxied": proxied,
        }
        result: Any = self._request(
            "POST", f"/zones/{zone_id}/dns_records", json=payload
        )
        return DNSRecord.from_dict(result)

    def delete_dns_record(self, zone_id: str, record_id: str) -> None:
        self._request("DELETE", f"/zones/{zone_id}/dns_records/{record_id}")

    def update_dns_record(
        self,
        zone_id: str,
        record_id: str,
        record_type: str,
        name: str,
        content: str,
        ttl: int,
        proxied: bool,
    ) -> DNSRecord:
        payload: dict[str, Any] = {
            "type": record_type,
            "name": name,
            "content": content,
            "ttl": ttl,
            "proxied": proxied,
        }
        result: Any = self._request(
            "PATCH", f"/zones/{zone_id}/dns_records/{record_id}", json=payload
        )
        return DNSRecord.from_dict(result)

    def update_nameservers(self, zone_id: str, name_servers: list[str]) -> Zone:
        result: Any = self._request(
            "PATCH",
            f"/zones/{zone_id}",
            json={"vanity_name_servers": name_servers},
        )
        return Zone.from_dict(result)
