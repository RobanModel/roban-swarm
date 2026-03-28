#!/usr/bin/env bash
# Roban Swarm — Stop all SITL heli instances.

set -euo pipefail

echo "=== Stopping SITL helis ==="
pkill -f "arducopter-sitl" 2>/dev/null || true
rm -rf /tmp/sitl

# Remove SITL endpoints from mavlink-hub config
HUBCONF="/etc/mavlink-router/main.conf"
sudo sed -i '/# --- SITL START ---/,/# --- SITL END ---/d' "$HUBCONF"
sudo systemctl restart mavlink-hub
sleep 1

echo "=== SITL stopped, mavlink-hub cleaned ==="
