#!/usr/bin/env bash
# Roban Swarm — Start SITL heli instances
# SysID offset +100: real 11→sim 111, real 12→sim 112
# Each instance listens on TCP 5760+10*instance
set -euo pipefail

SITL_BIN="/opt/roban-swarm/arducopter-sitl"
SITL_DIR="/tmp/sitl"
HOME_LAT="23.1611"
HOME_LON="113.8822"
HOME_ALT="45"
NUM_HELIS=${1:-2}

# Kill any existing instances
pkill -f "arducopter-sitl" 2>/dev/null || true
sleep 1

# Remove old SITL endpoints from mavlink-hub (not needed with bridge)
HUBCONF="/etc/mavlink-router/main.conf"
sudo sed -i '/# --- SITL START ---/,/# --- SITL END ---/d' "$HUBCONF" 2>/dev/null || true

echo "=== Starting ${NUM_HELIS} SITL helis (sysid +100) ==="

for HELI_ID in $(seq 1 "${NUM_HELIS}"); do
    INST=$((HELI_ID + 9))      # instance 10,11,... → TCP 5860,5870 (avoid 5760 mavlink-hub)
    SYSID=$((110 + HELI_ID))  # 111, 112, ...
    HELI_DIR="${SITL_DIR}/heli${HELI_ID}"
    LOG="${SITL_DIR}/sitl-heli${HELI_ID}.log"

    rm -rf "$HELI_DIR"
    mkdir -p "$HELI_DIR"

    # Offset home position 3m east per heli
    HELI_LON=$(python3 -c "print(f'${HOME_LON} + ${INST} * 0.00003:.7f'.format())" 2>/dev/null || echo "${HOME_LON}")

    # Write per-instance defaults
    cat > "${HELI_DIR}/defaults.parm" << PARM
SYSID_THISMAV ${SYSID}
ARMING_CHECK 0
PARM

    # SITL sends MAVLink to mavlink-hub via UDP on port 14660+HELI_ID
    SITL_UDP_PORT=$((14660 + HELI_ID))
    echo "  Heli${HELI_ID}: sysid=${SYSID} → udp:127.0.0.1:${SITL_UDP_PORT}"
    cd "$HELI_DIR"
    # SITL listens on TCP 5860+(INST-10)*10 = 5860, 5870, ...
    nohup "$SITL_BIN" \
        -S \
        --model '+' \
        --wipe \
        --speedup 1 \
        --home "${HOME_LAT},${HELI_LON:-$HOME_LON},${HOME_ALT},0" \
        --instance "$INST" \
        --defaults "${HELI_DIR}/defaults.parm" \
        > "$LOG" 2>&1 &
    echo $! > "${SITL_DIR}/sitl-heli${HELI_ID}.pid"
    sleep 2
done

echo
sleep 3
echo "=== Status ==="
for HELI_ID in $(seq 1 "${NUM_HELIS}"); do
    INST=$((HELI_ID - 1))
    PID=$(cat "${SITL_DIR}/sitl-heli${HELI_ID}.pid" 2>/dev/null || echo "")
    if [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; then
        echo "  Heli${HELI_ID} (sysid $((110+HELI_ID))): RUNNING (pid $PID, tcp:$((5760+10*INST)))"
    else
        echo "  Heli${HELI_ID}: FAILED — check ${SITL_DIR}/sitl-heli${HELI_ID}.log"
    fi
done
# Add SITL TCP client endpoints to mavlink-hub config
HUBCONF="/etc/mavlink-router/main.conf"
sudo sed -i '/# --- SITL START ---/,/# --- SITL END ---/d' "$HUBCONF" 2>/dev/null || true
{
    echo ""
    echo "# --- SITL START ---"
    for HELI_ID in $(seq 1 "${NUM_HELIS}"); do
        INST=$((HELI_ID + 9))
        SITL_PORT=$((5760 + 10 * INST))
        echo "[TcpEndpoint sitl_heli${HELI_ID}]"
        echo "Address = 127.0.0.1"
        echo "Port = ${SITL_PORT}"
        echo "RetryTimeout = 3"
        echo ""
    done
    echo "# --- SITL END ---"
} | sudo tee -a "$HUBCONF" > /dev/null
sudo systemctl restart mavlink-hub
sleep 2
echo "mavlink-hub restarted with SITL TCP endpoints"
echo
echo "Stop: pkill -f arducopter-sitl && sudo bash /opt/roban-swarm/tools/stop-sitl.sh"
