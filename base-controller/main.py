"""Roban Swarm Base Controller — FastAPI application."""

import asyncio
import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles

from api.fleet import router as fleet_router
from api.mode import router as mode_router
from mavlink.vehicle_tracker import VehicleTracker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)-20s %(levelname)s  %(message)s",
)
log = logging.getLogger("roban.main")

_start_time = time.time()

# --- WebSocket manager ---
_ws_clients: set[WebSocket] = set()


async def _ws_broadcast(payload: dict):
    """Send a JSON payload to all connected WebSocket clients."""
    dead = []
    for ws in _ws_clients:
        try:
            await ws.send_json(payload)
        except Exception:
            dead.append(ws)
    for ws in dead:
        _ws_clients.discard(ws)


# --- MAVLink tracker (singleton) ---
_tracker: VehicleTracker | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    global _tracker
    _tracker = VehicleTracker(
        hub_addr="127.0.0.1:5760",
        on_update=_ws_broadcast,
    )
    await _tracker.start()
    log.info("Base controller started")
    yield
    await _tracker.stop()
    log.info("Base controller stopped")


app = FastAPI(
    title="Roban Swarm Controller",
    version="0.2.0",
    lifespan=lifespan,
)

# --- API routers ---
app.include_router(fleet_router, prefix="/api")
app.include_router(mode_router, prefix="/api")


@app.get("/api/health")
async def health():
    vehicles = _tracker.get_all() if _tracker else []
    return {
        "status": "ok",
        "uptime_s": round(time.time() - _start_time, 1),
        "version": app.version,
        "vehicles_online": sum(1 for v in vehicles if v["online"]),
        "vehicles_total": len(vehicles),
    }


@app.get("/api/vehicles")
async def list_vehicles():
    """Live telemetry snapshot for all tracked vehicles."""
    if not _tracker:
        return []
    return _tracker.get_all()


@app.websocket("/ws/telemetry")
async def ws_telemetry(websocket: WebSocket):
    """WebSocket endpoint — streams vehicle_update events to the browser."""
    await websocket.accept()
    _ws_clients.add(websocket)
    log.info("WebSocket client connected (%d total)", len(_ws_clients))
    try:
        # Send current state snapshot on connect
        if _tracker:
            for v in _tracker.get_all():
                await websocket.send_json({"type": "vehicle_update", "vehicle": v})
        # Keep alive — wait for client disconnect
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        _ws_clients.discard(websocket)
        log.info("WebSocket client disconnected (%d remaining)", len(_ws_clients))


# --- Static frontend (must be last — catches all unmatched paths) ---
app.mount("/", StaticFiles(directory="static", html=True), name="static")
