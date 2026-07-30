# cloudflare-ctl

Interactive CLI for managing Cloudflare from your terminal: domains (zones), DNS records, and nameservers.

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)

## Usage

```bash
uv run python main.py
```

On start, choose an authentication method:

1. **API Token** (recommended) — create one at https://dash.cloudflare.com/profile/api-tokens
2. **Email + Global API Key**

## Features

- List domains (zones)
- List DNS records per zone
- Add DNS records (A, AAAA, CNAME, TXT, MX, NS) — including subdomains and wildcards
- Edit existing DNS records
- Delete DNS records
- Change nameservers (vanity NS, Business/Enterprise plans)

Credentials are kept in memory only and never written to disk.
