# Changelog

## Unreleased

### Phase 8 — Packaging
- Finished `scripts/build.sh`, `health-check.sh`, `reset.sh` (previously
  Phase-1 placeholders) as real orchestrators over the VM scripts.
- Added `vm/scripts/export-vm.sh`: flattens the clean-start snapshot
  into a standalone, checksummed qcow2. Verified by booting the export
  independently on isolated ports and confirming all state intact.
- Added `scripts/package.sh`: separates player/instructor deliverables,
  with an automated leak check (spot-tested against a planted leak).
- Added `HANDOVER-REPORT.md` against the spec's Definition of Done.
- Final clean regression pass: tests, flag validator, health check.

**Project complete — all 8 phases done.**

### Phase 7 — Integration testing
- Ran the full Section 21 acceptance checklist (A-G) against the live
  VM; wrote `instructor-material/acceptance-test-report.md` with
  observed evidence for every check.
- Verified app-level reset (DB wipe + re-provision).
- Verified VM-level reset for real: damaged state (deleted a flag,
  stopped the service), `qemu-img snapshot` + restore, confirmed exact
  recovery including the privesc weakness and no leftover artifacts.
  Created the `clean-start` snapshot as the VM's actual reset baseline.
- Closed a real gap: tested an actual netcat reverse shell over the
  documented VM networking path (`10.0.2.2`, not `127.0.0.1`) — the
  listener genuinely caught a shell as the Linux `admin` account.
- Functionally tested the scoring-guide.md snippet's genuine/decoy/
  unrecognized-input behavior.

### Phase 6 — Documentation
- Wrote `instructor-guide.md`, `troubleshooting.md`, `security-review.md`
  from the real build (not generic placeholders).
- Updated `build-guide.md` with the Phase 4/5 steps.
- Fixed `player-material/Getting-Started.md`: players never get SSH
  access (corrected from an earlier placeholder assumption); they get a
  shell via the command-injection path and need a listener, not an SSH
  client.
- Live-verified listening services on the VM (`ss -tlnp`): only SSH and
  the app, nothing unexpected.

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
