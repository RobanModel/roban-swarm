# LC29HEA Baud Rate Reconfiguration (460800 → 115200)

## Problem

The Quectel LC29HEA GNSS module ships at **460800 baud** by default.
The Orange Pi Zero 2W's H618 SoC UART has **8.5% baud rate error** at 460800,
making it unusable. All LC29HEA modules must be reconfigured to **115200 baud**
before connecting to an OPi.

## Why the OPi Can't Do This Itself

The H618 UART at 460800 corrupts both TX and RX — the OPi cannot send
commands to the LC29HEA at that baud. A USB-UART adapter (CH340, CP2102, etc.)
connected to the base station or any PC with clean 460800 support is required.

## Prerequisites

- USB-UART adapter (the base station's `/dev/ttyUSB0` is occupied by the base GNSS)
- pyserial installed: `pip install pyserial`
- Physical access to the LC29HEA module

## Wiring (temporary, for reconfiguration only)

```
USB-UART TX  →  LC29HEA RX
USB-UART RX  ←  LC29HEA TX
USB-UART GND ↔  LC29HEA GND
USB-UART VCC →  LC29HEA VCC (3.3V) — or power separately
```

## Procedure

### 1. Connect LC29HEA to base station via USB-UART

```bash
# Identify the new port (usually /dev/ttyUSB1 if base GNSS is on USB0)
ls /dev/ttyUSB*
```

### 2. Run the reconfiguration script

```bash
sudo /opt/roban-swarm/venv/bin/python3 -c "
import serial, time

PORT = '/dev/ttyUSB1'  # Adjust if different

# Open at factory default 460800
ser = serial.Serial(PORT, 460800, timeout=1)
ser.reset_input_buffer()

# Verify we see NMEA at 460800
line = ser.readline().decode(errors='replace').strip()
print(f'At 460800: {line[:60]}')
if '\$G' not in line:
    print('ERROR: No NMEA at 460800 — check wiring')
    ser.close()
    exit(1)

# Send PAIR864 baud change command
ser.write(b'\$PAIR864,0,0,115200*1B\r\n')
time.sleep(0.1)

# Immediately switch our serial to 115200
ser.baudrate = 115200
time.sleep(0.5)

# Send save command at new baud rate
ser.write(b'\$PQTMSAVEPAR*5A\r\n')
time.sleep(1)

print('Command sent. Power-cycle the LC29HEA now.')
ser.close()
"
```

### 3. Power-cycle the LC29HEA

**Critical:** Unplug the LC29HEA power (or USB) for 2 seconds, then reconnect.
The baud change only takes effect after a full power cycle.

### 4. Verify at 115200

```bash
sudo /opt/roban-swarm/venv/bin/python3 -c "
import serial, time
ser = serial.Serial('/dev/ttyUSB1', 115200, timeout=2)
ser.reset_input_buffer()
for _ in range(10):
    line = ser.readline().decode(errors='replace').strip()
    if line:
        print(line[:80])
        if 'GGA' in line:
            print('✓ LC29HEA is now at 115200!')
            break
else:
    print('✗ No NMEA at 115200 — retry from step 2')
ser.close()
"
```

### 5. Wire to OPi and test

Disconnect from USB-UART, connect to OPi UART5:

```
Pin 11 (PH2) UART5_TX → LC29HEA RX
Pin 13 (PH3) UART5_RX ← LC29HEA TX
Pin 14       GND       ↔ LC29HEA GND
```

Reboot the OPi and check gps-bridge:

```bash
journalctl -u gps-bridge -f
# Should show: gps-bridge: fix=NoFix sats=0 ... rate=9.8Hz
# (rate > 0 means NMEA is flowing at 115200)
```

## Protocol Notes

- **PAIR864** is the Airoha (MediaTek) command for UART config
- Response: `$PAIR001,864,0` means ACK success
- **$PQTMSAVEPAR** persists settings to flash
- The module ACKs the baud change but **continues outputting at the old baud**
  until power-cycled — this is normal behavior
- Do NOT use `$PQTMCFGUART` — it returns `ERROR,3` on LC29HEA
- Checksum for 115200: `$PAIR864,0,0,115200*1B`

## Batch Processing

For 10 modules, the procedure takes ~2 minutes each:
1. Plug in via USB
2. Run script
3. Power-cycle
4. Verify
5. Label and set aside

Consider doing all 10 in one batch before wiring to OPis.

## FC Parameters (after wiring LC29HEA to OPi)

The flight controller must also be configured to accept GPS data via MAVLink
from the OPi companion. **Requires custom firmware** with `AP_GPS_MAV_ENABLED 1`
(stock ArduPilot on 1MB boards has this compiled out).

### Firmware

Flash `arducopter-heli-4.6.3_with_bl.hex` (custom build with AP_GPS_MAV).
See `docs/bringup_log.md` Session 10 for details.

### Required ArduPilot Parameters

Set via Mission Planner or MAVProxy in config mode:

```
GPS1_TYPE      = 14    # MAVLink GPS — receives GPS_INPUT from gps-bridge
GPS_AUTO_CONFIG = 0    # Must be 0 for MAVLink GPS (no serial GPS to configure)
SERIAL2_PROTOCOL = 2   # MAVLink2 on TELEM port (connected to OPi UART0)
SERIAL2_BAUD   = 111   # 115200 baud (must match mavlink-router config)
SYSID_THISMAV  = N     # 11 for Heli01, 12 for Heli02, ... (10 + heli_id)
```

### Verification

After setting params and rebooting the FC:
- GPS_RAW_INT should show fix type 3+ (3D), 5 (RTK Float), or 6 (RTK Fixed)
- SYS_STATUS should show GPS bit set in `sensors_present`
- Dashboard should show green GPS status with satellite count
