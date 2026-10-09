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
- [ ] Phase 5 — Privilege escalation
- [ ] Phase 6 — Documentation (player + instructor)
- [ ] Phase 7 — Integration testing
- [ ] Phase 8 — Packaging

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
