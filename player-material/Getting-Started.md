# Getting Started

## What you're given

Just one thing: the address of the web application (your instructor
will give you this, e.g. `http://<lab-ip>:8080/`). Everything else is
reachable from there — nothing needs to be separately downloaded,
emailed, or handed to you on a drive.

1. **The landing page** (`/`) links to the handover material: John's
   old profile page and project page, a few photos from the handover,
   a downloadable copy of the `ledger-tools` Git repository, and the
   decrypt tool you'll need. All of it is served directly by the box —
   `/materials/`.
2. **The decrypt tool**, `flagcrypto.py` (linked from `/materials/`).
   Whenever you find something encrypted, this is what decrypts it,
   once you have the right password:
   ```
   python3 flagcrypto.py decrypt "<password>" <file> -
   ```
3. **A web login**: you start already logged in as John's web account
   (`john` / `Summer2019!` — found among his things).

(If your instructor handed you a separate folder instead — some events
run that way — the same material is in there; start with that instead
of the web app's `/materials/` page.)

## Tools you'll want

- `exiftool` (or equivalent) for Stage 2.
- `git` for Stage 3 — `git log`, `git show`, `git log --diff-filter=D`
  are your friends.
- A web browser or `curl` for Stage 4.
- An SSH client for Stage 4's follow-through — once you find the right
  credential, you SSH straight into the box with it. No separate
  listener or shell-catching step; ask your instructor for the server's
  address if it isn't the same one the web app is on.

## Where to start

Visit the web app's address and start with the handover material
linked from the landing page — not the login form. There's a reason
John's old profile is in there.

See `Rules.md` for what's in and out of scope, and `Flag-Submission.md`
for how scoring works.
