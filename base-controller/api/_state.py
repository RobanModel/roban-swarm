"""Shared state accessors for API routers.

The flight daemon and other singletons are created in main.py's lifespan
and registered here so API routers can access them without circular imports.
"""

_daemon = None
_tracker = None
_sim_mode = False
SIM_SYSID_OFFSET = 100  # sim sysid = real sysid + 100


def set_daemon(daemon):
    global _daemon
    _daemon = daemon


def get_daemon():
    if _daemon is None:
        raise RuntimeError("Flight daemon not initialized")
    return _daemon


def set_tracker(tracker):
    global _tracker
    _tracker = tracker


def get_tracker():
    return _tracker


def set_sim_mode(enabled: bool):
    global _sim_mode
    _sim_mode = enabled


def is_sim_mode() -> bool:
    return _sim_mode


def get_sysid_offset() -> int:
    """Returns 100 in sim mode, 0 in real mode."""
    return SIM_SYSID_OFFSET if _sim_mode else 0
