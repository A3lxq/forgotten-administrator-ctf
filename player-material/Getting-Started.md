# Getting Started

## What you're given

1. **A folder of handover material** (`challenge-data/` — your instructor
   will tell you how it's shared with you): John's old profile page and
   project page, a few photos from the handover, and a copy of the
   `ledger-tools` Git repository. All of this is self-contained — you
   don't need internet access to investigate any of it.
2. **A decrypt tool**, `flagcrypto.py`, in that same folder's `tools/`
   subdirectory. Whenever you find something encrypted, this is what
   decrypts it, once you have the right password:
   ```
   python3 tools/flagcrypto.py decrypt "<password>" <file> -
   ```
3. **Access to the web application**: your instructor will give you its
   address (e.g. `http://<lab-ip>:8080/`). You start already logged in
   as John's web account (`john` / `Summer2019!` — found among his
   things).

## Tools you'll want

- `exiftool` (or equivalent) for Stage 2.
- `git` for Stage 3 — `git log`, `git show`, `git log --diff-filter=D`
  are your friends.
- A web browser or `curl` for Stage 4.
- A listener (e.g. `nc -lvnp <port>`) for when you get a shell back
  from the server — you are not given SSH access to this box at any
  point; the intended path is to make the application give you a shell.
  Ask your instructor which address the server can reach your listener
  on — it is usually **not** `127.0.0.1` from the server's own point of
  view.

## Where to start

Start with the handover material, not the web app. There's a reason
John's old profile is in there.

See `Rules.md` for what's in and out of scope, and `Flag-Submission.md`
for how scoring works.
