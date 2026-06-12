#!/usr/bin/env bash
# Scotch & Bourbon — Proxmox LXC setup & update script
# Runs on an unprivileged Debian/Ubuntu LXC container as root.
# Safe to re-run: detects first-time install vs. update automatically.

set -euo pipefail

APP_DIR="/opt/scotch-and-bourbon"
APP_PORT="8000"
APP_USER="cellar"
SERVICE="scotch-and-bourbon"

echo "==> Scotch & Bourbon"
echo "    App directory : $APP_DIR"
echo "    Port          : $APP_PORT"
echo "    Service       : $SERVICE"
echo ""

# ── Detect mode ────────────────────────────────────────────────────────────────
if systemctl is-active --quiet "$SERVICE" 2>/dev/null || systemctl is-enabled --quiet "$SERVICE" 2>/dev/null; then
  MODE="update"
else
  MODE="install"
fi
echo "==> Mode: $MODE"
echo ""

# ── System packages ────────────────────────────────────────────────────────────
# gcc, python3-dev, libffi-dev are required to build bcrypt's C extension
# when no prebuilt wheel is available for this platform.
echo "==> Installing system packages…"
apt-get update -qq
apt-get install -y -qq python3 python3-pip python3-venv git gcc python3-dev libffi-dev

# ── First-time install only ────────────────────────────────────────────────────
if [ "$MODE" = "install" ]; then
  echo "==> Creating app user '$APP_USER'…"
  id "$APP_USER" &>/dev/null || useradd -r -s /bin/bash -m -d "/home/$APP_USER" "$APP_USER"

  echo "==> Creating directory structure…"
  mkdir -p "$APP_DIR"/{data,static/uploads}
fi

# ── Code ───────────────────────────────────────────────────────────────────────
if [ -d "$APP_DIR/.git" ]; then
  echo "==> Pulling latest code…"
  git -C "$APP_DIR" pull
else
  if [ ! -f "$APP_DIR/main.py" ]; then
    echo ""
    echo "ERROR: No application files found in $APP_DIR."
    echo "       Copy them first, then re-run this script:"
    echo "       rsync -av /path/to/scotch-and-bourbon/ $APP_DIR/"
    exit 1
  fi
  echo "==> Application files found (no git repo — skipping pull)."
fi

# ── Python virtual environment & dependencies ──────────────────────────────────
echo "==> Creating/updating Python virtual environment…"
python3 -m venv "$APP_DIR/.venv"

echo "==> Upgrading pip…"
"$APP_DIR/.venv/bin/pip" install --upgrade pip

echo "==> Installing dependencies…"
"$APP_DIR/.venv/bin/pip" install -r "$APP_DIR/requirements.txt"

# ── Verify the install worked before touching the service ──────────────────────
if [ ! -x "$APP_DIR/.venv/bin/uvicorn" ]; then
  echo ""
  echo "ERROR: uvicorn was not installed correctly."
  echo "       Check the pip output above for errors."
  exit 1
fi
echo "==> uvicorn found at $APP_DIR/.venv/bin/uvicorn — OK"

# ── File ownership ─────────────────────────────────────────────────────────────
chown -R "$APP_USER:$APP_USER" "$APP_DIR"

# ── systemd service ────────────────────────────────────────────────────────────
if [ "$MODE" = "install" ]; then
  echo "==> Creating systemd service…"
  cat > /etc/systemd/system/${SERVICE}.service << EOF
[Unit]
Description=Scotch & Bourbon Whiskey Cellar
After=network.target

[Service]
Type=simple
User=$APP_USER
WorkingDirectory=$APP_DIR
ExecStart=$APP_DIR/.venv/bin/uvicorn main:app --host 0.0.0.0 --port $APP_PORT
Restart=on-failure
RestartSec=5
Environment=TZ=America/Chicago

[Install]
WantedBy=multi-user.target
EOF
  systemctl daemon-reload
  systemctl enable --now "$SERVICE"
  echo ""
  echo "✅  Installed and running at http://$(hostname -I | awk '{print $1}'):$APP_PORT"
  echo ""
  echo "    First run : visit /setup to create your admin account"
else
  echo "==> Restarting service…"
  systemctl daemon-reload
  systemctl restart "$SERVICE"
  echo ""
  echo "✅  Updated and restarted at http://$(hostname -I | awk '{print $1}'):$APP_PORT"
fi

echo ""
echo "    Logs    : journalctl -u $SERVICE -f"
echo "    Status  : systemctl status $SERVICE"
echo "    Update  : bash $APP_DIR/proxmox-setup.sh"
