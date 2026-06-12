# Changelog

All notable changes are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/).

---

## [1.0.0] – 2026-06-12

### Added
- Initial release of the Scotch & Bourbon whiskey cellar app
- **Bottle inventory** — Track all whiskey types (Single Malt Scotch, Bourbon, Rye, Irish, Japanese, and more)
- **Bottle status tracking** — Sealed / Opened / Finished states per bottle
- **Verdict system** — Per-bottle Liked ❤️ and Buy Again 🛒 flags
- **Tasting notes** — Detailed notes with nose / palate / finish / overall fields, plus 1–10 rating per session
- **Barcode scanner** — UPC lookup via UPC Item DB API and Open Food Facts fallback; auto-parses whiskey type, age, ABV, region, volume
- **Admin scanner queue** — Batch scan multiple bottles, autofill from barcode, commit to cellar
- **Wish list** — Track wanted bottles with priority (Low/Medium/High), estimated price, and one-click convert-to-cellar
- **Photo management** — 2 image slots per bottle with swap support
- **Dashboard** — Summary stats (total, sealed, opened, finished, liked, buy again, wish list count) and type breakdown
- **Multi-user authentication** — Cookie-based sessions, remember-me (30 days), bcrypt passwords
- **Admin panel** — User management (create, promote, enable/disable, delete)
- **Soft delete + trash** — Restore or permanently delete bottles
- **Mark as sold** — Optional price-sold tracking
- **Proxmox LXC deployment** — `proxmox-setup.sh` supports both Docker and native Python/systemd
- **Docker Compose** — Single-command deployment with persistent data volumes
- **SQLite database** — Zero-configuration, stored in `data/cellar.db`
- **Auto schema migration** — `init_db()` adds columns to existing databases without data loss
