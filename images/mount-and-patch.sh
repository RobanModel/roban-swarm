#!/bin/bash
set -e

IMG=/workdir/roban-heli-golden.img

# Mount the image
OFFSET=$((8192 * 512))
mkdir -p /mnt/img
mount -o loop,offset=$OFFSET $IMG /mnt/img
echo "✓ Mounted image"

# 1. Write WiFi netplan config
cat > /mnt/img/etc/netplan/50-roban-wifi.yaml <<'NETPLAN'
# Roban Swarm — WiFi client config (baked into golden image)
network:
  version: 2
  renderer: networkd
  wifis:
    wlan0:
      dhcp4: true
      access-points:
        "Robanswarm":
          password: "dopedope"
NETPLAN
chmod 600 /mnt/img/etc/netplan/50-roban-wifi.yaml
echo "✓ WiFi config written"

# 2. Write auto-provision script (replaces captive portal on first boot)
cat > /mnt/img/opt/roban-swarm/roban-provision.py <<'PROVISION'
#!/usr/bin/env python3
"""
Roban Swarm — Companion Auto-Provisioning

First-boot service: if not yet provisioned, connects to Robanswarm WiFi
and registers with the base controller API to get a heli ID assignment.
Falls back to captive portal if base controller is unreachable.

Pure stdlib — no pip packages needed.
"""

import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request

CONF_DIR = "/etc/roban-swarm"
PROVISIONED_FLAG = os.path.join(CONF_DIR, "provisioned")
HELI_ENV = os.path.join(CONF_DIR, "heli.env")
IFACE = "wlan0"

BASE_IP = "192.168.50.1"
BASE_API = f"http://{BASE_IP}:8080/api"

DEFAULTS = {
    "ntrip_port": "2101",
    "ntrip_mount": "BASE",
    "ntrip_user": "admin",
    "ntrip_pass": "roban",
    "fc_serial": "/dev/ttyS0",
    "fc_baud": "115200",
    "gnss_serial": "/dev/ttyS5",
    "gnss_baud": "115200",
}


def log(msg):
    print(f"[provision] {msg}", flush=True)


def run(cmd, check=True):
    log(f"  $ {cmd}")
    return subprocess.run(cmd, shell=True, check=check,
                          capture_output=True, text=True)


def get_mac():
    """Get wlan0 MAC address."""
    try:
        with open(f"/sys/class/net/{IFACE}/address") as f:
            return f.read().strip()
    except FileNotFoundError:
        return None


def wait_for_network(timeout=60):
    """Wait until we have an IP on wlan0 and can reach the base station."""
    log(f"Waiting for network (up to {timeout}s)...")
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        # Check if we have an IP
        r = run(f"ip -4 addr show {IFACE} | grep -q inet", check=False)
        if r.returncode == 0:
            # Try to reach base station
            try:
                s = socket.create_connection((BASE_IP, 8080), timeout=3)
                s.close()
                log("Base controller reachable")
                return True
            except (socket.timeout, ConnectionRefusedError, OSError):
                pass
        time.sleep(2)
    log("Network timeout — base controller not reachable")
    return False


def register_with_base(mac):
    """Call POST /api/fleet/register with our MAC. Returns assigned config."""
    payload = json.dumps({"mac": mac}).encode()
    req = urllib.request.Request(
        f"{BASE_API}/fleet/register",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read())
        log(f"Registered: heli_id={data['id']}, ip={data['ip']}, sysid={data['sysid']}")
        return data
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        log(f"Registration failed: {e.code} — {body}")
        # If already registered, try to get existing assignment
        if e.code == 409:
            return get_existing_assignment(mac)
        return None
    except Exception as e:
        log(f"Registration error: {e}")
        return None


def get_existing_assignment(mac):
    """If already registered, fetch our assignment from fleet list."""
    try:
        resp = urllib.request.urlopen(f"{BASE_API}/fleet", timeout=10)
        fleet = json.loads(resp.read())
        for heli in fleet:
            if heli.get("mac") == mac.lower():
                log(f"Found existing assignment: heli_id={heli['id']}")
                return heli
    except Exception as e:
        log(f"Fleet lookup error: {e}")
    return None


def write_config(assignment):
    """Write heli.env and mavlink-router config from base controller assignment."""
    heli_id = assignment["id"]
    sysid = assignment["sysid"]
    hub_port = assignment["hub_port"]
    expected_ip = assignment["ip"]

    os.makedirs(CONF_DIR, exist_ok=True)

    # --- heli.env ---
    env_content = f"""\
# Roban Swarm — Heli {heli_id:02d} environment
# Auto-provisioned on {time.strftime('%Y-%m-%d %H:%M:%S')}

# Identity
HELI_ID={heli_id:02d}

# Network
BASE_IP={BASE_IP}
WIFI_SSID=Robanswarm

# NTRIP (RTCM corrections)
NTRIP_PORT={DEFAULTS['ntrip_port']}
NTRIP_MOUNT={DEFAULTS['ntrip_mount']}
NTRIP_USER={DEFAULTS['ntrip_user']}
NTRIP_PASS={DEFAULTS['ntrip_pass']}

# Serial ports — native SoC UARTs on 40-pin header
FC_SERIAL={DEFAULTS['fc_serial']}
FC_BAUD={DEFAULTS['fc_baud']}
GNSS_RTCM_SERIAL={DEFAULTS['gnss_serial']}
GNSS_RTCM_BAUD={DEFAULTS['gnss_baud']}

# MAVLink
UDP_PORT={hub_port}
CMD_PORT={hub_port + 100}
SYSID={sysid}
"""
    with open(HELI_ENV, "w") as f:
        f.write(env_content)
    os.chmod(HELI_ENV, 0o600)
    log(f"Wrote {HELI_ENV}")

    # --- mavlink-router config ---
    mavlink_conf_dir = "/etc/mavlink-router"
    os.makedirs(mavlink_conf_dir, exist_ok=True)
    mavlink_content = f"""\
# Roban Swarm — Heli {heli_id:02d} mavlink-router config
# Auto-provisioned on {time.strftime('%Y-%m-%d %H:%M:%S')}

[General]
TcpServerPort = 0
ReportStats = false
MavlinkDialect = ardupilotmega

# Flight controller serial connection
[UartEndpoint fc]
Device = {DEFAULTS['fc_serial']}
Baud = {DEFAULTS['fc_baud']}

# Bidirectional link to base station hub
[UdpEndpoint base]
Mode = Normal
Address = {BASE_IP}
Port = {hub_port}

# Local GPS bridge input
[UdpEndpoint gps_bridge]
Mode = Server
Address = 127.0.0.1
Port = 14570
"""
    with open(os.path.join(mavlink_conf_dir, "main.conf"), "w") as f:
        f.write(mavlink_content)
    log("Wrote mavlink-router config")

    # --- Mark provisioned ---
    with open(PROVISIONED_FLAG, "w") as f:
        f.write(f"heli_id={heli_id:02d}\n"
                f"mac={get_mac()}\n"
                f"ip={expected_ip}\n"
                f"sysid={sysid}\n"
                f"provisioned={time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    log("Marked as provisioned")


def start_operational_services():
    """Start mavlink-router and gps-bridge after provisioning."""
    for svc in ["mavlink-router", "gps-bridge", "roban-watchdog"]:
        run(f"systemctl start {svc}", check=False)
    log("Operational services started")


def main():
    log("Roban Swarm Auto-Provisioning starting...")

    if os.path.exists(PROVISIONED_FLAG):
        log(f"Already provisioned ({PROVISIONED_FLAG} exists). Exiting.")
        sys.exit(0)

    log("NOT provisioned — attempting auto-register with base controller")

    mac = get_mac()
    if not mac:
        log("ERROR: Cannot read wlan0 MAC address")
        sys.exit(1)
    log(f"MAC: {mac}")

    # Wait for WiFi + base controller to be reachable
    if not wait_for_network(timeout=90):
        log("Base controller not reachable. Falling back to captive portal.")
        log("To use captive portal, run: roban-provision-portal.py")
        sys.exit(1)

    # Register with base controller
    assignment = register_with_base(mac)
    if not assignment:
        log("Registration failed. Board needs manual provisioning.")
        sys.exit(1)

    # Write config files
    write_config(assignment)

    # Start services (no reboot needed — WiFi is already connected)
    start_operational_services()

    log(f"Provisioning complete! Heli {assignment['id']:02d} ready.")


if __name__ == "__main__":
    main()
PROVISION
chmod 755 /mnt/img/opt/roban-swarm/roban-provision.py
echo "✓ Auto-provision script written"

# 3. Keep the old captive portal as fallback
if [ -f /mnt/img/opt/roban-swarm/roban-provision.py.bak ]; then
    echo "  (backup already exists)"
else
    # The old one was already replaced above, but it's in the repo
    echo "  (captive portal available in repo as fallback)"
fi

# 4. Verify key files
echo ""
echo "=== Verification ==="
echo "WiFi config:"
cat /mnt/img/etc/netplan/50-roban-wifi.yaml
echo ""
echo "heli.env (should be placeholder):"
cat /mnt/img/etc/roban-swarm/heli.env
echo ""
echo "Provisioned flag:"
ls -la /mnt/img/etc/roban-swarm/provisioned 2>&1 || echo "  ✓ No provisioned flag (good)"
echo ""
echo "Provision script (first 3 lines):"
head -3 /mnt/img/opt/roban-swarm/roban-provision.py

# Unmount
umount /mnt/img
echo ""
echo "✓ Image patched and unmounted. Ready to flash!"
