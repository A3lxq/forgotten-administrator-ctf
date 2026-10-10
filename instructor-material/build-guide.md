# Build Guide

> Private — instructor use only.

## VM guest OS choice

**Ubuntu Server 24.04 LTS** (official cloud image,
`ubuntu-24.04-server-cloudimg-amd64.img`), booted under QEMU/KVM with
cloud-init (NoCloud datasource). Rationale: LTS stability through 2029,
minimal/server image (no GUI), well-documented `sudo`/systemd/cron
behavior for a teaching privilege-escalation lab, same distro family as
most instructors' own experience.

## One-time: download and verify the base image

```
cd vm/images
curl -L -o ubuntu-24.04-server-cloudimg-amd64.img \
  https://cloud-images.ubuntu.com/releases/noble/release/ubuntu-24.04-server-cloudimg-amd64.img
curl -s -o SHA256SUMS https://cloud-images.ubuntu.com/releases/noble/release/SHA256SUMS
sha256sum -c <(grep cloudimg-amd64.img SHA256SUMS)
```
This needs temporary internet access (Section 20) — a one-time download,
not part of the running lab. `vm/images/` is gitignored (597MB, and it's
a public Canonical artifact, not project-specific).

## Build the instructor SSH key (once)

```
ssh-keygen -t ed25519 -N "" -C "ctf-instructor-build-key" -f vm/keys/ctfbuilder_ed25519
```
Paste the resulting `.pub` into `vm/cloud-init/user-data.yaml`'s
`ctfbuilder` user `ssh_authorized_keys`. `vm/keys/` is gitignored — never
commit the private key.

## Create the disk and boot

```
cd vm
./scripts/create-disk.sh      # builds disks/forgotten-admin.qcow2 (copy-on-write
                               # overlay of the base image) + seed/seed.img
./scripts/boot-vm.sh          # boots in the background, host-only networking
```
First boot runs cloud-init (account creation, base packages). **Under
software emulation (no `/dev/kvm` access) this took roughly 8-10 minutes**
in testing — mostly `apt-get update` and the `command-not-found` database
rebuild, not disk I/O. With real KVM acceleration (add your user to the
`kvm` group) it is much faster. Poll readiness with:
```
ssh -i keys/ctfbuilder_ed25519 -p 2222 -o StrictHostKeyChecking=no \
    -o UserKnownHostsFile=/dev/null ctfbuilder@127.0.0.1 'cloud-init status --wait'
```

## Deploy the application

```
./scripts/provision.sh
```
Idempotent — copies `app/` into the VM, builds/updates its venv, writes
and (re)starts the `forgotten-admin.service` systemd unit (runs as the
Linux **admin** account), lays out `/home/admin` per Section 11, and
installs the Phase 5 privilege-escalation weakness
(`/opt/admin-tools/cleanup.sh` + its root cron job). Safe to re-run
after any app change.

## Build and deploy the flags

```
cd ..                                   # back to project root
app/.venv/bin/python3 scripts/author_flags.py
./scripts/validate-flags.sh             # should print "RESULT: all checks passed"
cd vm
./scripts/deploy-flags.sh               # pushes Stage 4/5 artifacts onto the VM
```
`author_flags.py` is the single source of truth for all 10 flags; it
regenerates `challenge-data/` and `instructor-material/flag-manifest.json`.
Re-run it (then `deploy-flags.sh`) any time a flag value changes.

## Verify

```
curl -s http://127.0.0.1:8080/healthz
ssh -i keys/ctfbuilder_ed25519 -p 2222 -o StrictHostKeyChecking=no \
    -o UserKnownHostsFile=/dev/null ctfbuilder@127.0.0.1 \
    'systemctl is-active forgotten-admin && ps -o user= -C python3'
```
Expect `{"status":"ok"}` and the app process owned by `admin`, not root.
For the full exploit chain and permission-boundary checks, see
`solution-walkthrough.md` and `security-review.md`.

## Stop / snapshot / reset

See `reset-guide.md`. In short: `./scripts/stop-vm.sh` /
`./scripts/boot-vm.sh` to start/stop,
`./scripts/reset-privesc.sh` to reset just the Stage 5 weakness, and
`qemu-img snapshot` on `disks/forgotten-admin.qcow2` for a full clean
restore between teams.
