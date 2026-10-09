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
- [ ] Phase 3 — Linux identity & admin vulnerability (VM build)
- [ ] Phase 4 — Flags & story (15 flags, encryption, manifest)
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
