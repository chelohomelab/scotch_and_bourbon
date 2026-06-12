# 🥃 Scotch & Bourbon

A self-hosted whiskey cellar tracker for your personal collection.

**Stack:** FastAPI · SQLite · Jinja2 · Tailwind CSS

---

## Features

| Feature | Details |
|---|---|
| Bottle inventory | All whiskey types: Single Malt Scotch, Blended Scotch, Bourbon, Rye, Irish, Japanese, Canadian, and more |
| Status tracking | Sealed → Opened → Finished per bottle |
| Verdict system | Liked ❤️ and Buy Again 🛒 per bottle |
| Tasting notes | Nose / Palate / Finish / Overall with 1–10 rating per session |
| Barcode lookup | UPC scan autofills brand, type, age, ABV, region, and volume |
| Wish list | Track wanted bottles with priority and one-click convert to cellar |
| Photo management | 2 image slots per bottle with swap |
| Dashboard | Stats by status and type breakdown |
| Multi-user | Cookie-based sessions, remember-me, admin panel |
| Soft delete | Trash with restore / permanent delete |

---

## Local Development

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Visit **http://localhost:8000** — you'll be sent to `/setup` on first run to create your admin account.

---

## Proxmox LXC Deployment

Deployment uses native Python + systemd inside an **unprivileged** LXC container. No Docker required.

### First-Time Install

1. Create a Debian or Ubuntu LXC container in Proxmox (unprivileged is fine)
2. Start the container and open a root shell
3. Copy the application files into the container:
   ```bash
   # From your workstation:
   rsync -av /home/chelo/Scotch_and_Bourbon/ root@<lxc-ip>:/opt/scotch-and-bourbon/
   ```
4. Run the setup script inside the container:
   ```bash
   bash /opt/scotch-and-bourbon/proxmox-setup.sh
   ```
5. On first boot, visit `http://<lxc-ip>:8000/setup` to create your admin account

The script creates a dedicated `cellar` system user, a Python virtual environment, and registers the app as a systemd service that starts on boot.

### Prepare the LXC Container (run once after creation)

Before running the setup script, do a full system update and configure SSH root access:

```bash
# 1. Update and upgrade the container
apt-get update && apt-get upgrade -y

# 2. Allow SSH login as root
sed -i 's/^#\?PermitRootLogin.*/PermitRootLogin yes/' /etc/ssh/sshd_config

# 3. Set a root password (if not already set)
passwd root

# 4. Restart SSH to apply the change
systemctl restart ssh
```

You can now SSH in from your workstation:
```bash
ssh root@<lxc-ip>
```

Or use key-based auth (recommended) — set `PermitRootLogin prohibit-password` instead and add your public key:
```bash
mkdir -p /root/.ssh
echo "<your-public-key>" >> /root/.ssh/authorized_keys
chmod 700 /root/.ssh && chmod 600 /root/.ssh/authorized_keys
```

### Updating

Re-run the same script — it detects the service is already installed and switches to update mode automatically: pulls code (if git), reinstalls dependencies, and restarts the service.

```bash
bash /opt/scotch-and-bourbon/proxmox-setup.sh
```

Or manually:
```bash
# pull new code first, then:
systemctl restart scotch-and-bourbon
```

### Service Commands

```bash
systemctl status  scotch-and-bourbon
systemctl restart scotch-and-bourbon
systemctl stop    scotch-and-bourbon
journalctl -u     scotch-and-bourbon -f
```

---

## Data

| Path | Contents |
|---|---|
| `data/cellar.db` | SQLite database |
| `static/uploads/` | Bottle photos and UPC cache images |

Back these up to preserve your collection data across reinstalls.

---

## Barcode Lookup

When adding a bottle you can scan or type a UPC barcode. The lookup pipeline:

1. **Local cache** — `upc_cache` table; instant on repeat scans
2. **UPC Item DB** — Free API, good coverage for US spirits
3. **Open Food Facts** — Open crowdsourced database, broader international coverage

Fields auto-populated from a successful lookup:
- Whiskey type (Single Malt Scotch, Bourbon, Rye, Irish, Japanese…)
- Age statement (12 Year, 18 Year, NAS)
- ABV %
- Volume in ml
- Region (Speyside, Islay, Highland, Kentucky…)

---

## Whiskey Types

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

**8000** — edit the `ExecStart` line in `/etc/systemd/system/scotch-and-bourbon.service` to change it, then `systemctl daemon-reload && systemctl restart scotch-and-bourbon`.

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md).
