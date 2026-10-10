# Handover Report — The Forgotten Administrator

A concise status report against the project's own Definition of Done
(spec Section 24). Every item below reflects something actually run and
observed in this project, not an assumption. Full evidence for each is
in `PROJECT-STATUS.md` (phase-by-phase) and
`instructor-material/acceptance-test-report.md` (checklist-by-checklist).

## Definition of Done — item by item

| # | Requirement | Status | Where it was verified |
|---|---|---|---|
| 1 | Application starts from a clean build | ✅ DONE | `scripts/build.sh`; re-seeded DB + restarted service, health check passed |
| 2 | Fictional web users work | ✅ DONE | `john`/`admin` login tested live, repeatedly |
| 3 | IDOR works as designed | ✅ DONE | `GET /records/2` as `john` discloses admin's record, live and in pytest |
| 4 | Admin shell path works in the isolated VM | ✅ DONE | Command injection confirmed live (proof-file + a real netcat reverse shell caught over the documented VM network path) |
| 5 | Linux accounts and permissions are correct | ✅ DONE | `john`/`admin`/`ctfbuilder`/disabled `root`; `/home/admin` and `/root` permission boundaries confirmed live |
| 6 | Privilege-escalation stage works as designed | ✅ DONE | Genuine `admin` → `euid=0` performed live, zero instructor `sudo`; reset verified |
| 7 | 5 genuine flags and 10 decoys exist | ✅ DONE | `scripts/validate-flags.sh`: exact counts, confirmed |
| 8 | Encryption distribution is correct | ✅ DONE | 3 genuine + 5 decoy encrypted = 8 total, confirmed |
| 9 | Original Flag 3 unlocks the final artifact | ✅ DONE | Live decrypt chain run end to end |
| 10 | Original Flag 3 is not the Linux root password | ✅ DONE | `root` has no password at all (login disabled); Flag 3's password/value are also distinct from each other, confirmed |
| 11 | Original Flag 5 can be recovered after root access | ✅ DONE | Recovered live via the real privesc path |
| 12 | Genuine flags award the correct points | ✅ DONE | Scoring snippet functionally tested (100/0/unrecognized cases) |
| 13 | Decoys award zero points | ✅ DONE | `validate-flags.sh`: "all decoys award 0 points" |
| 14 | The VM can be reset between teams | ✅ DONE | `scripts/reset.sh {app,privesc,vm}`, all three tested live; `clean-start` qemu snapshot exists and was used for a real damage→restore cycle |
| 15 | Player and instructor files are separated | ✅ DONE | `scripts/package.sh` produces separate `dist/player-package` and `dist/instructor-package`, with an automated check that aborts the build if any decrypted genuine-flag value or the manifest leaks into the player package (tested — it actually catches a planted leak) |
| 16 | Monitor hints match the actual challenge | ✅ DONE | `instructor-material/hint-sheet.md` rewritten stage-by-stage against the real implementation |
| 17 | Build and troubleshooting instructions are complete | ✅ DONE | `build-guide.md` (updated through Phase 5), `troubleshooting.md` (4 real bugs hit + fixes) |
| 18 | All executed tests have truthful results | ✅ DONE | Every PASS in this project cites actual command output; see `acceptance-test-report.md` |
| 19 | The final package has been verified | ✅ DONE | Exported VM booted independently on isolated ports with no backing-file dependency; accounts, app, flags, and privesc weakness all confirmed intact in that independent boot |

**Every item is DONE.** None are marked complete without the evidence above existing in this project's own history.

## What exists, concretely

- Flask app (`app/`), 15 automated tests, all passing.
- A real, booted Ubuntu 24.04 LTS VM (`vm/`), host-only networking,
  with the full intended vulnerability chain wired up and exploited
  for real at least once end-to-end.
- 15 flags (5 genuine/800 pts, 10 decoys/0 pts), standard crypto
  (scrypt + AES-256-GCM), a private manifest, and an author/validator
  script pair.
- A one-shot privilege-escalation weakness (group-writable cron
  script), with its own reset mechanism.
- Full player-material and instructor-material documentation sets.
- A standalone, exported, checksum-verified VM image
  (`vm/dist/forgotten-admin-ctf.qcow2`, ~1.3GB) plus a separate,
  automatically-leak-checked player/instructor package split
  (`dist/player-package`, `dist/instructor-package`).

## Honest limitations (carried forward, not hidden)

- **Multi-host lab networking is untested.** Everything was verified
  on one development machine using loopback port-forwarding. Before a
  real event on separate physical machines, re-verify the bindings in
  `vm/networking.md` and `vm/scripts/boot-vm.sh` against your actual
  lab network, and re-run `scripts/health-check.sh` against that setup.
- **"No accidental shortcut" (Section 21.G3) is a reasoned check of
  the implemented surface, not an exhaustive penetration test.** SSH
  password auth is disabled everywhere, passwords are high-entropy, and
  no other route skips authentication — but this wasn't fuzzed or
  independently red-teamed.
- **This was built and tested on a single development host under
  software CPU emulation** (no `/dev/kvm` access in this environment).
  Functionally everything works the same under KVM, just faster to
  boot; this hasn't been separately re-verified with KVM acceleration
  on.

## How to actually run this

1. `instructor-material/build-guide.md` — build from scratch (one-time
   base-image download + SSH key generation, then `scripts/build.sh`).
2. `scripts/health-check.sh` — confirm it's healthy before an event.
3. `scripts/package.sh` (+ `vm/scripts/export-vm.sh` first, if you want
   a standalone VM image in the instructor package) — produce the two
   separate deliverables.
4. `instructor-material/instructor-guide.md` — run the event.
5. `scripts/reset.sh {app|privesc|vm}` — reset between teams.
