# Instructor Guide

> Private — never place under app/static, app/templates, challenge-data
> served paths, or player-material.

## What this is

A single Ubuntu Server 24.04 LTS VM (QEMU/KVM, host-only networking)
running one deliberately vulnerable Flask application, with a 5-stage
story-driven path from OSINT to a root-protected encrypted artifact.
5 genuine flags (800 points total), 5 decoys (0 points, one per stage).
Built and verified incrementally — see `PROJECT-STATUS.md` in the
project root for exactly what's been tested and how.

**Design note on decoys:** decoys are deliberately the *loud, fast,
satisfying* find in each stage — prominent placement, enticing framing
("found a flag!", password notes that scream for attention). Genuine
flags are deliberately *quiet* — blended into ordinary prose, requiring
you to actually read rather than skim. A player who grabs the first
flag-shaped thing they see and stops looking will submit a decoy. This
is intentional: it rewards careful verification over speed, and gives
instructors an easy tell for "rushed through it" vs. "actually
investigated."

## Document map

| Document | Use it for |
|---|---|
| `build-guide.md` | Building/deploying the VM and app from scratch |
| `solution-walkthrough.md` | The exact, verified path through every stage |
| `scoring-guide.md` | Point values, flag validation, scoring a submission |
| `privesc-design.md` | The Stage 5 weakness: what, why, how to test/reset |
| `reset-guide.md` | Resetting app state / the privesc mechanism / the VM |
| `security-review.md` | Isolation and safety checks for this lab |
| `troubleshooting.md` | Real issues hit while building this, and their fixes |
| `flag-manifest.json` | Authoritative flag values/passwords (machine-readable) |

## The intended path (summary — see solution-walkthrough.md for exact commands)

1. **OSINT** (`challenge-data/stage1-osint/`) — John's profile and
   project page → Flag 1 (plaintext, 100 pts).
2. **Metadata** (`challenge-data/stage2-metadata/`) — EXIF on handover
   photos → Flag 2 (plaintext, 100 pts).
3. **Git history + crypto** (`challenge-data/stage3-git-history/`) — a
   real repo with a deleted-but-recoverable encrypted backup → Flag 3
   (encrypted, 150 pts). **Its decrypted value is retained** — it's the
   final artifact's password later.
4. **Web app / IDOR** — log in as the seeded `john` web account,
   `GET /records/2` (no ownership check) discloses the `admin` web
   account's password.
5. **Credential reuse / SSH** — that same password is also the real
   Linux `admin` account's SSH password (set in
   `vm/scripts/remote-provision.sh`, SSH password auth scoped to that
   one account via an sshd `Match User admin` block). `ssh admin@<vm>`
   with it → Flag 4 (encrypted, 200 pts, in `/home/admin/flags/`). No
   command injection or reverse shell involved — this is the entire
   second "vulnerability": the admin reused one password everywhere.
6. **Linux privilege escalation** — a root cron job executes a script
   that's group-writable by `admin` → genuine root shell.
7. **Final artifact** — `/root/final_evidence.enc`, unlocked with Flag
   3's decrypted plaintext (not its password, not any Linux password)
   → Flag 5 (encrypted, 250 pts).

Total: 800 points across 5 genuine flags. 5 decoys exist alongside
every stage (one each) and are safe, fair distractions — see
`flag-manifest.json`. They're the easy, obvious, fast find in each
stage; genuine flags require actually reading.

## Running an event

1. Build/boot the VM and deploy everything (`build-guide.md`), or
   restore a clean snapshot (`reset-guide.md`).
2. Give players `player-material/` plus the VM's connection details
   (host/port for the web app). Players never need SSH credentials
   handed to them directly — the intended path is to find the admin
   password through the IDOR and SSH in with it themselves.
3. Watch for out-of-scope activity per `player-material/Rules.md`.
4. Score submissions per `scoring-guide.md`.
5. Reset per `reset-guide.md` before the next team.

## Known limitation

There is no automated full end-to-end "run the whole attack chain from
a cold boot" test (Section 21.G) — each stage's reproducibility was
verified individually and the full chain was run manually, start to
finish, in this session (see `PROJECT-STATUS.md` Phases 3-5). See
`acceptance-test-report.md` for the complete, honest pass/fail/untested
breakdown.
