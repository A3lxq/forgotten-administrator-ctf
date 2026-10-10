# Setup Guide — The Forgotten Administrator

One complete, start-to-finish walkthrough for standing up this CTF from
a fresh clone of this repo. This is the single entry point; it links
out to the detailed docs under `instructor-material/` where there's
more to say, but you shouldn't need to open those just to get running.

If you only want to **import the pre-built OVA** and test it in your
own VirtualBox/VMware, skip to [Option B](#option-b-import-the-pre-built-ova)
— you don't need to build anything.

---

## 0. What you're setting up

One Ubuntu Server 24.04 LTS VM, deliberately vulnerable, running a
Flask app, for a 5-stage story-driven CTF. Full design in
`instructor-material/instructor-guide.md`. This guide only covers
**getting it running**; the guide above covers **running the event**.

---

## Option A: Build everything from source

### A1. Prerequisites (one-time, per build machine)

```
sudo apt-get update
sudo apt-get install -y qemu-system-x86 qemu-utils cloud-image-utils \
    genisoimage libimage-exiftool-perl sqlite3
```
(Debian/Ubuntu package names; adjust for your distro. macOS: use
`brew install qemu`, cloud-init seed creation via `cloud-localds`
equivalent, or build on a Linux machine instead — the scripts assume a
Linux host.)

Also needed: `python3` (3.10+), `python3-venv`, `git`, `openssl`. Check
everything at once:
```
./scripts/preflight.sh
```

### A2. Clone and set up the app

```
git clone <this-repo-url>
cd forgotten-administrator-ctf
python3 -m venv app/.venv
app/.venv/bin/pip install -r app/requirements.txt
./scripts/run-tests.sh          # should print "15 passed"
```

### A3. Download the base VM image (one-time, needs internet)

```
mkdir -p vm/images
cd vm/images
curl -L -o ubuntu-24.04-server-cloudimg-amd64.img \
  https://cloud-images.ubuntu.com/releases/noble/release/ubuntu-24.04-server-cloudimg-amd64.img
curl -s -o SHA256SUMS \
  https://cloud-images.ubuntu.com/releases/noble/release/SHA256SUMS
sha256sum -c <(grep cloudimg-amd64.img SHA256SUMS)
cd ../..
```

### A4. Generate your own instructor SSH key

```
ssh-keygen -t ed25519 -N "" -C "ctf-instructor-build-key" \
    -f vm/keys/ctfbuilder_ed25519
```
Paste the printed `.pub` contents into
`vm/cloud-init/user-data.yaml`, replacing the existing
`ssh_authorized_keys` entry under the `ctfbuilder` user. (This repo's
own key is **not** shipped — generate your own; it only grants SSH
access to the disposable lab VM you're about to build, nothing else.)

### A5. Build everything

```
./scripts/build.sh
```
This single command: creates the VM disk, boots it, waits for
cloud-init (several minutes under software emulation — faster if your
user is in the `kvm` group and `/dev/kvm` is accessible), deploys the
app + privilege-escalation weakness, generates and deploys all 15
flags, and runs a health check. If it finishes cleanly, you have a
fully working lab.

Take a clean snapshot now, before anyone touches it — `build.sh` prints
the exact command, or just run:
```
cd vm && ./scripts/stop-vm.sh && \
  qemu-img snapshot -c clean-start disks/forgotten-admin.qcow2 && \
  ./scripts/boot-vm.sh && cd ..
```

### A6. Verify

```
./scripts/health-check.sh
```
Should print `RESULT: healthy`. If not, see
`instructor-material/troubleshooting.md`.

### A7. (Optional) Export a distributable VM image

```
cd vm
./scripts/export-vm.sh      # standalone qcow2, for QEMU/KVM distribution
./scripts/export-ova.sh     # OVA/OVF, for VirtualBox/VMware import
cd ..
```
See [Testing the OVA](#testing-the-ova-in-virtualbox) below.

### A8. Package player/instructor deliverables

```
./scripts/package.sh
```
Produces `dist/player-package/` (safe to hand out) and
`dist/instructor-package/` (private — never give this to participants;
it includes the manifest, solutions, and your SSH key).

---

## Option B: Import the pre-built OVA

If a `.ova` has already been built and attached to a GitHub Release (or
handed to you some other way), you don't need any of the QEMU tooling
above — just VirtualBox or VMware.

1. Download `forgotten-admin-ctf.ova` and its `.sha256` file.
2. Verify integrity:
   ```
   sha256sum -c forgotten-admin-ctf.ova.sha256
   ```
3. **Test-import first, without committing to it:**
   ```
   VBoxManage import forgotten-admin-ctf.ova --dry-run
   ```
   If that reports no errors, do a real import:
   ```
   VBoxManage import forgotten-admin-ctf.ova
   ```
   Or via the GUI: **File → Import Appliance**.
4. **Before powering it on**, check the network adapter is set to
   **NAT** or **Host-only**, not **Bridged**. This VM is intentionally
   vulnerable — never put it on a shared/production network.
5. Power on. Give it a minute or two to boot.
6. The web app listens on guest port 8000. Add a NAT port-forwarding
   rule (VirtualBox: Settings → Network → Advanced → Port Forwarding)
   mapping some host port to guest `8000`, then browse to
   `http://127.0.0.1:<host-port>/`.
7. **This import does not include SSH access as `ctfbuilder`** — that
   key is kept separately from the distributed image on purpose (see
   `vm/dist/IMPORT.md`, generated alongside the export). If you need to
   inspect the box directly as its builder, you built it yourself in
   Option A and already have the matching key; a `.ova` handed to you
   by someone else won't include it, by design.

### Testing the OVA in VirtualBox

This is exactly what step 3 above does. If you hit an import error,
capture the exact `VBoxManage` output — it's the single most useful
piece of information for debugging the OVF descriptor
(`vm/scripts/export-ova.sh` is what generated it; the descriptor itself
is DMTF OVF 1.0, hand-written, not emitted by VirtualBox/VMware's own
exporter, so this is the first real-world cross-tool import test it
gets).

---

## Resetting between runs

```
./scripts/reset.sh app       # wipe + re-seed just the web app's DB
./scripts/reset.sh privesc   # restore the Stage 5 weakness to clean
./scripts/reset.sh vm        # roll back to the clean-start snapshot
```
Full explanation of each: `instructor-material/reset-guide.md`.

## Running the actual event

`instructor-material/instructor-guide.md` is the next document to read
— it covers the intended player path, hints, scoring, and what to hand
out vs. keep private.

## Something went wrong

`instructor-material/troubleshooting.md` documents every real issue
hit while building this project, with the actual fix for each — check
there before anywhere else.
