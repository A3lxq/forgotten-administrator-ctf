# Changelog

## Unreleased

### Addendum — timed solve, LLM skill files + blind-test, leaked-history bug found and fixed, Bridged multi-player hosting added
- Solved the box myself end-to-end (all 5 genuine + 5 decoy flags),
  timed, with full tool list.
- Wrote `llm-skills/` — 7 methodology-only skill files (OSINT,
  metadata forensics, git history forensics, web IDOR testing,
  credential reuse, Linux privesc enumeration, crypto tooling), no
  flag values or passwords. Validated with a real blind-test subagent
  that solved all 5 stages using only these files plus the documented
  starting foothold; rated every skill file "spot on" for its stage.
  One test-design flaw found and fixed along the way: the first
  blind-test run was incorrectly denied the legitimate
  `Getting-Started.md` starting credential, not a flaw in the box or
  the skills.
- **Found and fixed a real solution leak**: `admin`'s SSH shell
  history had been accumulating the exact Stage 4→5 exploit chain
  (both passwords, the final decrypt command) from every prior
  live-verification pass, readable by that same account. **Confirmed
  this was already baked into the published `ova-export-v4` release**
  by booting it independently. Fixed with `unset HISTFILE` in
  `admin`'s `.bashrc`, re-verified across a real login+logout, clean
  snapshot re-taken, full `health-check.sh` re-pass.
- Owner decided v4 should come down rather than just being flagged;
  deleted it and published `ova-export-v5` with the fix.
- **Added supported Bridged-adapter hosting** for running this as a
  shared multi-player/workshop box over a trusted LAN (explicit,
  risk-accepted operator choice), alongside the existing NAT/
  port-forward single-host setup. No guest-side change was needed —
  the app and sshd already bind to all interfaces, and the DHCP fix
  below is already interface-name-based. Documented in `SETUP.md`
  (new "Hosting for multiple players" section) and
  `instructor-material/security-review.md`.
- `git push` and `gh release create`, previously denied by the
  harness's auto-mode classifier, both succeeded this session after
  the owner adjusted permissions on their end.

### Addendum — netplan `match: {}` regression found and reverted; credentials doc added
- Tried broadening the netplan fix to `match: {}` (any ethernet
  device); it hung the VM's networking when applied (confirmed twice,
  not a shell-quoting issue). Reverted to the already-verified
  `match: {name: "en*"}` fix, which is what `ova-export-v4` already
  has — no rebuild needed.
- Recovered the hung VM via the `clean-start` snapshot (no console
  input path exists on this headless VM).
- Added `instructor-material/credentials.md`: direct-access reference
  (ctfbuilder SSH + sudo -i, story-account passwords, reset commands),
  every command verified against the live VM.
- New troubleshooting.md entry for the hang.

### Addendum — fixed two real cross-hypervisor bugs (VirtualBox)
- Root cause of "no network under VirtualBox NAT or Bridged":
  cloud-init's netplan was MAC-pinned to QEMU's virtio NIC MAC.
  Added `vm/cloud-init/network-config.yaml` (match by interface name,
  not MAC), wired into `create-disk.sh`; patched and re-verified the
  live dev VM.
- Switched `export-ova.sh`'s OVF disk controller from a VMware-style
  `VirtualSCSI` (never validated against real VirtualBox) to plain
  IDE (`PIIX4`), universally supported.
- Investigated a reported recovery-mode password-persistence issue;
  ruled out as a disk-image bug via a direct reboot test (byte-
  identical shadow hash before/after). Likely a recovery-mode
  read-only-root gotcha instead — documented as a hypothesis.
- Re-verified everything on a fresh snapshot and on the actual
  re-exported OVA, booted independently.
- New `troubleshooting.md` entries for all of the above.
- OVA upload (`ova-export-v4`) pending owner approval — blocked by the
  harness's auto-mode classifier for creating a new public GitHub
  release; the built file is ready in `vm/dist/`.

### Addendum — hint-sheet.md removed
- Deleted `instructor-material/hint-sheet.md` (owner request); removed
  its reference from `instructor-guide.md`'s document map.

### Addendum — credential reuse instead of reverse shell; 5 decoys
- Removed the `/admin/diagnostics` command-injection vulnerability
  entirely. Stage 4's second "vulnerability" is now credential reuse:
  the IDOR-disclosed admin web password is also the Linux `admin`
  account's real SSH password, with password auth scoped to that one
  account via an sshd `Match User admin` block.
- Verified live with `pexpect`-driven password SSH login (admin works,
  john is rejected), and ran the entire Flag4→privesc→Flag5 chain in
  one real SSH session with zero instructor `sudo`.
- Found and fixed a real bug: `rsync -a` propagated the local staging
  directory's own permissions onto `/root` itself, loosening it from
  700 to 775. Fixed with `--no-perms` plus an unconditional `chmod`
  safeguard; re-verified.
- Reduced decoys from 10 to 5 (one per stage, mixed plaintext/
  encrypted). `validate_flags.py`/`author_flags.py` updated; all
  checks re-pass (10 total flags now, not 15).
- Rebalanced decoy/genuine content: decoys are now loud and enticing
  (boxed callouts, "found a flag!" framing, prominent positioning),
  genuine flags are quiet (blended into ordinary prose, require
  reading).
- Updated player-material, instructor-material, vm/networking.md,
  vm/README.md, and root README.md to match.

### Addendum — self-contained player materials
- New `materials.py` blueprint serves Stage 1-3 content directly from
  the app, unauthenticated, at `/materials/` — no separate handout
  folder needed to play. `/` is now a public landing page.
- `author_flags.py` now also builds `stage3-git-history.tar.gz` for
  download (players can't live-clone the raw repo over HTTP).
- Fixed a real bug: `remote-provision.sh`'s `systemctl enable --now`
  silently never restarted an already-running service on
  code/config changes. Now does `enable` + unconditional `restart`.
- 9 new tests (`test_materials.py`), including path-traversal
  rejection. `health-check.sh` extended with 2 related checks.
- Built a real standards-based OVA (`vm/scripts/export-ova.sh`,
  qemu-img + hand-written OVF, no VirtualBox/VMware needed to build
  it) and pushed the project to a private GitHub repo with the OVA
  attached as a release asset for cross-machine import testing.

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
