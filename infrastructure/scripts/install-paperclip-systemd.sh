#!/bin/bash
# ==============================================================================
# Henko Sys x01 — Install Paperclip as systemd service in WSL2 Ubuntu
# ==============================================================================
# Makes Paperclip auto-start when WSL2 Ubuntu boots, so you don't lose
# the API after machine restarts or `wsl --shutdown`.
#
# Run as root:
#   wsl -d Ubuntu -- bash /mnt/c/Users/Daniel\ Amer/henko-sys-x01/infrastructure/scripts/install-paperclip-systemd.sh
# ==============================================================================
set -e

if [ "$EUID" -ne 0 ]; then
  echo "❌ Run as root (needed to write to /etc/systemd/system/)"
  echo "   wsl -d Ubuntu -- bash $(realpath "$0")"
  exit 1
fi

DANIEL_HOME="/home/daniel"
NPX_BIN=$(su - daniel -c 'which npx')

if [ -z "$NPX_BIN" ]; then
  echo "❌ npx not found for daniel user"
  exit 1
fi

echo "📦 Installing Paperclip systemd service..."
echo "  npx: $NPX_BIN"
echo "  user home: $DANIEL_HOME"

cat > /etc/systemd/system/henko-paperclip.service << EOF
[Unit]
Description=Henko Sys x01 — Paperclip AI Company OS
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=daniel
Group=daniel
WorkingDirectory=$DANIEL_HOME
Environment="HOME=$DANIEL_HOME"
Environment="PATH=$DANIEL_HOME/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart=$NPX_BIN paperclipai run
Restart=on-failure
RestartSec=10
StandardOutput=append:/var/log/henko-paperclip.log
StandardError=append:/var/log/henko-paperclip.err

[Install]
WantedBy=multi-user.target
EOF

# Ensure log files exist with right perms
touch /var/log/henko-paperclip.log /var/log/henko-paperclip.err
chown daniel:daniel /var/log/henko-paperclip.log /var/log/henko-paperclip.err

systemctl daemon-reload
systemctl enable henko-paperclip.service

echo "✓ Service installed: henko-paperclip.service"
echo ""
echo "Commands:"
echo "  systemctl start henko-paperclip      # Start now"
echo "  systemctl status henko-paperclip     # Check status"
echo "  systemctl stop henko-paperclip       # Stop"
echo "  journalctl -u henko-paperclip -f     # Tail logs"
echo "  tail -f /var/log/henko-paperclip.log # Tail stdout"
