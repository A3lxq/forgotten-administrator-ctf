#!/usr/bin/env bash
# create-disk.sh — builds the VM's writable disk and cloud-init seed image
# from the base Ubuntu 24.04 cloud image. Safe to re-run: it refuses to
# overwrite an existing disk unless you pass --force (so you don't lose a
# running lab's state by accident).
set -euo pipefail
cd "$(dirname "$0")/.."

BASE_IMAGE="images/ubuntu-24.04-server-cloudimg-amd64.img"
DISK="disks/forgotten-admin.qcow2"
SEED="seed/seed.img"
DISK_SIZE="12G"
FORCE=0

for arg in "$@"; do
  [ "$arg" = "--force" ] && FORCE=1
done

if [ ! -f "$BASE_IMAGE" ]; then
  echo "Missing $BASE_IMAGE. Download the Ubuntu 24.04 LTS cloud image first" >&2
  echo "(see instructor-material/build-guide.md)." >&2
  exit 1
fi

mkdir -p disks seed

if [ -f "$DISK" ] && [ "$FORCE" -ne 1 ]; then
  echo "Refusing to overwrite existing $DISK (pass --force to rebuild from scratch)." >&2
  exit 1
fi

echo "== Creating writable overlay disk ($DISK_SIZE) from base image =="
qemu-img create -f qcow2 -F qcow2 -b "$(pwd)/$BASE_IMAGE" "$DISK" "$DISK_SIZE"

echo "== Building cloud-init seed image =="
cloud-localds "$SEED" cloud-init/user-data.yaml cloud-init/meta-data.yaml

echo "Done."
echo "Disk:  $DISK"
echo "Seed:  $SEED"
echo "Next:  ./scripts/boot-vm.sh"
