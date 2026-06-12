# Changelog

All notable changes are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/).

---

## [1.0.1] – 2026-06-12

### Changed
- `proxmox-setup.sh` now auto-detects install vs. update mode — safe to re-run; on update it pulls code, reinstalls dependencies, and restarts the service without touching the systemd unit or recreating the user
- Proxmox deployment simplified to unprivileged LXC + native Python/systemd only; Docker option removed

### Removed
- Admin scanner queue — barcode lookup is available directly in the Add Bottle form; Open Food Facts provides sufficient coverage without a separate staging workflow

---

## [1.0.0] – 2026-06-12

### Added
- **Bottle inventory** — Track all whiskey types (Single Malt Scotch, Blended Scotch, Bourbon, Rye, Irish, Japanese, Canadian, and more)
- **Bottle status tracking** — Sealed / Opened / Finished states per bottle
- **Verdict system** — Per-bottle Liked ❤️ and Buy Again 🛒 flags
- **Tasting notes** — Nose / Palate / Finish / Overall fields with 1–10 rating; multiple sessions per bottle
- **Barcode lookup** — UPC scan in the Add Bottle form; pipeline: local cache → UPC Item DB → Open Food Facts; auto-parses type, age, ABV, region, volume
- **Wish list** — Track wanted bottles with priority (Low/Medium/High), estimated price, URL, and one-click convert to cellar
- **Photo management** — 2 image slots per bottle with swap support
- **Dashboard** — Summary stats (total, sealed, opened, finished, liked, buy again, wish list count) and type breakdown chart
- **Multi-user authentication** — Cookie-based sessions, remember-me (30 days), bcrypt passwords
- **Admin panel** — User management (create, promote, enable/disable, delete)
- **Soft delete + trash** — Restore or permanently delete bottles
- **Mark as sold** — Optional price-sold tracking
- **Proxmox LXC deployment** — `proxmox-setup.sh` installs the app as a systemd service in an unprivileged container
- **SQLite database** — Zero-configuration, stored in `data/cellar.db`
- **Auto schema migration** — `init_db()` adds columns to existing databases without data loss
