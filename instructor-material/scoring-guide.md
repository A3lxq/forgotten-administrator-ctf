# Scoring Guide

> Private — instructor use only.

## Points

| Flag | Stage | Points | Encrypted |
|---|---|---|---|
| Original Flag 1 | 1 — OSINT | 100 | no |
| Original Flag 2 | 2 — Metadata | 100 | no |
| Original Flag 3 | 3 — Git/crypto | 150 | yes |
| Original Flag 4 | 4 — Web/IDOR/admin | 200 | yes |
| Original Flag 5 | 5 — Privesc/root | 250 | yes |
| **Total** | | **800** | |

Decoys (5, `FFLAG{...}`, one per stage) always score 0, regardless of
which one a team submits. They're deliberately the loud, fast find in
each stage — a team that submits one quickly isn't being penalized for
exploring, just reminded to keep digging.

## Validating submissions

Run the local validator any time:
```
./scripts/validate-flags.sh
```
It checks: exact counts (5 genuine / 5 decoy), encryption distribution
(3 genuine + 3 decoy encrypted = 6 total), uniqueness, format, that
every encrypted flag actually decrypts with its recorded password and
rejects a wrong one, and that the max score is 800. See
`flag-manifest.json` for the authoritative values (private — never copy
it anywhere player-accessible).

## Marking a team's submission

There is no public scoring API (per project scope — Section 5). To
score a submitted string, check it against `flag-manifest.json`'s
`flags[].value` field by hand or with a small script:
```
python3 -c "
import json
m = json.load(open('instructor-material/flag-manifest.json'))
submitted = input('Flag: ').strip()
match = next((f for f in m['flags'] if f['value'] == submitted), None)
if not match:
    print('Not a recognized flag.')
elif match['classification'] == 'decoy':
    print('Valid decoy — 0 points.')
else:
    print(f\"Valid genuine flag — {match['points']} points.\")
"
```
Track which flags each team has already submitted yourself (e.g. a
spreadsheet) to prevent double-scoring — the validator does not persist
state between runs by design (Section 18: "prevent duplicate scoring" is
an instructor-process requirement, not a server requirement, since no
public scoring server is in scope here).
