# Hint Sheet

> Private. Give hints progressively — Level 1 first, Level 3 only if a
> team is genuinely stuck. Matches the actual implementation (Phase 4).

## Stage 1 — OSINT

1. John has an online identity. What does his profile page link to?
2. The same username appears in more than one place — correlate them.
3. Check `project-page.html`'s footer, not just its changelog. Page
   source, not just the rendered view — `profile.html` has more than
   one "old" thing sitting on it too (one's a decoy, one's a password
   for something nearby).

## Stage 2 — Metadata

1. These photos aren't interesting for what's *in* them.
2. `exiftool <file>` shows more fields than just the date taken — look
   at `Comment` and `Artist`.
3. `handover_photo.png`'s `Comment` field has the real flag.
   `scan_backup.png` has an encrypted decoy in `Comment` and its
   password sitting in its own `Artist` field.

## Stage 3 — Git history

1. The current files in the repo are not the whole story.
2. `git log --oneline` shows more commits than the current file list
   would suggest. What got removed?
3. `git show <commit>:<path>` recovers a deleted file without checking
   it out. The passphrase is in a commit that's still in history
   (`notes.txt`, added alongside the real backup) — don't confuse it
   with the *other* old passphrase mentioned in a later commit (that
   one's for the decoy).

## Stage 4 — IDOR

1. Once logged in as John, look at how his own record is addressed —
   is there a number in that URL?
2. Compare what happens when you change just that number.
3. `GET /records/<id>` never checks that the record belongs to you —
   only that you're logged in at all. Try id `2`.

## Stage 4 — Admin function / reverse shell

1. The record you weren't supposed to see tells you how to log in as
   something else, and what tool that account has access to.
2. That tool runs a real system command with your input in it. What
   happens if your input isn't just a hostname?
3. `/admin/diagnostics`'s `host` field is concatenated into a shell
   command. A `;` after a valid-looking host lets you run anything —
   and it runs as the Linux `admin` account, not root.

## Stage 5 — Linux privilege escalation

1. Check who you are, what groups you're in, and what runs
   automatically on this box (not just what you can run yourself).
2. Look at `/etc/cron.d/` — something there runs as root. What file
   does it execute, and who can write to *that* file?
3. `/opt/admin-tools/cleanup.sh` is group-writable by `admin` — you're
   in that group. Anything you add to it runs as root within a minute.

## Final artifact

1. The final evidence is under `/root` — you'll need to actually be
   root, not just read-access tricks.
2. It's also encrypted, separately from the filesystem permission.
3. The password is the plaintext you got from decrypting Original
   Flag 3 back in Stage 3 — not anything you've seen since.
