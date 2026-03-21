#!/usr/bin/env bash
# Roban Swarm — Create a golden OPi companion image from a working SD card.
#
# Usage (on Mac):
#   1. Insert the SD card from a fully-installed, working companion
#   2. Run:  sudo ./images/make-golden.sh /dev/rdiskN
#   3. Output: images/roban-companion-golden-YYYYMMDD.img.gz
#
# The golden image has install.sh already run (all packages, UARTs, services)
# but is NOT provisioned — the captive portal triggers on first boot so the
# user can pick a heli ID via phone/laptop.
#
# To flash a new SD card:
#   gunzip -k images/roban-companion-golden-YYYYMMDD.img.gz
#   sudo dd if=images/roban-companion-golden-YYYYMMDD.img of=/dev/rdiskN bs=4m status=progress
#
# Or use balenaEtcher / Raspberry Pi Imager (both handle .img.gz directly).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DATE=$(date +%Y%m%d)
IMG_NAME="roban-companion-golden-${DATE}.img"
IMG_PATH="${SCRIPT_DIR}/${IMG_NAME}"

# --- Argument: source disk ---
if [ $# -lt 1 ]; then
    echo "Usage: sudo $0 /dev/rdiskN"
    echo
    echo "Available disks:"
    diskutil list | grep -E '(external|/dev/disk)' || true
    echo
    echo "Pick the SD card disk (use /dev/rdiskN for raw speed)."
    exit 1
fi

SRC_DISK="$1"

if [ "$(id -u)" -ne 0 ]; then
    echo "ERROR: Must run as root (sudo)." >&2
    exit 1
fi

if [ ! -b "$SRC_DISK" ]; then
    echo "ERROR: $SRC_DISK is not a block device." >&2
    exit 1
fi

# Safety check: don't image the boot disk
BOOT_DISK=$(diskutil info / | awk '/Part of Whole/ {print $NF}')
if echo "$SRC_DISK" | grep -q "$BOOT_DISK"; then
    echo "ERROR: $SRC_DISK appears to be your boot disk. Refusing." >&2
    exit 1
fi

echo "=== Roban Swarm — Golden Image Builder ==="
echo
echo "Source:  $SRC_DISK"
echo "Output:  ${IMG_PATH}.gz"
echo

# Get disk size for progress
DISK_SIZE=$(diskutil info "$SRC_DISK" | awk '/Disk Size/ {print $3, $4}' || echo "unknown")
echo "Disk size: $DISK_SIZE"
echo
read -p "This will read the ENTIRE SD card. Continue? [y/N] " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi

# Unmount (but don't eject) the SD card
echo "Unmounting partitions..."
diskutil unmountDisk "$SRC_DISK" || true

# Read image
echo "Reading image (this takes a few minutes)..."
dd if="$SRC_DISK" of="$IMG_PATH" bs=4m status=progress

echo "Compressing (gzip -1 for speed, still ~60-70% smaller)..."
gzip -1 "$IMG_PATH"

echo
echo "=== Done ==="
echo "Golden image: ${IMG_PATH}.gz"
echo "Size: $(du -h "${IMG_PATH}.gz" | cut -f1)"
echo
echo "Next steps:"
echo "  1. Flash to a new SD card (balenaEtcher or dd)"
echo "  2. Boot the new OPi"
echo "  3. Connect phone to 'RobanHeli-SETUP' WiFi"
echo "  4. Fill in heli ID + WiFi password in the captive portal"
echo "  5. OPi reboots into the fleet automatically"
