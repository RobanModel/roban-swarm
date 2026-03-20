"""Vehicle state tracker — aggregates MAVLink messages per sysid, detects online/offline."""

import asyncio
import logging
import time
from typing import Callable, Awaitable

from .hub_client import HubClient

log = logging.getLogger("roban.tracker")

# ArduCopter/Heli flight mode map (custom_mode field)
_COPTER_MODES = {
    0: "STABILIZE", 1: "ACRO", 2: "ALT_HOLD", 3: "AUTO", 4: "GUIDED",
    5: "LOITER", 6: "RTL", 7: "CIRCLE", 9: "LAND", 11: "DRIFT",
    13: "SPORT", 14: "FLIP", 15: "AUTOTUNE", 16: "POSHOLD",
    17: "BRAKE", 18: "THROW", 19: "AVOID_ADSB", 20: "GUIDED_NOGPS",
    21: "SMART_RTL", 22: "FLOWHOLD", 23: "FOLLOW", 24: "ZIGZAG",
    25: "SYSTEMID", 26: "AUTOROTATE", 27: "AUTO_RTL",
}

OFFLINE_TIMEOUT_S = 5.0  # no heartbeat for 5s → offline


class VehicleState:
    """Live state snapshot for a single vehicle."""

    __slots__ = (
        "sysid", "online", "last_heartbeat",
        "armed", "flight_mode", "flight_mode_num",
        "fix_type", "lat", "lon", "alt_m", "satellites", "hdop",
        "battery_mv", "battery_pct",
        "roll_deg", "pitch_deg", "yaw_deg",
        "groundspeed", "heading_deg", "throttle_pct", "climb_rate",
        "relative_alt_m",
    )

    def __init__(self, sysid: int):
        self.sysid = sysid
        self.online = False
        self.last_heartbeat = 0.0
        self.armed = False
        self.flight_mode = "UNKNOWN"
        self.flight_mode_num = 0
        self.fix_type = 0
        self.lat = 0.0
        self.lon = 0.0
        self.alt_m = 0.0
        self.satellites = 0
        self.hdop = None
        self.battery_mv = 0
        self.battery_pct = None
        self.roll_deg = 0.0
        self.pitch_deg = 0.0
        self.yaw_deg = 0.0
        self.groundspeed = 0.0
        self.heading_deg = 0.0
        self.throttle_pct = 0
        self.climb_rate = 0.0
        self.relative_alt_m = 0.0

    def to_dict(self) -> dict:
        return {
            "sysid": self.sysid,
            "online": self.online,
            "armed": self.armed,
            "flight_mode": self.flight_mode,
            "gps_fix": self.fix_type,
            "lat": self.lat,
            "lon": self.lon,
            "alt_m": self.alt_m,
            "sats": self.satellites,
            "hdop": self.hdop,
            "battery_mv": self.battery_mv,
            "battery_pct": self.battery_pct,
            "roll": self.roll_deg,
            "pitch": self.pitch_deg,
            "yaw": self.yaw_deg,
            "groundspeed": self.groundspeed,
            "heading": self.heading_deg,
            "throttle": self.throttle_pct,
            "climb": self.climb_rate,
            "relative_alt_m": self.relative_alt_m,
        }


class VehicleTracker:
    """Manages per-vehicle state and pushes updates to WebSocket broadcast.

    Usage:
        tracker = VehicleTracker(hub_addr="127.0.0.1:5760", on_update=ws_broadcast)
        await tracker.start()
        ...
        await tracker.stop()
    """

    def __init__(self, hub_addr: str = "127.0.0.1:5760",
                 on_update: Callable[[dict], Awaitable[None]] | None = None):
        self._vehicles: dict[int, VehicleState] = {}
        self._on_update = on_update
        self._hub = HubClient(hub_addr=hub_addr, on_message=self._on_msg)
        self._watchdog_task: asyncio.Task | None = None

    async def start(self):
        await self._hub.start()
        self._watchdog_task = asyncio.create_task(self._watchdog())
        log.info("VehicleTracker started")

    async def stop(self):
        if self._watchdog_task:
            self._watchdog_task.cancel()
            try:
                await self._watchdog_task
            except asyncio.CancelledError:
                pass
        await self._hub.stop()
        log.info("VehicleTracker stopped")

    def get_all(self) -> list[dict]:
        """Snapshot of all known vehicles."""
        return [v.to_dict() for v in self._vehicles.values()]

    def get(self, sysid: int) -> dict | None:
        v = self._vehicles.get(sysid)
        return v.to_dict() if v else None

    async def _on_msg(self, sysid: int, msg_type: str, fields: dict):
        """Called by HubClient for every relevant MAVLink message."""
        # Ignore GCS traffic (sysid 255) and our own (250)
        if sysid >= 250:
            return

        if sysid not in self._vehicles:
            self._vehicles[sysid] = VehicleState(sysid)
            log.info("New vehicle detected: sysid %d", sysid)

        v = self._vehicles[sysid]

        if msg_type == "HEARTBEAT":
            v.last_heartbeat = time.monotonic()
            v.online = True
            v.armed = fields["armed"]
            v.flight_mode_num = fields["flight_mode"]
            v.flight_mode = _COPTER_MODES.get(fields["flight_mode"], f"MODE_{fields['flight_mode']}")

        elif msg_type == "GPS_RAW_INT":
            v.fix_type = fields["fix_type"]
            v.lat = fields["lat"]
            v.lon = fields["lon"]
            v.alt_m = fields["alt_m"]
            v.satellites = fields["satellites"]
            v.hdop = fields["hdop"]

        elif msg_type == "SYS_STATUS":
            v.battery_mv = fields["battery_mv"]
            if fields["battery_pct"] is not None:
                v.battery_pct = fields["battery_pct"]

        elif msg_type == "ATTITUDE":
            v.roll_deg = fields["roll_deg"]
            v.pitch_deg = fields["pitch_deg"]
            v.yaw_deg = fields["yaw_deg"]

        elif msg_type == "GLOBAL_POSITION_INT":
            v.lat = fields["lat"]
            v.lon = fields["lon"]
            v.alt_m = fields["alt_m"]
            v.relative_alt_m = fields["relative_alt_m"]
            if fields["heading_deg"] is not None:
                v.heading_deg = fields["heading_deg"]

        elif msg_type == "VFR_HUD":
            v.groundspeed = fields["groundspeed"]
            v.heading_deg = fields["heading_deg"]
            v.throttle_pct = fields["throttle_pct"]
            v.climb_rate = fields["climb_rate"]

        elif msg_type == "BATTERY_STATUS":
            if fields["battery_pct"] is not None:
                v.battery_pct = fields["battery_pct"]
            if fields["battery_mv"] is not None:
                v.battery_mv = fields["battery_mv"]

        # Broadcast update
        if self._on_update:
            await self._on_update({
                "type": "vehicle_update",
                "vehicle": v.to_dict(),
            })

    async def _watchdog(self):
        """Periodically mark vehicles offline if no heartbeat received."""
        while True:
            await asyncio.sleep(2)
            now = time.monotonic()
            for v in self._vehicles.values():
                was_online = v.online
                v.online = (now - v.last_heartbeat) < OFFLINE_TIMEOUT_S
                if was_online and not v.online:
                    log.warning("Vehicle sysid %d went OFFLINE", v.sysid)
                    if self._on_update:
                        await self._on_update({
                            "type": "vehicle_update",
                            "vehicle": v.to_dict(),
                        })
