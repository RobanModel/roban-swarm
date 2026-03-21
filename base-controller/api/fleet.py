"""Fleet management API — HeliID / MAC / IP table CRUD."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from fleet_store import fleet_store

router = APIRouter(tags=["fleet"])


class HeliCreate(BaseModel):
    id: int = Field(..., ge=1, le=99, description="Heli ID (01-99)")
    mac: str = Field(..., pattern=r"^([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}$")
    name: Optional[str] = None


class HeliRegister(BaseModel):
    """Auto-registration request from a new companion board."""
    mac: str = Field(..., pattern=r"^([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}$")


class HeliUpdate(BaseModel):
    mac: Optional[str] = Field(None, pattern=r"^([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}$")
    name: Optional[str] = None


class HeliOut(BaseModel):
    id: int
    mac: str
    name: str
    ip: str
    sysid: int
    hub_port: int
    status: str  # "unknown" until vehicle tracker fills it in


@router.get("/fleet", response_model=list[HeliOut])
async def list_fleet():
    return fleet_store.list_all()


@router.post("/fleet", response_model=HeliOut, status_code=201)
async def add_heli(heli: HeliCreate):
    try:
        return fleet_store.add(heli.id, heli.mac, heli.name)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/fleet/{heli_id}", response_model=HeliOut)
async def get_heli(heli_id: int):
    h = fleet_store.get(heli_id)
    if not h:
        raise HTTPException(status_code=404, detail="Heli not found")
    return h


@router.put("/fleet/{heli_id}", response_model=HeliOut)
async def update_heli(heli_id: int, update: HeliUpdate):
    h = fleet_store.update(heli_id, mac=update.mac, name=update.name)
    if not h:
        raise HTTPException(status_code=404, detail="Heli not found")
    return h


@router.delete("/fleet/{heli_id}", status_code=204)
async def delete_heli(heli_id: int):
    if not fleet_store.delete(heli_id):
        raise HTTPException(status_code=404, detail="Heli not found")


@router.post("/fleet/register", response_model=HeliOut, status_code=201)
async def register_heli(reg: HeliRegister):
    """Auto-register a new companion board by MAC address.

    Called by the companion's roban-provision.py on first boot.
    Assigns the next available heli ID, registers the MAC, applies
    dnsmasq + mavlink-hub configs, and returns the full assignment.
    If the MAC is already registered, returns the existing assignment (409).
    """
    mac = reg.mac.lower()

    # Check if this MAC is already registered
    for h in fleet_store.list_all():
        if h["mac"] == mac:
            raise HTTPException(
                status_code=409,
                detail=f"MAC {mac} already registered as Heli {h['id']:02d}",
            )

    # Find next available heli ID (1-99)
    existing_ids = {h["id"] for h in fleet_store.list_all()}
    next_id = None
    for i in range(1, 100):
        if i not in existing_ids:
            next_id = i
            break
    if next_id is None:
        raise HTTPException(status_code=507, detail="Fleet full (99 helis)")

    # Register and apply configs
    result = fleet_store.add(next_id, mac, f"Heli{next_id:02d}")
    fleet_store.apply_configs()
    return result


@router.post("/fleet/apply")
async def apply_fleet():
    """Regenerate dnsmasq + mavlink-hub configs and restart services."""
    result = fleet_store.apply_configs()
    return {"status": "applied", "details": result}
