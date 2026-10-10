#!/usr/bin/env bash
# export-vm.sh — packages the VM's "clean-start" snapshot into a single,
# standalone qcow2 image (no backing-file dependency on the base cloud
# image, so it can be copied to another machine on its own) plus the
# cloud-init seed and a minimal boot script. Requires the VM to be
# stopped (needs the disk's write lock) and a "clean-start" snapshot to
# already exist (see build.sh's last step, or reset.sh's error message
# if it's missing).
set -euo pipefail
cd "$(dirname "$0")/.."

DISK="disks/forgotten-admin.qcow2"
OUT_DIR="dist"
OUT_IMAGE="$OUT_DIR/forgotten-admin-ctf.qcow2"

if [ ! -f "$DISK" ]; then
  echo "Missing $DISK. Build the VM first (see instructor-material/build-guide.md)." >&2
  exit 1
fi

echo "== Stopping the VM (export needs the disk's write lock) =="
./scripts/stop-vm.sh

if ! qemu-img snapshot -l "$DISK" 2>/dev/null | grep -q clean-start; then
  echo "No 'clean-start' snapshot exists on $DISK. Create one first:" >&2
  echo "  qemu-img snapshot -c clean-start $DISK" >&2
  exit 1
fi

mkdir -p "$OUT_DIR"

echo "== Flattening the clean-start snapshot into a standalone image =="
echo "   (this merges the base cloud image + overlay + snapshot into one"
echo "    self-contained file -- can take a few minutes)"
rm -f "$OUT_IMAGE"
qemu-img convert -l clean-start -O qcow2 -c "$DISK" "$OUT_IMAGE"

echo "== Copying the cloud-init seed (public key + account config only -- no secrets beyond the one-way password hashes already in this repo's vm/cloud-init/user-data.yaml) =="
cp seed/seed.img "$OUT_DIR/seed.img"

echo "== Checksumming =="
(cd "$OUT_DIR" && sha256sum forgotten-admin-ctf.qcow2 seed.img > SHA256SUMS)

echo "== Writing import instructions =="
cat > "$OUT_DIR/IMPORT.md" <<'EOF'
# Importing this VM package

Contents:
- `forgotten-admin-ctf.qcow2` — the standalone VM disk (clean-start state:
  app deployed, flags placed, privesc weakness in place, nothing yet
  exploited).
- `seed.img` — cloud-init seed. Not needed for normal boots (cloud-init
  only re-runs its per-instance modules once, and that already happened
  when this image was built), but harmless to attach and kept here for
  completeness / in case you need to re-derive account config.
- `SHA256SUMS` — checksums for both files.

## Verify integrity
```
sha256sum -c SHA256SUMS
```

## Boot it
Requires `qemu-system-x86_64` (see the project's `DEPENDENCIES.md`).
```
qemu-system-x86_64 \
  -machine type=q35,accel=kvm   `# use accel=tcg if /dev/kvm isn't available` \
  -cpu max -m 2048 -smp 2 \
  -drive file=forgotten-admin-ctf.qcow2,if=virtio,format=qcow2 \
  -netdev user,id=net0,hostfwd=tcp:127.0.0.1:2222-:22,hostfwd=tcp:127.0.0.1:8080-:8000 \
  -device virtio-net-pci,netdev=net0 \
  -display none -daemonize
```
This reproduces the same host-only networking as the project's own
`vm/scripts/boot-vm.sh` (see `vm/networking.md` for what that means and
why `127.0.0.1` inside the guest is not the same as `127.0.0.1` on your
host). Adjust the forwarded host addresses/ports for your actual lab
network before a live event -- do not bind to `0.0.0.0` on a host that
also has a public interface.

## Access

- SSH as `ctfbuilder` requires the private key that matches the public
  key baked into this image at build time
  (`vm/keys/ctfbuilder_ed25519` in the source project) -- that key is
  NOT included in this package; it is handed to instructors separately,
  never to players.
- The web app is at `http://127.0.0.1:8080/` (or your lab network's
  equivalent) once booted.
- Players are never given SSH credentials for `john` or `admin` on the
  intended path.
EOF

echo
echo "== Restarting the source VM (unaffected by the export) =="
./scripts/boot-vm.sh

echo
echo "Done. Package contents:"
ls -lh "$OUT_DIR"
