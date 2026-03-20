"""Async MAVLink client — connects to mavlink-hub TCP 5760, dispatches messages."""

import asyncio
import logging
from pymavlink import mavutil

log = logging.getLogger("roban.mavlink")

# Messages we care about
_WANTED = {
    "HEARTBEAT", "GPS_RAW_INT", "SYS_STATUS", "ATTITUDE",
    "GLOBAL_POSITION_INT", "VFR_HUD", "BATTERY_STATUS",
}


class HubClient:
    """Reads MAVLink from mavlink-hub and feeds parsed messages to a callback.

    Runs in a background thread (pymavlink is blocking) and posts results
    back to the asyncio event loop via call_soon_threadsafe.
    """

    def __init__(self, hub_addr: str = "127.0.0.1:5760",
                 on_message=None):
        self._hub_addr = hub_addr
        self._on_message = on_message  # async callable(sysid, msg_type, fields)
        self._conn = None
        self._task: asyncio.Task | None = None
        self._running = False

    async def start(self):
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        log.info("HubClient starting — target %s", self._hub_addr)

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        if self._conn:
            self._conn.close()
        log.info("HubClient stopped")

    async def _run_loop(self):
        """Reconnect loop — keeps retrying on connection loss."""
        while self._running:
            try:
                await self._connect_and_read()
            except asyncio.CancelledError:
                break
            except Exception as e:
                log.warning("HubClient connection lost: %s — retrying in 3s", e)
                await asyncio.sleep(3)

    async def _connect_and_read(self):
        """Connect to mavlink-hub and read messages in a thread."""
        loop = asyncio.get_running_loop()

        # pymavlink connect is blocking — run in thread
        self._conn = await loop.run_in_executor(
            None, lambda: mavutil.mavlink_connection(
                f"tcp:{self._hub_addr}", source_system=250, source_component=191,
                retries=1, timeout=5,
            )
        )
        log.info("Connected to mavlink-hub at %s", self._hub_addr)

        while self._running:
            # recv_match is blocking — run in thread with short timeout
            msg = await loop.run_in_executor(
                None, lambda: self._conn.recv_match(blocking=True, timeout=1.0)
            )
            if msg is None:
                continue

            msg_type = msg.get_type()
            if msg_type == "BAD_DATA" or msg_type not in _WANTED:
                continue

            sysid = msg.get_srcSystem()
            fields = self._extract(msg_type, msg)
            if fields and self._on_message:
                # Fire-and-forget into the event loop
                asyncio.ensure_future(self._on_message(sysid, msg_type, fields))

    @staticmethod
    def _extract(msg_type: str, msg) -> dict | None:
        """Pull the fields we need from each message type."""
        if msg_type == "HEARTBEAT":
            from pymavlink.dialects.v20 import ardupilotmega as apm
            return {
                "armed": bool(msg.base_mode & apm.MAV_MODE_FLAG_SAFETY_ARMED),
                "flight_mode": msg.custom_mode,
                "mav_type": msg.type,
                "system_status": msg.system_status,
            }
        if msg_type == "GPS_RAW_INT":
            return {
                "fix_type": msg.fix_type,
                "lat": msg.lat / 1e7,
                "lon": msg.lon / 1e7,
                "alt_m": msg.alt / 1e3,
                "satellites": msg.satellites_visible,
                "hdop": msg.eph / 100.0 if msg.eph != 65535 else None,
            }
        if msg_type == "SYS_STATUS":
            return {
                "battery_mv": msg.voltage_battery,
                "battery_pct": msg.battery_remaining if msg.battery_remaining >= 0 else None,
                "sensors_present": msg.onboard_control_sensors_present,
                "sensors_health": msg.onboard_control_sensors_health,
            }
        if msg_type == "ATTITUDE":
            return {
                "roll_deg": round(msg.roll * 57.2958, 1),
                "pitch_deg": round(msg.pitch * 57.2958, 1),
                "yaw_deg": round(msg.yaw * 57.2958, 1),
            }
        if msg_type == "GLOBAL_POSITION_INT":
            return {
                "lat": msg.lat / 1e7,
                "lon": msg.lon / 1e7,
                "alt_m": msg.alt / 1e3,
                "relative_alt_m": msg.relative_alt / 1e3,
                "heading_deg": msg.hdg / 100.0 if msg.hdg != 65535 else None,
            }
        if msg_type == "VFR_HUD":
            return {
                "airspeed": msg.airspeed,
                "groundspeed": msg.groundspeed,
                "heading_deg": msg.heading,
                "throttle_pct": msg.throttle,
                "climb_rate": msg.climb,
            }
        if msg_type == "BATTERY_STATUS":
            return {
                "battery_pct": msg.battery_remaining if msg.battery_remaining >= 0 else None,
                "battery_mv": msg.voltages[0] if msg.voltages[0] != 65535 else None,
                "current_ma": msg.current_battery if msg.current_battery >= 0 else None,
            }
        return None
