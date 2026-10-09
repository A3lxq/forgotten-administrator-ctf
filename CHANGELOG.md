# Changelog

## Unreleased

### Phase 3 — Linux identity & VM build
- Downloaded and checksum-verified the Ubuntu 24.04 LTS cloud image.
- Added `vm/cloud-init/` (user-data.yaml, meta-data.yaml), `vm/scripts/`
  (create-disk.sh, boot-vm.sh, stop-vm.sh, provision.sh,
  remote-provision.sh), `vm/networking.md`, `vm/README.md`.
- Built and booted the VM under QEMU (host-only user-mode networking).
- Fixed a cloud-init bug (username/group collision for "admin") found
  during the build, by rebuilding from a corrected `user-data.yaml`
  rather than patching the running instance.
- Deployed the Phase 2 app into the VM as a systemd service running
  under the Linux `admin` account.
- Ran the full IDOR → credential disclosure → command injection chain
  against the live VM over HTTP, and independently verified over SSH
  that the injected commands executed as the Linux `admin` user.

### Phase 2 — Application
- Implemented Flask app (`app/forgotten_admin/`): seeded `john`/`admin` web
  identities, login/logout, `/records/<id>` with intentional IDOR,
  `/admin/diagnostics` with intentional OS command injection gated by
  admin role.
- Added 14 new automated tests (15 total) covering auth, IDOR, the admin
  role gate, command injection, health check, and seed idempotency — all
  passing (`./scripts/run-tests.sh`).
- Chose Ubuntu Server 24.04 LTS as the Phase 3 VM guest OS.

### Phase 1 — Skeleton
- Initialized git repository.
- Created project directory structure (`scripts/`, `app/`, `challenge-data/`,
  `player-material/`, `instructor-material/`, `vm/`, `logs/`).
- Added `README.md`, `PROJECT-STATUS.md`, `.gitignore`.
- Added placeholder player and instructor documentation.

### Phase 0 — Environment & plan
- Inspected host environment (OS, resources, tooling availability).
- Chose architecture: Flask + SQLite app, QEMU/KVM VM with cloud-init
  provisioning, host-only networking.
