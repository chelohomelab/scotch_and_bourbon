#!/usr/bin/env bash
# Scotch & Bourbon — Proxmox LXC setup script
# Run this script inside a fresh Debian/Ubuntu LXC container (as root).
# The container must be PRIVILEGED if you want Docker inside LXC.
# Alternative: run natively (no Docker) — see option 2 below.

set -euo pipefail

APP_DIR="/opt/scotch-and-bourbon"
APP_PORT="8000"
APP_USER="cellar"

echo "==> Scotch & Bourbon — LXC Setup"
echo "    Target directory: $APP_DIR"
echo "    Port: $APP_PORT"
echo ""

# ─────────────────────────────────────────────────────────────────────────────
# OPTION 1: Docker-based deployment (requires privileged LXC)
# ─────────────────────────────────────────────────────────────────────────────
install_docker() {
  echo "==> Installing Docker…"
  apt-get update -qq
  apt-get install -y -qq ca-certificates curl gnupg
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  chmod a+r /etc/apt/keyrings/docker.gpg
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
    https://download.docker.com/linux/debian $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
    > /etc/apt/sources.list.d/docker.list
  apt-get update -qq
  apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-compose-plugin
  systemctl enable --now docker
  echo "==> Docker installed."
}

deploy_docker() {
  echo "==> Cloning / updating repository…"
  if [ -d "$APP_DIR/.git" ]; then
    git -C "$APP_DIR" pull
  else
    git clone https://github.com/chelohomelab/scotch-and-bourbon "$APP_DIR" 2>/dev/null || {
      echo "NOTE: Public repo not available. Copy files manually to $APP_DIR"
      mkdir -p "$APP_DIR"
    }
  fi

  echo "==> Starting with Docker Compose…"
  cd "$APP_DIR"
  docker compose up -d --build
  echo ""
  echo "✅ Running at http://$(hostname -I | awk '{print $1}'):$APP_PORT"
  echo "   First run: visit /setup to create your admin account."
}

# ─────────────────────────────────────────────────────────────────────────────
# OPTION 2: Native Python deployment (works in unprivileged LXC)
# ─────────────────────────────────────────────────────────────────────────────
deploy_native() {
  echo "==> Installing system packages…"
  apt-get update -qq
  apt-get install -y -qq python3 python3-pip python3-venv git

  echo "==> Creating app user…"
  id "$APP_USER" &>/dev/null || useradd -r -s /bin/bash -m -d "/home/$APP_USER" "$APP_USER"

  echo "==> Setting up application directory…"
  mkdir -p "$APP_DIR"/{data,static/uploads}

  if [ -d "$APP_DIR/.git" ]; then
    git -C "$APP_DIR" pull
  else
    echo "NOTE: Copy your application files to $APP_DIR"
  fi

  echo "==> Creating Python virtual environment…"
  python3 -m venv "$APP_DIR/.venv"
  "$APP_DIR/.venv/bin/pip" install --quiet -r "$APP_DIR/requirements.txt"

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
  echo "✅ Running at http://$(hostname -I | awk '{print $1}'):$APP_PORT"
  echo "   Service: systemctl status scotch-and-bourbon"
  echo "   Logs:    journalctl -u scotch-and-bourbon -f"
  echo "   First run: visit /setup to create your admin account."
}

# ─────────────────────────────────────────────────────────────────────────────
# Menu
# ─────────────────────────────────────────────────────────────────────────────
echo "Choose deployment method:"
echo "  1) Docker (requires privileged LXC container)"
echo "  2) Native Python + systemd (works in unprivileged LXC)"
read -rp "Enter 1 or 2: " choice

case "$choice" in
  1)
    install_docker
    deploy_docker
    ;;
  2)
    deploy_native
    ;;
  *)
    echo "Invalid choice. Exiting."
    exit 1
    ;;
esac
