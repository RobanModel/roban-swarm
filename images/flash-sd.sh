#!/usr/bin/env bash
# Roban Swarm — Flash a golden image to an SD card.
#
# Usage (on Mac):
#   sudo ./images/flash-sd.sh /dev/rdiskN [images/roban-companion-golden-YYYYMMDD.img.gz]
#
# If no image path given, uses the newest .img.gz in images/.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# --- Arguments ---
if [ $# -lt 1 ]; then
    echo "Usage: sudo $0 /dev/rdiskN [image.img.gz]"
    echo
    echo "Available disks:"
    diskutil list | grep -E '(external|/dev/disk)' || true
    exit 1
fi

DST_DISK="$1"

# Find image
if [ $# -ge 2 ]; then
    IMG_PATH="$2"
else
    # Find newest golden image
    IMG_PATH=$(ls -t "${SCRIPT_DIR}"/roban-companion-golden-*.img.gz 2>/dev/null | head -1)
    if [ -z "$IMG_PATH" ]; then
        echo "ERROR: No golden image found in ${SCRIPT_DIR}/" >&2
        echo "Run make-golden.sh first." >&2
        exit 1
    fi
fi

if [ "$(id -u)" -ne 0 ]; then
    echo "ERROR: Must run as root (sudo)." >&2
    exit 1
fi

if [ ! -b "$DST_DISK" ]; then
    echo "ERROR: $DST_DISK is not a block device." >&2
    exit 1
fi

if [ ! -f "$IMG_PATH" ]; then
    echo "ERROR: Image not found: $IMG_PATH" >&2
    exit 1
fi

# Safety: don't write to boot disk
BOOT_DISK=$(diskutil info / | awk '/Part of Whole/ {print $NF}')
if echo "$DST_DISK" | grep -q "$BOOT_DISK"; then
    echo "ERROR: $DST_DISK appears to be your boot disk. Refusing." >&2
    exit 1
fi

echo "=== Roban Swarm — SD Card Flasher ==="
echo
echo "Image:  $IMG_PATH ($(du -h "$IMG_PATH" | cut -f1))"
echo "Target: $DST_DISK"
echo
read -p "This will ERASE the SD card. Continue? [y/N] " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi

echo "Unmounting..."
diskutil unmountDisk "$DST_DISK" || true

echo "Flashing (this takes a few minutes)..."
gunzip -c "$IMG_PATH" | dd of="$DST_DISK" bs=4m status=progress

echo "Syncing..."
sync

echo "Ejecting..."
diskutil eject "$DST_DISK" || true

echo
echo "=== Done ==="
echo "SD card is ready. Insert into OPi and power on."
echo "Connect to 'RobanHeli-SETUP' WiFi to provision."
