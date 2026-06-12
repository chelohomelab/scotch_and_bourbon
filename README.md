# 🥃 Scotch & Bourbon

A self-hosted whiskey cellar tracker for your personal collection.

**Stack:** FastAPI · SQLite · Jinja2 · Tailwind CSS · Docker

---

## Features

| Feature | Details |
|---|---|
| Bottle inventory | All whiskey types: Single Malt Scotch, Blended Scotch, Bourbon, Rye, Irish, Japanese, Canadian, and more |
| Status tracking | Sealed → Opened → Finished per bottle |
| Verdict system | Liked ❤️ and Buy Again 🛒 per bottle |
| Tasting notes | Nose / Palate / Finish / Overall with 1–10 rating |
| Barcode scanning | UPC lookup via UPC Item DB + Open Food Facts fallback |
| Admin scanner queue | Batch scan, autofill, commit to cellar |
| Wish list | Track wanted bottles with priority and one-click convert |
| Photo management | 2 image slots per bottle with swap |
| Dashboard | Stats and type breakdown |
| Multi-user | Cookie-based sessions, admin panel |
| Soft delete | Trash with restore / permanent delete |

---

## Quick Start

### Docker (recommended)

```bash
git clone <repo-url> scotch-and-bourbon
cd scotch-and-bourbon
docker compose up -d
```

Visit **http://localhost:8000** — you'll be directed to `/setup` on first run to create your admin account.

### Local development

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

---

## Proxmox LXC Deployment

Two options are available via `proxmox-setup.sh`:

### Option 1 — Docker (privileged LXC required)

1. Create a **privileged** Debian/Ubuntu LXC container in Proxmox
2. Copy `proxmox-setup.sh` to the container and run it as root:
   ```bash
   bash proxmox-setup.sh   # choose option 1
   ```
3. Open port 8000 in your network/firewall

### Option 2 — Native Python + systemd (unprivileged LXC)

1. Create any Debian/Ubuntu LXC container
2. Copy your application files to `/opt/scotch-and-bourbon`
3. Run the setup script:
   ```bash
   bash proxmox-setup.sh   # choose option 2
   ```
4. Service name: `scotch-and-bourbon`

**Useful service commands:**
```bash
systemctl status scotch-and-bourbon
systemctl restart scotch-and-bourbon
journalctl -u scotch-and-bourbon -f
```

---

## Data Persistence

| Path | Contents |
|---|---|
| `data/cellar.db` | SQLite database |
| `static/uploads/` | Bottle photos and UPC cache images |

When using Docker, both are mounted as volumes so data survives container rebuilds.

---

## Barcode Lookup

The UPC lookup pipeline:
1. **Local cache** — `upc_cache` table (instant, populated on first lookup)
2. **UPC Item DB** — Free API, covers most US spirits
3. **Open Food Facts** — Open crowdsourced database, good fallback for international products

Parsed fields from product titles:
- Whiskey type (Single Malt, Bourbon, Rye, Irish, Japanese…)
- Age statement (12 Year, 18 Year, NAS)
- ABV percentage
- Volume in ml
- Region (Speyside, Islay, Highland, Kentucky…)

---

## Whiskey Types Supported

- Single Malt Scotch
- Blended Scotch
- Blended Malt Scotch
- Single Grain Scotch
- Bourbon
- Tennessee Whiskey
- Rye Whiskey
- Irish Whiskey
- Japanese Whisky
- Canadian Whisky
- World Whisky

---

## Default Port

**8000** — change in `docker-compose.yml` or the systemd service if needed.

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md).
