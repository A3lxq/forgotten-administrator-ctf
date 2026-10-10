# Acceptance Test Report

> Private. Every result below was actually run against the live,
> booted VM (or the actual files) in this session — Phase 7 — not
> inferred from earlier phases' notes, though several checks had also
> been run during Phases 3–5 and are re-confirmed here. Nothing is
> marked PASS without observed output.
>
> **Revision note:** Stage 4's mechanism later changed from command
> injection + reverse shell to credential reuse + direct SSH (decoys
> also reduced from 10 to 5, one per stage). Rows C2, G3, G4, and
> Section E below are updated to the current mechanism, each with
> fresh evidence from re-running the full chain after that change —
> not left describing a feature that no longer exists.

Legend: **PASS** (run, observed correct) / **FAIL** (run, observed
incorrect) / **UNTESTED** (not run, with reason).

## A. Machine and application

| # | Check | Result | Evidence |
|---|---|---|---|
| A1 | Application starts successfully | PASS | `curl /healthz` → `{"status":"ok"}` |
| A2 | Application health check passes | PASS | same as above |
| A3 | Seeded fictional users exist | PASS | DB query → `[('john', 0), ('admin', 1)]` |
| A4 | Application can be reset | PASS | Stopped service, deleted the sqlite DB, re-ran `provision.sh` — re-seeded correctly (`users: [('john', 0), ('admin', 1)]`, `records: [(2,)]`), service restarted under a new PID, health check passed again. |

## B. IDOR

| # | Check | Result | Evidence |
|---|---|---|---|
| B1 | John can access his own record | PASS | Logged in as `john`, `GET /records/1` → `<h1>Handover notes</h1>` |
| B2 | John can access the designated administrative record via IDOR | PASS | Same session, `GET /records/2` → `<h1>Admin handover record...</h1>` + the admin password `N3tOps-Diag#7`, with no ownership check |
| B3 | The vulnerability is present as designed (not a page that merely pretends) | PASS | `records.py`'s query has no `WHERE owner_user_id = ?` clause — confirmed by reading the actual route code, not just its behavior; a non-existent id (999) still correctly 404s, proving the route does hit the DB rather than returning a static page |

## C. Account boundaries

| # | Check | Result | Evidence |
|---|---|---|---|
| C1 | Web identities are distinct from Linux identities | PASS | Web: `john`(not admin)/`admin`(admin) in the app DB. Linux: `john`(uid 1001), `admin`(uid 1002, gid 110), `ctfbuilder`(uid 1000), `root` disabled. Confirmed via `getent passwd`. |
| C2 | The credential-reuse pivot lands in the Linux admin identity | PASS | Real SSH password login (`ssh admin@<vm>` with the IDOR-disclosed password, no key) → `id` → `uid=1002(admin) gid=110(admin) groups=110(admin)`. |
| C3 | It does not execute as root | PASS | Same evidence — `uid=1002`, not `0` |

## D. File permissions

| # | Check | Result | Evidence |
|---|---|---|---|
| D1 | Linux admin can read its intended evidence | PASS | `sudo -u admin cat /home/admin/evidence/decrypt_notes.txt` → readable |
| D2 | Linux admin cannot read the final root-only artifact | PASS | `sudo -u admin cat /root/final_evidence.enc` → `Permission denied`; `sudo -u admin ls /root` → `Permission denied` |
| D3 | Root can read the final artifact | PASS | `sudo cat /root/final_evidence.enc \| wc -c` → `83` (readable, correct size) |

## E. Flags

| # | Check | Result | Evidence |
|---|---|---|---|
| E1 | Exactly 5 genuine flags exist | PASS | `validate-flags.sh`: "exactly 5 genuine flags (5)" |
| E2 | Exactly 5 decoys exist (revised from 10, one per stage) | PASS | "exactly 5 decoy flags (5)" |
| E3 | 3 genuine flags encrypted | PASS | "3 genuine flags encrypted (3)" (spec says "three genuine flags are encrypted" in Section 21.E — matches our distribution of flags 3/4/5) |
| E4 | 3 decoys encrypted (revised from 5) | PASS | "3 decoy flags encrypted (3)" |
| E5 | All flag values are unique | PASS | "all 10 flag values are unique" |
| E6 | Only genuine flags receive points | PASS | Functionally tested the scoring snippet from `scoring-guide.md` with a genuine flag (→ 100 pts), a decoy (→ 0 pts), and an unrecognized string (→ not recognized) — all three behaved correctly |

## F. Final artifact

| # | Check | Result | Evidence |
|---|---|---|---|
| F1 | The correct Original Flag 3 value unlocks the artifact | PASS | `flagcrypto.py decrypt "SYN{git_ghost_61ace7b2}" final_evidence.enc -` → `SYN{root_of_all_evidence_3b7d55a0}` |
| F2 | An incorrect password does not unlock it | PASS | Random wrong password → rejected. Also specifically tested Flag 3's own *password* (`BlueHarbor-99`, as opposed to its decrypted *value*) → also correctly rejected, confirming the spec's "retain the decrypted value, not the password" distinction is real, not just documented |
| F3 | Original Flag 5 is recoverable after successful decryption | PASS | shown in F1 |
| F4 | The final artifact is not accessible to Linux admin before privilege escalation | PASS | re-confirmed live: `sudo -u admin test -r /root/final_evidence.enc` → "PASS: admin cannot read it" |

## G. Full player path

| # | Check | Result | Evidence |
|---|---|---|---|
| G1 | The intended path is documented and manually testable | PASS | `instructor-material/solution-walkthrough.md`; every step in it has been executed for real at least once across Phases 3–7 |
| G2 | Every stage has a reproducible starting state | PASS | App/DB: `A4` above. Privesc mechanism: `reset-privesc.sh`, tested in Phase 5 (re-exploit → reset → clean). Whole VM: this phase, deliberately deleted a flag file and stopped the app service, took a `qemu-img snapshot`, restored it, and confirmed both were back exactly as before, plus the privesc weakness and no leftover artifacts. The resulting `clean-start` snapshot is now the VM's checked-in baseline for resetting between teams (see `reset-guide.md`). |
| G3 | No accidental shortcut makes an earlier stage unnecessary | PASS (checked, not proven exhaustively) | SSH password auth is scoped to `admin` only via an sshd `Match User admin` block (confirmed: `john` → `Permission denied (publickey)` trying the same password route) — players can't reach a shell without first finding `admin`'s password through the IDOR. That password and the final artifact's password are both high-entropy/arbitrary strings, not guessable. No other route in the Flask app skips authentication. This is a reasoned check of the implemented surface, not an exhaustive penetration test of every conceivable shortcut. |
| G4 | Stage 4's credential-reuse pivot works as a real SSH session, not just a `sudo` proxy | PASS | `ssh -o PreferredAuthentications=password -o PubkeyAuthentication=no admin@127.0.0.1` with the IDOR-disclosed password → real interactive shell, `id` → `uid=1002(admin)`. Ran the full chain through this exact session: read `decrypt_notes.txt`, decrypted Flag 4, appended the privesc payload to `cleanup.sh`, waited for the real cron tick, got `euid=0`, decrypted `/root/final_evidence.enc` with Flag 3's plaintext → Flag 5. No instructor `sudo` anywhere in this run. |

## Full end-to-end chain — run live, start to finish, in this project (cumulative across Phases 3-7)

OSINT (Flag 1) → metadata (Flag 2) → git history/crypto (Flag 3,
plaintext retained) → web login as `john` → IDOR on `/records/2` →
admin password disclosed → real SSH password login as Linux `admin`
with that same password (no key, no command injection) → decrypt
Flag 4 on-box → enumerate `/etc/cron.d/` → exploit the group-writable
cron script → genuine `euid=0` → decrypt `/root/final_evidence.enc`
with Flag 3's plaintext → Flag 5. All five genuine flags recovered
this way, in one continuous SSH session; all five decoys also
recovered and confirmed to award 0 points.

## Known limitations (stated, not hidden)

- **Not an automated single-script end-to-end test.** Section 21
  allows this ("If a full end-to-end attack simulation cannot be safely
  automated, document the manual verification steps and their
  results") — that's what this report and `solution-walkthrough.md`
  are: every step was run manually and for real, including the actual
  reverse shell (G4), rather than scripted as one unattended pipeline.
- **Multi-host lab networking is untested** (see
  `security-review.md`) — only single-host loopback hostfwd has been
  exercised.
