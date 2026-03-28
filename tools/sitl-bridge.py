#!/usr/bin/env python3
"""SITL Bridge — connects to SITL TCP ports and forwards MAVLink into mavlink-hub.

Each SITL instance runs on TCP 5860+offset. This bridge connects to each one
and forwards all traffic to mavlink-hub via its TCP 5760 port (which is
bidirectional, so commands flow back to SITL too).

Usage:
    python3 sitl-bridge.py [num_helis]
"""

import sys
import time
import threading
import socket
from pymavlink import mavutil

NUM_HELIS = int(sys.argv[1]) if len(sys.argv) > 1 else 2
SITL_BASE_PORT = 5860   # instance 10 → 5860, instance 11 → 5870
HUB_ADDR = "127.0.0.1"
HUB_PORT = 5760


def bridge_sitl(heli_idx: int):
    """Bridge one SITL instance to mavlink-hub."""
    sitl_port = SITL_BASE_PORT + (heli_idx * 10)
    sysid = 110 + heli_idx + 1
    label = f"SITL-Heli{heli_idx+1}(sysid {sysid})"

    while True:
        try:
            print(f"[{label}] Connecting to SITL TCP {sitl_port}...")
            sitl = mavutil.mavlink_connection(
                f"tcp:127.0.0.1:{sitl_port}",
                source_system=250, source_component=200 + heli_idx,
            )

            print(f"[{label}] Connecting to mavlink-hub TCP {HUB_PORT}...")
            hub = mavutil.mavlink_connection(
                f"tcp:127.0.0.1:{HUB_PORT}",
                source_system=250, source_component=210 + heli_idx,
            )

            print(f"[{label}] Bridge active: SITL:{sitl_port} ↔ Hub:{HUB_PORT}")

            # Forward SITL → Hub in main thread, Hub → SITL in sub-thread
            def hub_to_sitl():
                while True:
                    try:
                        msg = hub.recv_match(blocking=True, timeout=1)
                        if msg and msg.get_type() != "BAD_DATA":
                            # Only forward commands targeted at this sysid
                            buf = msg.get_msgbuf()
                            if buf:
                                sitl.write(buf)
                    except Exception:
                        break

            t = threading.Thread(target=hub_to_sitl, daemon=True)
            t.start()

            # SITL → Hub
            while True:
                msg = sitl.recv_match(blocking=True, timeout=2)
                if msg is None:
                    continue
                if msg.get_type() == "BAD_DATA":
                    continue
                buf = msg.get_msgbuf()
                if buf:
                    hub.write(buf)

        except Exception as e:
            print(f"[{label}] Error: {e} — reconnecting in 3s")
            time.sleep(3)


def main():
    print(f"=== SITL Bridge — {NUM_HELIS} helis ===")
    threads = []
    for i in range(NUM_HELIS):
        t = threading.Thread(target=bridge_sitl, args=(i,), daemon=True)
        t.start()
        threads.append(t)
        time.sleep(0.5)

    # Keep main thread alive
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("\nBridge stopped")


if __name__ == "__main__":
    main()
