# Changelog

## Unreleased

### Phase 5 — Privilege escalation
- Added the one intentional privesc weakness: a root cron job
  (`/etc/cron.d/admin-tools-cleanup`) running a script
  (`/opt/admin-tools/cleanup.sh`) that's group-writable by `admin`.
- Added `vm/scripts/reset-privesc.sh` to restore the clean state and
  clear known exploit artifacts between teams.
- Added `instructor-material/privesc-design.md` and
  `instructor-material/reset-guide.md`.
- Updated Stage 5 hints and the solution walkthrough to match.
- Performed a real, live `admin` → root privilege escalation on the VM
  with zero instructor assistance, recovered Original Flag 5, and
  verified the reset script restores the clean state afterward.

### Phase 4 — Flags & story
- Added `challenge-data/tools/flagcrypto.py` (scrypt + AES-256-GCM,
  ships to players) and `scripts/author_flags.py` (single source of
  truth for all 15 flags, generates all stage content + the manifest).
- Built Stage 1 (OSINT profile/project pages), Stage 2 (3 PNGs with
  real EXIF metadata), Stage 3 (a real nested git repo with recoverable
  deleted history) under `challenge-data/`.
- Added `vm/scripts/deploy-flags.sh` to push Stage 4/5 artifacts onto
  the VM with correct ownership/permissions; fixed a sudo/glob-ordering
  bug found while testing it.
- Added `scripts/validate_flags.py` / `scripts/validate-flags.sh` — the
  real local flag-validation utility (counts, encryption distribution,
  uniqueness, format, scoring, actual decrypt + wrong-password-reject
  checks). All checks pass.
- Updated player-material (Story, Getting-Started, Flag-Submission,
  Rules, README) and instructor-material (scoring-guide, hint-sheet,
  solution-walkthrough) to match the real implementation.
- Re-verified the full exploit chain against the live VM after
  deployment, including both genuine and decoy decryptions.

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
