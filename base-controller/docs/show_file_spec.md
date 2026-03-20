# Roban Swarm — Show File Specification (v1)

## Overview

A **show file** is a JSON document that describes a timed drone swarm
choreography. It contains per-helicopter flight style parameters and
ordered waypoint sequences. The flight daemon reads the show file and
streams `SET_POSITION_TARGET_LOCAL_NED` to each heli at 10-20 Hz.

## Coordinate System

- **NED (North-East-Down)** relative to the show's home position
- Positions in **meters**
- Down is positive → altitude above home is **negative D**
- Home position is defined by `home_lat`, `home_lon`, `home_alt_m`

## Schema

```json
{
  "name": "Demo Figure-8",
  "version": 1,
  "home_lat": 23.12345,
  "home_lon": 113.54321,
  "home_alt_m": 45.0,
  "duration_s": 120.0,
  "tracks": [
    {
      "heli_id": 1,
      "style": {
        "max_speed": 5.0,
        "max_accel": 2.0,
        "max_jerk": 5.0,
        "angle_max_deg": 30.0,
        "corner_radius": 2.0
      },
      "waypoints": [
        { "t": 0,   "pos": { "n": 0, "e": 0, "d": -10 } },
        { "t": 15,  "pos": { "n": 20, "e": 10, "d": -10 }, "vel": { "n": 2, "e": 1, "d": 0 } },
        { "t": 30,  "pos": { "n": 0, "e": 0, "d": -10 }, "hold_s": 5 }
      ]
    }
  ]
}
```

## Field Reference

### Top-level

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | yes | Show name |
| `version` | int | yes | Schema version (currently `1`) |
| `home_lat` | float | yes | Home latitude (decimal degrees) |
| `home_lon` | float | yes | Home longitude (decimal degrees) |
| `home_alt_m` | float | no | Home altitude AMSL (m), default 0 |
| `duration_s` | float | yes | Total show duration in seconds |
| `tracks` | array | yes | One entry per participating heli |

### HeliTrack

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `heli_id` | int (1-99) | yes | Fleet heli ID |
| `style` | HeliStyle | no | Flight dynamics constraints (defaults apply) |
| `waypoints` | array | yes | Ordered timed waypoints (min 1) |

### HeliStyle (per-heli flight constraints)

| Field | Default | Description |
|-------|---------|-------------|
| `max_speed` | 5.0 | Max ground speed (m/s) |
| `max_accel` | 2.0 | Max acceleration (m/s^2) |
| `max_jerk` | 5.0 | Max jerk (m/s^3) |
| `angle_max_deg` | 30.0 | Max lean angle (degrees, 1-60) |
| `corner_radius` | 2.0 | Min turning radius (m), 0 = sharp |

These constrain the trajectory planner, not ArduPilot directly.
`angle_max_deg` maps to ArduPilot's `ANGLE_MAX` parameter at upload time.

### Waypoint

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `t` | float | yes | Time from show start (seconds) |
| `pos` | Vec3 | yes | Target position (NED meters from home) |
| `vel` | Vec3 | no | Velocity hint (m/s) for smooth passing |
| `hold_s` | float | no | Hold at position for N seconds, default 0 |

### Vec3

| Field | Type | Description |
|-------|------|-------------|
| `n` | float | North (meters) |
| `e` | float | East (meters) |
| `d` | float | Down (meters), negative = above home |

## Flight Daemon Behavior

1. **Load** — parse + validate show file (timing, ranges)
2. **Arm** — pre-flight checks: all helis online, GPS fix >= 3D, GUIDED mode
3. **Go** — start streaming `SET_POSITION_TARGET_LOCAL_NED` at 20 Hz
4. **Interpolation** — linear lerp between waypoints (future: jerk-limited via Ruckig)
5. **Hold** — `hold_s > 0` pauses at waypoint with zero velocity
6. **Velocity hints** — `vel` on a waypoint helps the trajectory planner create smooth arcs
7. **Done** — after `duration_s`, hold final positions

## MAVLink Output

Each target is sent as `SET_POSITION_TARGET_LOCAL_NED`:
- Frame: `MAV_FRAME_LOCAL_NED`
- Type mask: position + velocity (ignore acceleration/yaw)
- Yaw: not set → ArduPilot auto-faces direction of travel
- Target system: `10 + heli_id`, component 1

## Validation Rules

- All waypoint times must be monotonically increasing per track
- All waypoint times must be <= `duration_s`
- `heli_id` must match a registered fleet member
- At least one waypoint per track
