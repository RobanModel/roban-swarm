#!/usr/bin/env bash
# Roban Swarm — Prepare a working companion for golden image cloning.
#
# Run this ON the OPi (via SSH) BEFORE pulling the SD card to clone.
# It strips the identity so the captive portal triggers on next boot.
#
# Usage:
#   sudo ./images/prep-for-clone.sh
#   # Then: power off, pull SD card, clone on Mac with make-golden.sh
#
# What it does:
#   - Removes /etc/roban-swarm/provisioned flag
#   - Clears heli identity from heli.env (sets HELI_ID=XX placeholder)
#   - Removes WiFi client config (so captive portal AP starts instead)
#   - Clears mavlink-router config (regenerated on provision)
#   - Clears DHCP leases and machine-id (so each clone gets unique ID)
#   - Clears logs and bash history
#   - Does NOT uninstall packages or services (that's the point)
#
# After cloning, restore Heli01 with:
#   sudo /opt/roban-swarm/set_heli_id.sh 01

set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
    echo "ERROR: Must run as root (sudo)." >&2
    exit 1
fi

echo "=== Roban Swarm — Prepare for Golden Image ==="
echo
echo "This will strip the heli identity and WiFi config."
echo "After cloning, restore this board with: set_heli_id.sh 01"
echo
read -p "Continue? [y/N] " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 0
fi

# 1. Remove provisioned flag — captive portal will start on next boot
echo "[1/7] Removing provisioned flag..."
rm -f /etc/roban-swarm/provisioned

# 2. Reset heli.env to placeholder values
echo "[2/7] Resetting heli.env..."
if [ -f /etc/roban-swarm/heli.env ]; then
    cat > /etc/roban-swarm/heli.env <<'ENV'
# Roban Swarm companion identity — populated by captive portal or set_heli_id.sh
HELI_ID=XX
BASE_IP=192.168.50.1
WIFI_SSID=Robanswarm
NTRIP_PORT=2101
NTRIP_MOUNT=BASE
NTRIP_USER=admin
NTRIP_PASS=roban
FC_SERIAL=/dev/ttyS0
FC_BAUD=115200
GNSS_RTCM_SERIAL=/dev/ttyS5
GNSS_RTCM_BAUD=115200
UDP_PORT=0
CMD_PORT=0
SYSID=0
ENV
fi

# 3. Remove WiFi client config — captive portal will set it up
echo "[3/7] Removing WiFi client config..."
rm -f /etc/netplan/50-roban-wifi.yaml
# Keep the setup AP config if it exists
netplan generate 2>/dev/null || true

# 4. Clear mavlink-router config (regenerated on provision)
echo "[4/7] Clearing mavlink-router config..."
cat > /etc/mavlink-router/main.conf <<'MCONF'
# Placeholder — regenerated on provisioning
[General]
TcpServerPort = 0
ReportStats = false
MCONF

# 5. Reset machine-id so each clone gets a unique one
echo "[5/7] Resetting machine-id..."
echo "" > /etc/machine-id
rm -f /var/lib/dbus/machine-id 2>/dev/null || true

# 6. Clear DHCP leases and logs
echo "[6/7] Clearing leases, logs, history..."
rm -f /var/lib/dhcp/*.leases 2>/dev/null || true
rm -f /var/lib/misc/dnsmasq.leases 2>/dev/null || true
journalctl --vacuum-time=1s 2>/dev/null || true
rm -f /var/log/*.gz /var/log/*.1 2>/dev/null || true
truncate -s 0 /var/log/syslog /var/log/messages /var/log/kern.log 2>/dev/null || true

# 7. Clear bash history
echo "[7/7] Clearing shell history..."
rm -f /root/.bash_history /home/*/.bash_history 2>/dev/null || true
history -c 2>/dev/null || true

# Stop services so state is clean
echo "Stopping services..."
systemctl stop mavlink-router gps-bridge watchdog 2>/dev/null || true

echo
echo "=== Ready for cloning ==="
echo
echo "Next steps:"
echo "  1. sudo poweroff"
echo "  2. Pull SD card"
echo "  3. On Mac: sudo ./images/make-golden.sh /dev/rdiskN"
echo "  4. Put SD card back in this OPi"
echo "  5. Restore: sudo /opt/roban-swarm/set_heli_id.sh 01"
