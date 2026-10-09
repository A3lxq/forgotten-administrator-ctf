# The Forgotten Administrator

A single-machine, story-driven cybersecurity CTF for **Synnefo Academy**, built for
authorized, isolated classroom use.

This is **one Linux machine**, not a set of separate boxes. Players progress through:

1. OSINT on a fictional developer
2. File metadata analysis
3. Git history investigation + cryptography
4. Web enumeration + IDOR
5. A web-to-shell pivot (admin reverse shell)
6. Linux enumeration + privilege escalation
7. Root-only artifact decryption

See `player-material/` for what participants receive, and `instructor-material/`
for the build, solution, scoring, and reset documentation (keep this directory
off any player-facing host).

## Status

See `PROJECT-STATUS.md` for the current build phase, what exists, what's tested,
and what's still incomplete. **Do not assume any phase is finished just because
files exist for it** — PROJECT-STATUS.md is the source of truth on verified state.

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
