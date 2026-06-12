#!/usr/bin/env bash
# Scotch & Bourbon — Proxmox LXC setup (unprivileged container, native Python + systemd)
# Run as root inside a fresh Debian/Ubuntu LXC container.

set -euo pipefail

APP_DIR="/opt/scotch-and-bourbon"
APP_PORT="8000"
APP_USER="cellar"

echo "==> Scotch & Bourbon — Proxmox LXC Setup"
echo "    App directory : $APP_DIR"
echo "    Port          : $APP_PORT"
echo "    Service user  : $APP_USER"
echo ""

echo "==> Installing system packages…"
apt-get update -qq
apt-get install -y -qq python3 python3-pip python3-venv git

echo "==> Creating app user…"
id "$APP_USER" &>/dev/null || useradd -r -s /bin/bash -m -d "/home/$APP_USER" "$APP_USER"

echo "==> Setting up application directory…"
mkdir -p "$APP_DIR"/{data,static/uploads}

# If a git remote is set, pull; otherwise expect files to already be in APP_DIR
if [ -d "$APP_DIR/.git" ]; then
  echo "==> Pulling latest code…"
  git -C "$APP_DIR" pull
else
  echo "NOTE: Copy your application files to $APP_DIR before continuing."
  echo "      Example:  rsync -av /path/to/scotch-and-bourbon/ $APP_DIR/"
  echo "      Then re-run this script."
  # Still proceed to install dependencies if requirements.txt exists
fi

if [ -f "$APP_DIR/requirements.txt" ]; then
  echo "==> Installing Python dependencies…"
  python3 -m venv "$APP_DIR/.venv"
  "$APP_DIR/.venv/bin/pip" install --quiet --upgrade pip
  "$APP_DIR/.venv/bin/pip" install --quiet -r "$APP_DIR/requirements.txt"
else
  echo "WARNING: $APP_DIR/requirements.txt not found — skipping pip install."
fi

chown -R "$APP_USER:$APP_USER" "$APP_DIR"

echo "==> Creating systemd service…"
cat > /etc/systemd/system/scotch-and-bourbon.service << EOF
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
systemctl enable --now scotch-and-bourbon.service

echo ""
echo "✅  Running at http://$(hostname -I | awk '{print $1}'):$APP_PORT"
echo ""
echo "    First run : visit /setup to create your admin account"
echo "    Logs      : journalctl -u scotch-and-bourbon -f"
echo "    Restart   : systemctl restart scotch-and-bourbon"
echo "    Update    : git -C $APP_DIR pull && systemctl restart scotch-and-bourbon"
