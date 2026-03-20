"""Flight daemon skeleton — reads a show file and streams SET_POSITION_TARGET_LOCAL_NED.

This is the "CNC G-code executor" for the swarm: it interpolates between
waypoints and sends position+velocity targets to each heli at 10-20 Hz via
MAVLink SET_POSITION_TARGET_LOCAL_NED in GUIDED mode.

Current status: SKELETON — trajectory interpolation and MAVLink output
are stubbed. The structure is in place for Phase 3+ implementation.
"""

import asyncio
import json
import logging
import time
from enum import Enum
from pathlib import Path

from pymavlink.dialects.v20 import ardupilotmega as mav

from .show_format import ShowFile, HeliTrack, Vec3

log = logging.getLogger("roban.flight")


class DaemonState(str, Enum):
    IDLE = "idle"
    LOADED = "loaded"       # show file parsed, ready to arm
    ARMED = "armed"         # pre-flight checks passed, waiting for GO
    RUNNING = "running"     # streaming position targets
    PAUSED = "paused"       # temporarily halted (hold position)
    DONE = "done"           # show complete
    ERROR = "error"


class FlightDaemon:
    """Manages show playback for the swarm.

    Lifecycle:
        load(path)  → LOADED
        arm()       → ARMED  (pre-flight checks: all helis online, GPS fix, GUIDED mode)
        go()        → RUNNING (starts streaming targets)
        pause()     → PAUSED (hold current position)
        resume()    → RUNNING
        stop()      → IDLE   (emergency stop, sends BRAKE/LOITER)
    """

    def __init__(self, tracker=None):
        """
        Args:
            tracker: VehicleTracker instance for live vehicle state.
        """
        self._tracker = tracker
        self._show: ShowFile | None = None
        self._state = DaemonState.IDLE
        self._task: asyncio.Task | None = None
        self._start_time: float = 0.0
        self._pause_offset: float = 0.0

    @property
    def state(self) -> DaemonState:
        return self._state

    @property
    def show(self) -> ShowFile | None:
        return self._show

    @property
    def elapsed_s(self) -> float:
        if self._state == DaemonState.RUNNING:
            return time.monotonic() - self._start_time - self._pause_offset
        return 0.0

    def load(self, path: str | Path) -> list[str]:
        """Load and validate a show file. Returns list of errors (empty = ok)."""
        path = Path(path)
        data = json.loads(path.read_text())
        show = ShowFile(**data)
        errors = show.validate_timing()
        if errors:
            self._state = DaemonState.ERROR
            return errors
        self._show = show
        self._state = DaemonState.LOADED
        log.info("Show '%s' loaded: %d tracks, %.1fs duration",
                 show.name, len(show.tracks), show.duration_s)
        return []

    async def arm(self) -> list[str]:
        """Pre-flight checks. Returns list of failures (empty = ok)."""
        if self._state != DaemonState.LOADED:
            return [f"Cannot arm in state {self._state}"]
        if not self._show:
            return ["No show loaded"]

        failures = []
        if not self._tracker:
            failures.append("No vehicle tracker available")
            return failures

        for track in self._show.tracks:
            sysid = 10 + track.heli_id  # fleet convention
            v = self._tracker.get(sysid)
            if v is None:
                failures.append(f"Heli {track.heli_id} (sysid {sysid}): not seen")
            elif not v["online"]:
                failures.append(f"Heli {track.heli_id}: offline")
            elif v["gps_fix"] < 3:
                failures.append(f"Heli {track.heli_id}: no GPS fix (fix={v['gps_fix']})")

        if not failures:
            self._state = DaemonState.ARMED
            log.info("Show armed — all %d helis ready", len(self._show.tracks))
        return failures

    async def go(self):
        """Start show playback."""
        if self._state != DaemonState.ARMED:
            raise RuntimeError(f"Cannot start in state {self._state}")
        self._state = DaemonState.RUNNING
        self._start_time = time.monotonic()
        self._pause_offset = 0.0
        self._task = asyncio.create_task(self._playback_loop())
        log.info("Show STARTED")

    async def pause(self):
        """Pause playback — all helis hold current position."""
        if self._state != DaemonState.RUNNING:
            return
        self._state = DaemonState.PAUSED
        self._pause_offset += time.monotonic() - self._start_time
        log.info("Show PAUSED at %.1fs", self.elapsed_s)
        # TODO: send BRAKE or hold-position to all helis

    async def resume(self):
        """Resume from pause."""
        if self._state != DaemonState.PAUSED:
            return
        self._start_time = time.monotonic()
        self._state = DaemonState.RUNNING
        log.info("Show RESUMED")

    async def stop(self):
        """Emergency stop — cancel playback, command BRAKE/LOITER."""
        prev = self._state
        self._state = DaemonState.IDLE
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        log.warning("Show STOPPED from state %s", prev)
        # TODO: send BRAKE/LOITER to all helis

    async def _playback_loop(self):
        """Main playback loop — interpolate and stream targets at ~20 Hz."""
        try:
            while self._state == DaemonState.RUNNING:
                t = self.elapsed_s

                if t >= self._show.duration_s:
                    self._state = DaemonState.DONE
                    log.info("Show COMPLETE (%.1fs)", t)
                    break

                # --- Interpolate and send targets ---
                for track in self._show.tracks:
                    target = self._interpolate(track, t)
                    if target:
                        await self._send_target(track.heli_id, target)

                await asyncio.sleep(0.05)  # 20 Hz

        except asyncio.CancelledError:
            pass

    def _interpolate(self, track: HeliTrack, t: float) -> dict | None:
        """Linear interpolation between surrounding waypoints.

        TODO: Replace with jerk-limited trajectory (Ruckig or CatmullRom spline).
        """
        wps = track.waypoints

        # Find surrounding waypoints
        if t <= wps[0].t:
            return {"pos": wps[0].pos, "vel": Vec3(n=0, e=0, d=0)}

        for i in range(len(wps) - 1):
            if wps[i].t <= t <= wps[i + 1].t:
                # Handle hold time
                if wps[i].hold_s > 0 and t <= wps[i].t + wps[i].hold_s:
                    return {"pos": wps[i].pos, "vel": Vec3(n=0, e=0, d=0)}

                # Linear interpolation
                dt = wps[i + 1].t - wps[i].t
                if dt <= 0:
                    return {"pos": wps[i + 1].pos, "vel": Vec3(n=0, e=0, d=0)}
                frac = (t - wps[i].t) / dt
                p0, p1 = wps[i].pos, wps[i + 1].pos
                pos = Vec3(
                    n=p0.n + (p1.n - p0.n) * frac,
                    e=p0.e + (p1.e - p0.e) * frac,
                    d=p0.d + (p1.d - p0.d) * frac,
                )
                vel = Vec3(
                    n=(p1.n - p0.n) / dt,
                    e=(p1.e - p0.e) / dt,
                    d=(p1.d - p0.d) / dt,
                )
                return {"pos": pos, "vel": vel}

        # Past last waypoint — hold final position
        return {"pos": wps[-1].pos, "vel": Vec3(n=0, e=0, d=0)}

    async def _send_target(self, heli_id: int, target: dict):
        """Send SET_POSITION_TARGET_LOCAL_NED to a heli.

        TODO: Implement actual MAVLink send via mavlink-hub UDP.
        Currently a no-op skeleton.
        """
        # Will use: mavutil connection per heli → SET_POSITION_TARGET_LOCAL_NED
        # with type_mask selecting position + velocity, NED frame
        # sysid = 10 + heli_id, target component = 1
        pass
