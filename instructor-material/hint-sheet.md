# Hint Sheet

> Private. Give hints progressively — Level 1 first, Level 3 only if a
> team is genuinely stuck. Matches the actual implementation.
>
> These hints are genuine nudges toward the real flag in each stage —
> they never hand it over outright. The decoys in the challenge content
> itself work the opposite way: loud, prominent, easy to stumble on
> fast. If a team submits a decoy, that's a sign they stopped
> investigating the moment something looked flag-shaped — a good
> moment to remind them decoys exist and are meant to be found quickly.

## Stage 1 — OSINT

1. John has an online identity. What does his profile page link to?
2. The same username appears in more than one place — correlate them.
3. Read `project-page.html`'s changelog line by line, not just the
   obvious bits — one entry has the real flag woven into ordinary
   text. (The prominent, boxed-off thing on `profile.html` is a decoy —
   its format is a tell if you look closely at what it starts with.)

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

## Stage 4 — Credential reuse

1. The record you weren't supposed to see gives you a login. Is a web
   login the only place that password might work?
2. This server has SSH. Whose password do you already have?
3. `ssh admin@<vm>` with the password from the IDOR'd record. It's the
   same password on both sides — the admin never got around to making
   them different. That's the whole vulnerability; there's no second
   exploit step.

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
