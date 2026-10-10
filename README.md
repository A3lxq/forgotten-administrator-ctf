# The Forgotten Administrator

A single-machine, story-driven cybersecurity CTF for **Synnefo Academy**, built for
authorized, isolated classroom use.

This is **one Linux machine**, not a set of separate boxes. Players progress through:

1. OSINT on a fictional developer
2. File metadata analysis
3. Git history investigation + cryptography
4. Web enumeration + IDOR
5. A web-to-shell pivot (credential reuse — the disclosed password is also the Linux admin's real SSH password)
6. Linux enumeration + privilege escalation
7. Root-only artifact decryption

See `player-material/` for what participants receive, and `instructor-material/`
for the build, solution, scoring, and reset documentation (keep this directory
off any player-facing host).

## Setting this up

**Start with [`SETUP.md`](SETUP.md)** — a complete, start-to-finish guide:
building from source, or importing a pre-built OVA into VirtualBox/VMware
directly. Everything else below is reference material once that's running.

## Status

See `PROJECT-STATUS.md` for the current build phase, what exists, what's tested,
and what's still incomplete, and `HANDOVER-REPORT.md` for the final project-wide
status against the spec's own Definition of Done. **Do not assume any phase is
finished just because files exist for it** — those two files are the source of
truth on verified state.

## Repository layout

```
forgotten-administrator-ctf/
    scripts/              setup, build, reset, test, validation scripts
    app/                  Flask web application + its own tests
    challenge-data/       fictional evidence, metadata files, staged repo content
    player-material/      participant-facing docs (no flags, no solutions)
    instructor-material/  private: manifest, solutions, hints, guides
    vm/                   VM build config, networking docs, packaging
    logs/                 build/test logs (secrets must never be written here)
```

## Safety

This machine is intentionally vulnerable. It is designed to run **isolated**
(host-only VM networking) and must never be exposed to a public or shared
network. See `vm/networking.md` once Phase 3 is complete.
